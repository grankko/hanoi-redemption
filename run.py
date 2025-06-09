#!/usr/bin/env python3
"""
Launcher script for Towers of Hanoi AI Testing Application.
This script handles the module path setup and launches the main application.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Launch the Towers of Hanoi AI testing application."""
    try:
        from src.main import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
