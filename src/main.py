from pathlib import Path
import click
from rich import print
from rich.console import Console
from rich.progress import track

from config import Config
from transcription import TranscriptionManager
from audio_processor import AudioProcessor
from utils import ensure_directories, get_audio_files

console = Console()

@click.command()
@click.option('--keyword', help='Keyword to split on (overrides settings.ini)')
@click.option('--model', 
             type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']),
             default='base',
             help='Whisper model to use (default: base)')
@click.option('--language',
             help='Language code for transcription (e.g., "en" for English, "de" for German)')
@click.option('--trim-remove-seconds',
             type=float,
             default=2.0,
             help='Number of seconds to remove when trimming (default: 2.0)')
@click.option('--trim-before',
             is_flag=True,
             help='Remove seconds before the keyword instead of after')
def main(keyword: str, model: str, language: str, 
         trim_remove_seconds: float, trim_before: bool):
    """Split audio files based on keyword occurrences."""
    try:
        # Initialize components
        config = Config()
        keyword = config.get_keyword(keyword)
        print(f"Using keyword: {keyword}")
        
        transcriber = TranscriptionManager(model_name=model, language=language)
        processor = AudioProcessor(trim_seconds=trim_remove_seconds, trim_before=trim_before)
        
        # Ensure directories exist and get audio files
        input_dir, _ = ensure_directories()
        audio_files = get_audio_files(input_dir)
        
        if not audio_files:
            return
        
        for audio_file in track(audio_files, description="Processing audio files"):
            print(f"\n[bold blue]Processing {audio_file.name}...[/bold blue]")
            
            # Transcribe audio
            transcription = transcriber.transcribe(audio_file)
            
            # Find keyword occurrences
            keyword_occurrences = processor.find_keyword_occurrences(
                transcription.words, keyword
            )
            
            # Process audio and save splits
            result = processor.process_audio(
                audio_file, keyword, keyword_occurrences
            )
            
            # Save metadata
            processor.save_metadata(
                result.output_dir,
                audio_file.stem,
                result,
                transcription.text,
                transcription.language,
                keyword
            )
        
        print("\n[green]Processing complete![/green]")
        
    except Exception as e:
        console.print_exception()
        raise click.ClickException(str(e))

if __name__ == "__main__":
    main()
