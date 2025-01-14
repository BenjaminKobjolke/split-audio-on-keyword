from pathlib import Path
from typing import Optional
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
@click.option('--keyword', help='Keyword(s) to split on (comma-separated, overrides settings.ini)')
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
@click.option('--end-keyword',
             help='Keyword(s) that mark the end of a segment (comma-separated)')
@click.option('--trim-end-keyword-remove-seconds',
             type=float,
             default=2.0,
             help='Number of seconds to remove when trimming around end-keyword (default: 2.0)')
@click.option('--trim-end-keyword-before',
             is_flag=True,
             help='Remove seconds before the end-keyword instead of after')
@click.option('--input-dir',
             type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
             help='Input directory (overrides settings.ini)')
@click.option('--output-dir',
             type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
             help='Output directory (overrides settings.ini)')
def main(keyword: str, model: str, language: str, 
         trim_remove_seconds: float, trim_before: bool, end_keyword: str,
         trim_end_keyword_remove_seconds: float, trim_end_keyword_before: bool,
         input_dir: Optional[Path], output_dir: Optional[Path]):
    """Split audio files based on keyword occurrences."""
    try:
        # Initialize components
        config = Config()
        keywords = config.get_keywords(keyword)
        print(f"Using keywords: {', '.join(keywords)}")
        
        transcriber = TranscriptionManager(model_name=model, language=language)
        processor = AudioProcessor(trim_seconds=trim_remove_seconds, trim_before=trim_before)
        
        # Get configured directories and ensure they exist
        config_input_dir, config_output_dir = config.get_directories()
        
        # CLI options override config
        if input_dir:
            # Clean any trailing quotes from paths
            input_dir = Path(str(input_dir).strip('"'))
            config.save_directories(str(input_dir), str(config_output_dir))
            config_input_dir = input_dir
        if output_dir:
            # Clean any trailing quotes from paths
            output_dir = Path(str(output_dir).strip('"'))
            config.save_directories(str(config_input_dir), str(output_dir))
            config_output_dir = output_dir
            
        input_dir, output_dir = ensure_directories(config_input_dir, config_output_dir)
        audio_files = get_audio_files(input_dir)
        
        if not audio_files:
            return
        
        for audio_file in track(audio_files, description="Processing audio files"):
            print(f"\n[bold blue]Processing {audio_file.name}...[/bold blue]")
            
            # Transcribe audio
            transcription = transcriber.transcribe(audio_file)
            
            # Find keyword occurrences
            keyword_occurrences = processor.find_keyword_occurrences(
                transcription.words, keywords
            )
            
            # Find end-keywords occurrences if specified
            end_keyword_occurrences = None
            if end_keyword:
                end_keywords = [k.strip() for k in end_keyword.split(',')]
                end_keyword_occurrences = processor.find_keyword_occurrences(
                    transcription.words, end_keywords
                )
                if end_keyword_occurrences:
                    print(f"Found {len(end_keyword_occurrences)} end-keyword occurrences")
            
            # Process audio and save splits
            result = processor.process_audio(
                audio_file, keywords, keyword_occurrences,
                output_base_dir=output_dir,
                end_keyword_occurrences=end_keyword_occurrences,
                trim_end_keyword_seconds=trim_end_keyword_remove_seconds,
                trim_end_keyword_before=trim_end_keyword_before
            )
            
            # Save metadata
            processor.save_metadata(
                result.output_dir,
                audio_file.stem,
                result,
                transcription.text,
                transcription.language,
                keywords,
                end_keywords=end_keywords if end_keyword else None
            )
        
        print("\n[green]Processing complete![/green]")
        
    except Exception as e:
        console.print_exception()
        raise click.ClickException(str(e))

if __name__ == "__main__":
    main()
