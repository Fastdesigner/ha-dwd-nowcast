"""Vendored wradlib RADOLAN reader (binary composite) + DWD grid georef.

Only the pieces needed to read the DWD RADVOR "RV" composite (a RADOLAN
binary product on the DE1200 1100x1200 grid) are exported. Pure numpy —
GDAL/osr is optional and falls back to trigonometric projection.

License of radolan.py / georef.py / util.py: wradlib (MIT). See upstream
https://github.com/wradlib/wradlib
"""

from .radolan import read_radolan_composite
from .georef import get_radolan_grid

__all__ = ["read_radolan_composite", "get_radolan_grid"]
