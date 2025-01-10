from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from pydub import AudioSegment
from rich import print
import json
from utils import clean_text, format_time

@dataclass
class SplitInfo:
    part: int
    start_time: float
    end_time: float
    duration: float
    file: str

@dataclass
class ProcessingResult:
    keyword_occurrences: List[dict]
    splits: List[SplitInfo]
    output_dir: Path

class AudioProcessor:
    def __init__(self, trim_seconds: float = 2.0, trim_before: bool = False):
        self.trim_seconds = trim_seconds
        self.trim_before = trim_before
    
    def find_keyword_occurrences(self, words: List[dict], keyword: str) -> List[dict]:
        """Find all occurrences of the keyword in the transcription."""
        keyword_occurrences = []
        
        for word in words:
            # Clean and normalize text for comparison
            word_text = clean_text(word["word"])
            search_keyword = clean_text(keyword)
            
            # Debug print to help diagnose matches
            print(f"Comparing - Word: '{word['word']}' -> '{word_text}', Keyword: '{keyword}' -> '{search_keyword}'")
            
            if search_keyword in word_text:
                keyword_occurrences.append(word)
        
        return keyword_occurrences
    
    def process_audio(self, input_file: Path, keyword: str, keyword_occurrences: List[dict]) -> ProcessingResult:
        """Process audio file, splitting it at keyword occurrences."""
        # Create output directory
        output_dir = Path('output') / input_file.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load audio file
        print("Loading audio file...")
        audio = AudioSegment.from_file(input_file)
        audio_duration = len(audio) / 1000.0  # Duration in seconds
        
        splits_info = []
        if keyword_occurrences:
            print(f"Found {len(keyword_occurrences)} occurrences of '{keyword}'")
            
            # Get timestamps and add start/end points
            timestamps = [word["start"] for word in keyword_occurrences]
            timestamps.insert(0, 0)
            timestamps.append(audio_duration)
            
            # Split audio at timestamps
            for i in range(len(timestamps) - 1):
                start_time = timestamps[i]
                end_time = timestamps[i + 1]
                
                # Convert to milliseconds for pydub
                start_ms = int(start_time * 1000)
                end_ms = int(end_time * 1000)
                
                # Apply trimming based on settings
                if i > 0:  # not the first segment
                    trim_ms = int(self.trim_seconds * 1000)
                    if self.trim_before:
                        end_ms -= trim_ms  # remove from end of previous segment
                    else:
                        start_ms += trim_ms  # remove from start of next segment
                
                # Extract segment
                segment = audio[start_ms:end_ms]
                
                # Save segment
                output_file = output_dir / f"part_{i+1}.mp3"
                segment.export(output_file, format="mp3")
                print(f"Saved {output_file}")
                
                # Record split information
                splits_info.append(SplitInfo(
                    part=i + 1,
                    start_time=start_time,
                    end_time=end_time,
                    duration=(end_ms - start_ms) / 1000.0,
                    file=output_file.name
                ))
        else:
            print(f"No occurrences of '{keyword}' found in {input_file}")
        
        # Move original file to output directory
        new_input_location = output_dir / input_file.name
        input_file.rename(new_input_location)
        print(f"Moved original file to {output_dir}")
        
        return ProcessingResult(
            keyword_occurrences=keyword_occurrences,
            splits=splits_info,
            output_dir=output_dir
        )
    
    def save_metadata(self, output_dir: Path, base_name: str, result: ProcessingResult,
                     transcription_text: str, language: str, keyword: str) -> None:
        """Save transcription and metadata to JSON and TXT files."""
        # Save JSON metadata
        json_data = {
            "full_text": transcription_text,
            "language": language,
            "keyword": keyword,
            "keyword_occurrences": result.keyword_occurrences,
            "splits": [vars(split) for split in result.splits]
        }
        
        json_file = output_dir / f"{base_name}_transcription.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"Saved transcription data to {json_file}")
        
        # Save human-readable text version
        txt_file = output_dir / f"{base_name}_transcription.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Full Transcription:\n{transcription_text}\n\n")
            f.write(f"Keyword: {keyword}\n")
            f.write(f"Found {len(result.keyword_occurrences)} occurrences at:\n")
            for occ in result.keyword_occurrences:
                f.write(f"- {occ['word']} at {format_time(occ['start'])}\n")
            f.write("\nSplit Information:\n")
            for split in result.splits:
                f.write(f"- {split.file}: {format_time(split.start_time)} to {format_time(split.end_time)} "
                       f"(duration: {format_time(split.duration)})\n")
        print(f"Saved transcription text to {txt_file}")
