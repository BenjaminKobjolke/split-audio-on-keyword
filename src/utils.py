from pathlib import Path
from typing import List, Tuple
from rich import print

def ensure_directories() -> Tuple[Path, Path]:
    """Ensure input and output directories exist."""
    input_dir = Path('input')
    output_dir = Path('output')
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    return input_dir, output_dir

def get_audio_files(input_dir: Path) -> List[Path]:
    """Get all MP3 and OGG files from input directory."""
    audio_files = list(input_dir.glob('*.mp3')) + list(input_dir.glob('*.ogg'))
    
    if not audio_files:
        print("[yellow]Warning: No audio files found in input directory[/yellow]")
    else:
        print(f"Found {len(audio_files)} audio file(s)")
    
    return audio_files

def clean_text(text: str) -> str:
    """Clean and normalize text for comparison."""
    return ''.join(c for c in text.lower() if c.isalnum())

def format_time(seconds: float) -> str:
    """Format time in seconds to HH:MM:SS.mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
