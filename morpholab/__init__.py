"""MorphoLab: phân đoạn từng đối tượng trên ảnh 2D, có thể tái lập."""
__version__ = "1.2.0"

# Giữ bộ đệm font trong project để chạy được trong môi trường hạn chế.
import os as _os
from pathlib import Path as _Path
_cache = _Path(__file__).resolve().parents[1] / 'outputs' / '.matplotlib'
_cache.mkdir(parents=True,exist_ok=True)
_os.environ.setdefault('MPLCONFIGDIR',str(_cache))
