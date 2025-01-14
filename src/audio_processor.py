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
    
    def find_keyword_occurrences(self, words: List[dict], keywords: List[str]) -> List[dict]:
        """Find all occurrences of any keyword in the transcription."""
        keyword_occurrences = []
        
        for word in words:
            # Clean and normalize text for comparison
            word_text = clean_text(word["word"])
            
            # Check each keyword
            for keyword in keywords:
                search_keyword = clean_text(keyword)
                
                # Debug print to help diagnose matches
                print(f"Comparing - Word: '{word['word']}' -> '{word_text}', Keyword: '{keyword}' -> '{search_keyword}'")
                
                if search_keyword in word_text:
                    # Add the matched keyword to the word info
                    word_with_keyword = word.copy()
                    word_with_keyword["matched_keyword"] = keyword
                    keyword_occurrences.append(word_with_keyword)
                    break  # Stop checking other keywords once we find a match
        
        return keyword_occurrences
    
    def process_audio(self, input_file: Path, keywords: List[str], keyword_occurrences: List[dict],
                     output_base_dir: Path,
                     end_keyword_occurrences: Optional[List[dict]] = None,
                     trim_end_keyword_seconds: float = 2.0,
                     trim_end_keyword_before: bool = False) -> ProcessingResult:
        """Process audio file, splitting it at keyword occurrences."""
        # Create output directory for this file's results
        output_dir = output_base_dir / input_file.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load audio file
        print("Loading audio file...")
        audio = AudioSegment.from_file(input_file)
        audio_duration = len(audio) / 1000.0  # Duration in seconds
        
        splits_info = []
        if keyword_occurrences:
            print(f"Found {len(keyword_occurrences)} keyword occurrences")
            for occ in keyword_occurrences:
                print(f"- '{occ['matched_keyword']}' at {format_time(occ['start'])}")
            
            # Get timestamps for main keyword
            timestamps = [word["start"] for word in keyword_occurrences]
            
            # Process each keyword occurrence
            for i, start_time in enumerate(timestamps):
                # Initialize end time and milliseconds
                end_time = audio_duration
                start_ms = int(start_time * 1000)
                end_ms = int(end_time * 1000)
                
                # Find the next end keyword after this timestamp
                if end_keyword_occurrences:
                    for end_word in end_keyword_occurrences:
                        if end_word["start"] > start_time:
                            # Found an end keyword after current timestamp
                            end_word_time = end_word["start"]
                            trim_ms = int(trim_end_keyword_seconds * 1000)
                            
                            if trim_end_keyword_before:
                                # Remove seconds before the end keyword
                                end_time = end_word_time
                                end_ms = int(end_time * 1000) - trim_ms
                            else:
                                # Remove seconds after the end keyword
                                end_time = end_word_time
                                end_ms = int(end_time * 1000) + trim_ms
                            break
                
                # Apply trimming based on settings
                trimmed_start_time = start_time
                trim_ms = int(self.trim_seconds * 1000)
                
                if self.trim_before:
                    # Remove from end of previous segment
                    end_ms = int(end_time * 1000) - trim_ms
                    end_time -= self.trim_seconds
                else:
                    # Remove from start of current segment
                    start_ms += trim_ms
                    trimmed_start_time += self.trim_seconds
                
                # Extract segment
                segment = audio[start_ms:end_ms]
                
                # Save segment
                output_file = output_dir / f"part_{i+1}.mp3"
                segment.export(output_file, format="mp3")
                print(f"Saved {output_file}")
                
                # Record split information with trimmed timestamps
                splits_info.append(SplitInfo(
                    part=i + 1,
                    start_time=trimmed_start_time,
                    end_time=end_time,
                    duration=(end_ms - start_ms) / 1000.0,
                    file=output_file.name
                ))
            
        else:
            print(f"No keyword occurrences found in {input_file}")
        
        # Copy original file to output directory
        new_input_location = output_dir / input_file.name
        try:
            # Try to move the file first
            input_file.rename(new_input_location)
            print(f"Moved original file to {output_dir}")
        except OSError:
            # If moving fails (e.g., across drives), copy instead
            import shutil
            shutil.copy2(input_file, new_input_location)
            print(f"Copied original file to {output_dir}")
        
        # Update keyword occurrences with trimmed timestamps
        trimmed_occurrences = []
        for i, occ in enumerate(keyword_occurrences):
            trimmed_occ = occ.copy()
            # Apply trimming to all occurrences
            if self.trim_before:
                # Keep original start time, end time is trimmed in splits
                trimmed_occ["end"] = occ["end"] - self.trim_seconds
            else:
                # Start time is trimmed
                trimmed_occ["start"] = occ["start"] + self.trim_seconds
                trimmed_occ["end"] = occ["end"] + self.trim_seconds
            trimmed_occurrences.append(trimmed_occ)

        return ProcessingResult(
            keyword_occurrences=trimmed_occurrences,
            splits=splits_info,
            output_dir=output_dir
        )
    
    def save_metadata(self, output_dir: Path, base_name: str, result: ProcessingResult,
                     transcription_text: str, language: str, keywords: List[str],
                     end_keywords: Optional[List[str]] = None) -> None:
        """Save transcription and metadata to JSON and TXT files."""
        # Save JSON metadata
        json_data = {
            "full_text": transcription_text,
            "language": language,
            "keywords": keywords,
            "keyword_occurrences": result.keyword_occurrences,
            "splits": [vars(split) for split in result.splits],
            "end_keywords": end_keywords
        }
        
        json_file = output_dir / f"{base_name}_transcription.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"Saved transcription data to {json_file}")
        
        # Save human-readable text version
        txt_file = output_dir / f"{base_name}_transcription.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Full Transcription:\n{transcription_text}\n\n")
            f.write(f"Main Keywords: {', '.join(keywords)}\n")
            if end_keywords:
                f.write(f"End Keywords: {', '.join(end_keywords)}\n")
            f.write(f"Found {len(result.keyword_occurrences)} occurrences at:\n")
            for occ in result.keyword_occurrences:
                f.write(f"- '{occ['matched_keyword']}' ({occ['word']}) at {format_time(occ['start'])}\n")
            f.write("\nSplit Information:\n")
            for split in result.splits:
                f.write(f"- {split.file}: {format_time(split.start_time)} to {format_time(split.end_time)} "
                       f"(duration: {format_time(split.duration)})\n")
        print(f"Saved transcription text to {txt_file}")
