# run.py
#!/usr/bin/env python3
"""
Discord Bot Launcher
Run this file to start your bot
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from bot import main

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════╗
    ║     DISCORD BOT LAUNCHER v1.0      ║
    ║        Starting up... 🔥           ║
    ╚════════════════════════════════════╝
    """)
    main()