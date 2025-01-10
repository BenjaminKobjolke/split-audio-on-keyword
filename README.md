# Split Audio on Keyword

A Python tool that uses OpenAI's Whisper to transcribe audio files and split them at occurrences of a specified keyword.

## Features

- Transcribes audio files using OpenAI's Whisper model
- Splits audio files at occurrences of a specified keyword
- Supports MP3 and OGG formats
- Saves keyword preference in settings.ini
- Removes 2 seconds from the beginning of each part after the keyword for cleaner splits

## Quick Setup (Windows)

1. Run `install.bat` to create a virtual environment and install all requirements
2. Use `activate_environment.bat` to activate the virtual environment when you want to use the tool

## Manual Setup

If you prefer to set up manually or are using Linux/Mac:

1. Create Python virtual environment:

```bash
python -m venv venv
```

2. Activate virtual environment:

- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Install requirements:

```bash
pip install -r requirements.txt
```

## Usage

1. Create an `input` directory and place your audio files (MP3 or OGG) there.

2. Run the script:

```bash
python split_on_keyword.py
```

On first run, you'll be prompted to enter a keyword. This will be saved to `settings.ini` for future use.

### Command Line Arguments

- `--keyword`: Override the saved keyword

```bash
python split_on_keyword.py --keyword "new-keyword"
```

## Output

The script creates an `output` directory with the following structure:

```
output/
  └── original_filename/
      ├── original_file.mp3
      ├── part_1.mp3
      ├── part_2.mp3
      └── ...
```

Each part represents a section of the audio:

- part_1: From start to first keyword
- part_2: From first to second keyword (if exists)
- Last part: From last keyword to end

Note: Parts after the first one start 2 seconds after the keyword occurrence for cleaner splits.

## Configuration

The keyword is stored in `settings.ini`. You can:

- Let the script prompt you for a keyword on first run
- Provide a keyword via command line argument
- Manually edit settings.ini

## Requirements

- Python 3.6+
- FFmpeg (required by pydub for audio processing)
- Internet connection (for initial Whisper model download)
