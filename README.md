# Split Audio on Keyword

A Python tool that uses OpenAI's Whisper to transcribe audio files and split them at occurrences of a specified keyword.

## Features

- Transcribes audio files using OpenAI's Whisper model
- Splits audio files at occurrences of a specified keyword (case-insensitive, ignores punctuation)
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

- `--keyword`: Override the saved keyword (case-insensitive matching, ignores punctuation)
  - Example: "hello" will match "Hello!", "HELLO.", etc.
- `--model`: Choose Whisper model (default: base)
  - Available models: tiny, base, small, medium, large
  - Larger models are more accurate but slower and require more memory
- `--language`: Specify input language (optional)
  - Example codes: "en" (English), "de" (German), "fr" (French), etc.
  - If not specified, Whisper will auto-detect the language
  - Specifying the correct language can improve accuracy
- `--trim-remove-seconds`: Number of seconds to remove when trimming (default: 2.0)
  - Controls how many seconds to remove around the keyword
  - Can be a decimal number (e.g., 1.5)
- `--trim-before`: Remove seconds before the keyword instead of after
  - By default, seconds are removed after the keyword
  - With this flag, seconds are removed before the keyword

Examples:

```bash
# Override keyword
python split_on_keyword.py --keyword "new-keyword"

# Use a different model
python split_on_keyword.py --model large

# Specify language for better accuracy
python split_on_keyword.py --language de

# Use custom trim duration (3.5 seconds)
python split_on_keyword.py --trim-remove-seconds 3.5

# Remove seconds before the keyword instead of after
python split_on_keyword.py --trim-before

# Combine all options
python split_on_keyword.py --keyword "schnitzel" --model medium --language de --trim-remove-seconds 1.5 --trim-before
```

Common Language Codes:

- en: English
- de: German
- fr: French
- es: Spanish
- it: Italian
- ja: Japanese
- ko: Korean
- zh: Chinese
- ru: Russian
- nl: Dutch

Model Comparison:

- tiny: Fastest, lowest accuracy, ~1GB memory
- base: Good balance, ~1GB memory
- small: Better accuracy, ~2GB memory
- medium: High accuracy, ~5GB memory
- large: Best accuracy, ~10GB memory

## Output

The script creates an `output` directory with the following structure:

```
output/
  └── original_filename/
      ├── original_file.mp3          # Original audio file
      ├── part_1.mp3                 # First audio segment
      ├── part_2.mp3                 # Second audio segment
      ├── original_file_transcription.json  # Detailed transcription data
      ├── original_file_transcription.txt   # Human-readable transcription
      └── ...
```

The script always processes files and creates output, even if no keyword is found:

1. When keyword is found:

   - Creates split audio parts
   - Moves original file to output directory
   - Generates transcription files

2. When no keyword is found:
   - Moves original file to output directory
   - Generates transcription files with full text
   - No audio splits are created

Output files always include:

1. `*_transcription.json` contains:

   - Full transcription text
   - Language detection
   - Word-level timestamps
   - Keyword occurrences
   - Split information (timestamps and durations)

2. `*_transcription.txt` contains:
   - Full transcription text
   - Keyword occurrences with timestamps
   - Split information in human-readable format

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
- NVIDIA GPU with CUDA support (optional, for faster processing)

## CUDA Support

### Installation (Optional)

CUDA support is optional but recommended for faster processing. To enable it:

1. First, uninstall any existing PyTorch installation:

```bash
pip uninstall torch torchvision torchaudio
```

2. Install PyTorch with CUDA support:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Verification

To check if your system supports CUDA, run:

```bash
python check_cuda.py
```

This will display information about your system's CUDA capabilities and available GPU memory.

The main script automatically detects and uses CUDA if available:

- With NVIDIA GPU: Uses CUDA for faster processing
- Without GPU: Falls back to CPU processing

To check if CUDA is being used, look for the message "Using CUDA with [GPU name]" when running the script.

Memory Requirements:

- CPU: Models use system RAM
- GPU: Models use VRAM
  - tiny/base: ~1GB VRAM
  - small: ~2GB VRAM
  - medium: ~5GB VRAM
  - large: ~10GB VRAM
