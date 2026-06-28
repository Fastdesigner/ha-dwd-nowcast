"""Fetch and parse the DWD RADVOR "RV" radar nowcast composite.

The RV product (https://opendata.dwd.de/weather/radar/composite/rv/) is a
RADOLAN *binary* composite on the DE1200 1100x1200 / 1 km grid, released every
5 minutes. Each ``.tar.bz2`` archive holds 25 members with lead times
000, 005, ... 120 minutes. ``read_radolan_composite`` returns values already
scaled to **mm per 5 min**; rain rate (mm/h) = value * 12.

This module is intentionally free of Home Assistant imports so the exact same
code path can be unit-tested standalone.
"""

from __future__ import annotations

import bz2
import io
import re
import tarfile
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np

from .radar import get_radolan_grid, read_radolan_composite

RV_BASE = "https://opendata.dwd.de/weather/radar/composite/rv/"
_FILE_RE = re.compile(r'href="(DE1200_RV\d{10}\.tar\.bz2)"')
_MEMBER_RE = re.compile(r"_(\d{3})$")
_USER_AGENT = "home-assistant-dwd-nowcast/0.1 (+opendata.dwd.de)"

# mm per 5-min interval -> mm/h
MM5_TO_MMH = 12.0


def _http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed host)
        return resp.read()


def list_latest_files(limit: int = 4, timeout: int = 60) -> list[str]:
    """Return the newest RV archive filenames (newest first)."""
    html = _http_get(RV_BASE, timeout=timeout).decode("utf-8", "replace")
    files = sorted(set(_FILE_RE.findall(html)))
    return files[-limit:][::-1]


def _parse_ts(filename: str) -> datetime:
    m = re.search(r"DE1200_RV(\d{10})\.tar\.bz2", filename)
    ts = datetime.strptime(m.group(1), "%y%m%d%H%M")
    return ts.replace(tzinfo=timezone.utc)


def _grid_index(lat: float, lon: float, shape: tuple[int, int]):
    """Nearest grid cell to (lat, lon) on the array's own DE1200 grid.

    The data array and ``get_radolan_grid`` share a lower-left origin, so the
    index applies directly to the array (no orientation guesswork).
    """
    grid = get_radolan_grid(shape[0], shape[1], wgs84=True)
    lon_g = grid[:, :, 0]
    lat_g = grid[:, :, 1]
    d2 = (lat_g - lat) ** 2 + (lon_g - lon) ** 2
    row, col = np.unravel_index(int(np.argmin(d2)), d2.shape)
    return int(row), int(col), float(lon_g[row, col]), float(lat_g[row, col])


def fetch_rv_series(lat: float, lon: float, leads=None, timeout: int = 60) -> dict:
    """Fetch the latest RV nowcast and extract the home-cell rain series.

    Args:
        lat, lon: exact location (decimal degrees).
        leads: iterable of lead minutes to extract (e.g. range(0, 121, 10)).
            None extracts all available 5-min steps.
        timeout: per-request timeout (seconds).

    Returns a dict with:
        filename, data_timestamp (aware UTC), cell_row, cell_col,
        cell_lon, cell_lat, series ({lead_min: mm_per_5min | None}).

    The implementation is built to extend to a 3x3 neighbourhood later:
    ``_grid_index`` already returns (row, col); a future version can read
    data[row-1:row+2, col-1:col+2] and aggregate. For now only the home cell
    is used.

    Raises RuntimeError on hard failure (after trying a few recent releases).
    """
    files = list_latest_files(limit=4, timeout=timeout)
    if not files:
        raise RuntimeError("Keine RV-Dateien im DWD-OpenData-Verzeichnis gefunden")

    last_err: Exception | None = None
    for fname in files:
        try:
            raw = _http_get(RV_BASE + fname, timeout=timeout)
            tar_bytes = bz2.decompress(raw)
            with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tf:
                members = {}
                for m in tf.getmembers():
                    mm = _MEMBER_RE.search(m.name)
                    if mm:
                        members[int(mm.group(1))] = m
                if not members:
                    raise RuntimeError("RV-Archiv enthält keine Datensätze")

                want = sorted(members) if leads is None else [
                    l for l in leads if l in members
                ]
                cell = None
                series: dict[int, float | None] = {}
                for lead in want:
                    data, _attrs = read_radolan_composite(
                        io.BytesIO(tf.extractfile(members[lead]).read())
                    )
                    if cell is None:
                        cell = _grid_index(lat, lon, data.shape)
                    val = float(data[cell[0], cell[1]])
                    series[lead] = None if np.isnan(val) else round(val, 3)

            return {
                "filename": fname,
                "data_timestamp": _parse_ts(fname),
                "cell_row": cell[0],
                "cell_col": cell[1],
                "cell_lon": round(cell[2], 4),
                "cell_lat": round(cell[3], 4),
                "series": series,
            }
        except Exception as err:  # noqa: BLE001 - try an older release, report last
            last_err = err
            continue

    raise RuntimeError(f"RV-Abruf fehlgeschlagen: {last_err}")
