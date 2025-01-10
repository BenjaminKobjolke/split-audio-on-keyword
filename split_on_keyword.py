#!/usr/bin/env python3
"""
Split Audio on Keyword - Command forwarding script.
This script forwards all commands to the modular implementation in src/main.py.
"""

import sys
import subprocess
import os

def main():
    if not os.path.exists('src/main.py'):
        print("Error: src/main.py not found. Please ensure the modular version is installed.")
        sys.exit(1)
    
    # Forward all arguments to src/main.py
    cmd = [sys.executable, 'src/main.py'] + sys.argv[1:]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
