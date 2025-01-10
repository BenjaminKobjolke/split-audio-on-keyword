import os
import whisper
from pydub import AudioSegment
import shutil
import configparser
import argparse
import json
import torch

def get_keyword(args):
    config = configparser.ConfigParser()
    
    # Check if keyword is provided via command line
    if args.keyword:
        # Save the new keyword to settings
        config['Settings'] = {'keyword': args.keyword}
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
        return args.keyword
    
    # Try to read existing settings
    if os.path.exists('settings.ini'):
        config.read('settings.ini')
        if 'Settings' in config and 'keyword' in config['Settings']:
            return config['Settings']['keyword']
    
    # If no keyword in settings, ask user
    keyword = input("Enter the keyword to split on: ")
    
    # Save the keyword to settings
    config['Settings'] = {'keyword': keyword}
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)
    
    return keyword

def process_audio_file(input_file, keyword, model_name, language=None, trim_seconds=2, trim_before=False):
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory
    output_dir = os.path.join('output', base_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Check for CUDA availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"Using CUDA with {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA not available, using CPU")
    
    # Load whisper model
    print(f"Loading whisper model '{model_name}' for {input_file}...")
    model = whisper.load_model(model_name).to(device)
    
    # Transcribe the audio with progress updates
    print("Transcribing audio...")
    
    # Prepare transcription options
    transcribe_options = {
        'word_timestamps': True,
        'verbose': True,  # Show progress bar
        'condition_on_previous_text': False  # Don't condition on previous text for more accurate timestamps
    }
    
    # Add language if specified
    if language:
        transcribe_options['language'] = language
        print(f"Using language: {language}")
    
    # Transcribe with progress bar
    result = model.transcribe(input_file, **transcribe_options)
    print(f"Detected language: {result['language']}")
    
    # Load audio file
    print("Loading audio file...")
    audio = AudioSegment.from_file(input_file)
    audio_duration = len(audio) / 1000.0  # Duration in seconds
    
    # Find timestamps for the keyword
    timestamps = []
    keyword_occurrences = []
    splits_info = []
    
    # Collect all words with timestamps and find keyword occurrences
    all_words = []
    for segment in result["segments"]:
        for word in segment["words"]:
            word_info = {
                "word": word["word"],
                "start": word["start"],
                "end": word.get("end", word["start"] + 1)  # fallback if end not provided
            }
            all_words.append(word_info)
            
            if keyword.lower() in word["word"].lower():
                timestamps.append(word["start"])
                keyword_occurrences.append(word_info)
    
    if not timestamps:
        print(f"No occurrences of '{keyword}' found in {input_file}")
    else:
        print(f"Found {len(timestamps)} occurrences of '{keyword}'")
        
        # Add start and end times
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
                trim_ms = int(trim_seconds * 1000)
                if trim_before:
                    end_ms -= trim_ms  # remove from end of previous segment
                else:
                    start_ms += trim_ms  # remove from start of next segment
            
            # Extract segment
            segment = audio[start_ms:end_ms]
            
            # Save segment
            output_file = os.path.join(output_dir, f"part_{i+1}.mp3")
            segment.export(output_file, format="mp3")
            print(f"Saved {output_file}")
            
            # Record split information
            splits_info.append({
                "part": i + 1,
                "start_time": start_time,
                "end_time": end_time,
                "duration": (end_ms - start_ms) / 1000.0,  # in seconds
                "file": f"part_{i+1}.mp3"
            })
    
    # Save transcription and metadata to JSON
    transcription_data = {
        "full_text": result["text"],
        "language": result["language"],
        "all_words": all_words,
        "keyword": keyword,
        "keyword_occurrences": keyword_occurrences,
        "splits": splits_info
    }
    
    json_file = os.path.join(output_dir, f"{base_name}_transcription.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(transcription_data, f, indent=2, ensure_ascii=False)
    print(f"Saved transcription data to {json_file}")
    
    # Also save a simple text version
    txt_file = os.path.join(output_dir, f"{base_name}_transcription.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Full Transcription:\n{result['text']}\n\n")
        f.write(f"Keyword: {keyword}\n")
        f.write(f"Found {len(keyword_occurrences)} occurrences at:\n")
        for occ in keyword_occurrences:
            f.write(f"- {occ['word']} at {occ['start']:.2f}s\n")
        f.write("\nSplit Information:\n")
        for split in splits_info:
            f.write(f"- {split['file']}: {split['start_time']:.2f}s to {split['end_time']:.2f}s (duration: {split['duration']:.2f}s)\n")
    print(f"Saved transcription text to {txt_file}")
    
    # Move original file to output directory
    shutil.move(input_file, os.path.join(output_dir, os.path.basename(input_file)))
    print(f"Moved original file to {output_dir}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Split audio files based on a keyword')
    parser.add_argument('--keyword', help='Keyword to split on (overrides settings.ini)')
    parser.add_argument('--model', 
                      choices=['tiny', 'base', 'small', 'medium', 'large'],
                      default='base',
                      help='Whisper model to use (default: base). Larger models are more accurate but slower.')
    parser.add_argument('--language',
                      help='Language code for transcription (e.g., "en" for English, "de" for German). '
                           'If not specified, Whisper will auto-detect the language.')
    parser.add_argument('--trim-remove-seconds',
                      type=float,
                      default=2.0,
                      help='Number of seconds to remove when trimming (default: 2.0)')
    parser.add_argument('--trim-before',
                      action='store_true',
                      help='Remove seconds before the keyword instead of after')
    args = parser.parse_args()
    
    # Get the keyword
    keyword = get_keyword(args)
    print(f"Using keyword: {keyword}")
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Process all mp3 and ogg files in input directory
    for filename in os.listdir('input'):
        if filename.lower().endswith(('.mp3', '.ogg')):
            input_file = os.path.join('input', filename)
            print(f"\nProcessing {filename}...")
            process_audio_file(input_file, keyword, args.model, args.language, 
                             trim_seconds=args.trim_remove_seconds, 
                             trim_before=args.trim_before)

if __name__ == "__main__":
    main()
