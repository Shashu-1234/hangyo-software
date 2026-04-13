#!/usr/bin/env python3
"""
Hangyo Ice Cream Distribution Manager v2.0
Run this file to start the application.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from main import LoginWindow

if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()
