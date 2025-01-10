from pathlib import Path
import configparser
from typing import Optional

class Config:
    def __init__(self, config_file: str = "settings.ini"):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
    
    def get_keyword(self, cli_keyword: Optional[str] = None) -> str:
        """Get keyword from CLI argument or settings file, prompting if neither exists."""
        if cli_keyword:
            self.save_keyword(cli_keyword)
            return cli_keyword
        
        if self.config_file.exists():
            self.config.read(self.config_file)
            if 'Settings' in self.config and 'keyword' in self.config['Settings']:
                return self.config['Settings']['keyword']
        
        keyword = input("Enter the keyword to split on: ")
        self.save_keyword(keyword)
        return keyword
    
    def save_keyword(self, keyword: str) -> None:
        """Save keyword to settings file."""
        self.config['Settings'] = {'keyword': keyword}
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
