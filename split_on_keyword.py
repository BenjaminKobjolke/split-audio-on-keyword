import os
import whisper
from pydub import AudioSegment
import shutil
import configparser
import argparse

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

def process_audio_file(input_file, keyword):
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory
    output_dir = os.path.join('output', base_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load whisper model
    print(f"Loading whisper model for {input_file}...")
    model = whisper.load_model("base")
    
    # Transcribe the audio
    print("Transcribing audio...")
    result = model.transcribe(input_file, word_timestamps=True)
    
    # Find timestamps for the keyword
    timestamps = []
    for segment in result["segments"]:
        for word in segment["words"]:
            if keyword.lower() in word["word"].lower():
                timestamps.append(word["start"])
    
    if not timestamps:
        print(f"No occurrences of '{keyword}' found in {input_file}")
        return
    
    print(f"Found {len(timestamps)} occurrences of '{keyword}'")
    
    # Load audio file
    audio = AudioSegment.from_file(input_file)
    
    # Add start and end times
    timestamps.insert(0, 0)
    timestamps.append(len(audio) / 1000.0)  # Convert milliseconds to seconds
    
    # Split audio at timestamps
    for i in range(len(timestamps) - 1):
        start_time = timestamps[i]
        end_time = timestamps[i + 1]
        
        # Convert to milliseconds for pydub
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # For parts after the first one (after keyword), remove first 2 seconds
        if i > 0:  # not the first segment
            start_ms += 2000  # add 2 seconds (2000 ms)
        
        # Extract segment
        segment = audio[start_ms:end_ms]
        
        # Save segment
        output_file = os.path.join(output_dir, f"part_{i+1}.mp3")
        segment.export(output_file, format="mp3")
        print(f"Saved {output_file}")
    
    # Move original file to output directory
    shutil.move(input_file, os.path.join(output_dir, os.path.basename(input_file)))
    print(f"Moved original file to {output_dir}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Split audio files based on a keyword')
    parser.add_argument('--keyword', help='Keyword to split on (overrides settings.ini)')
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
            process_audio_file(input_file, keyword)

if __name__ == "__main__":
    main()
