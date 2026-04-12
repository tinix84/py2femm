import sys
from pathlib import Path

# Make examples importable for tests that validate generated Lua
_examples_dir = str(Path(__file__).resolve().parent.parent / "examples" / "heatflow" / "heatsink")
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)
