"""Re-export app from root main for compatibility."""
import sys
from pathlib import Path

# Add backend directory to path if not already there
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app  # noqa: F401
