from pathlib import Path
import configparser
from typing import List, Optional, Tuple

class Config:
    def __init__(self, config_file: str = "settings.ini"):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.default_input_dir = 'input'
        self.default_output_dir = 'output'
    
    def get_directories(self) -> Tuple[Path, Path]:
        """Get input and output directories from settings file or use defaults."""
        if self.config_file.exists():
            self.config.read(self.config_file)
            if 'Settings' in self.config:
                input_dir = self.config['Settings'].get('input_dir', self.default_input_dir)
                output_dir = self.config['Settings'].get('output_dir', self.default_output_dir)
                return Path(input_dir), Path(output_dir)
        
        # If no config exists, save defaults
        self.save_directories(self.default_input_dir, self.default_output_dir)
        return Path(self.default_input_dir), Path(self.default_output_dir)
    
    def save_directories(self, input_dir: str, output_dir: str) -> None:
        """Save directories to settings file."""
        if not self.config.has_section('Settings'):
            self.config['Settings'] = {}
        self.config['Settings']['input_dir'] = input_dir
        self.config['Settings']['output_dir'] = output_dir
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    def get_keywords(self, cli_keywords: Optional[str] = None) -> List[str]:
        """Get keywords from CLI argument or settings file, prompting if neither exists."""
        if cli_keywords:
            keywords = [k.strip() for k in cli_keywords.split(',')]
            self.save_keywords(keywords)
            return keywords
        
        if self.config_file.exists():
            self.config.read(self.config_file)
            if 'Settings' in self.config and 'keywords' in self.config['Settings']:
                return [k.strip() for k in self.config['Settings']['keywords'].split(',')]
        
        keyword = input("Enter the keyword(s) to split on (comma-separated): ")
        keywords = [k.strip() for k in keyword.split(',')]
        self.save_keywords(keywords)
        return keywords
    
    def save_keywords(self, keywords: List[str]) -> None:
        """Save keywords to settings file."""
        if not self.config.has_section('Settings'):
            self.config['Settings'] = {}
        self.config['Settings']['keywords'] = ','.join(keywords)
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
