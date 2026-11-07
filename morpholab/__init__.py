"""MorphoLab PTIT: reproducible 2D instance segmentation."""
__version__ = "1.0.0"

# Keep generated font cache inside the project, also under restricted execution.
import os as _os
from pathlib import Path as _Path
_cache = _Path(__file__).resolve().parents[1] / 'outputs' / '.matplotlib'
_cache.mkdir(parents=True,exist_ok=True)
_os.environ.setdefault('MPLCONFIGDIR',str(_cache))
