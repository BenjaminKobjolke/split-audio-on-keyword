from pathlib import Path
import torch
import whisper
from typing import Dict, Any, Optional
from dataclasses import dataclass
from rich import print

@dataclass
class TranscriptionResult:
    text: str
    language: str
    segments: list
    words: list

class TranscriptionManager:
    def __init__(self, model_name: str = "base", language: Optional[str] = None):
        self.model_name = model_name
        self.language = language
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
    
    def initialize_model(self) -> None:
        """Initialize the Whisper model."""
        if self.device == "cuda":
            print(f"[green]Using CUDA with {torch.cuda.get_device_name(0)}[/green]")
        else:
            print("[yellow]CUDA not available, using CPU[/yellow]")
        
        print(f"Loading whisper model '{self.model_name}'...")
        self.model = whisper.load_model(self.model_name).to(self.device)
    
    def transcribe(self, audio_file: Path) -> TranscriptionResult:
        """Transcribe audio file using Whisper."""
        if not self.model:
            self.initialize_model()
        
        # Prepare transcription options
        options = {
            'word_timestamps': True,
            'verbose': True,
            'condition_on_previous_text': False
        }
        
        if self.language:
            options['language'] = self.language
            print(f"Using language: {self.language}")
        
        # Transcribe audio
        print("Transcribing audio...")
        result = self.model.transcribe(str(audio_file), **options)
        print(f"Detected language: {result['language']}")
        
        return TranscriptionResult(
            text=result["text"],
            language=result["language"],
            segments=result["segments"],
            words=[word for segment in result["segments"] 
                  for word in segment["words"]]
        )
