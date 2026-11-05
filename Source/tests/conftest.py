"""Pytest configuration and common fixtures for Griductive Solver."""

import sys
from pathlib import Path

# Add Source/ directory to sys.path so imports like 'from common...' work seamlessly
SOURCE_DIR = Path(__file__).resolve().parent.parent
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

