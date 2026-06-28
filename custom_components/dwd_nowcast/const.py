"""Constants for the DWD Nowcast (RADVOR RV) integration."""

from __future__ import annotations

DOMAIN = "dwd_nowcast"
PLATFORMS = ["sensor"]

# --- Configuration keys ---
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_THRESHOLD_ENTITY = "threshold_entity"
CONF_WARNING_ENTITY = "warning_entity"
CONF_STEP_MINUTES = "step_minutes"
CONF_HORIZON_MINUTES = "horizon_minutes"

# --- Defaults ---
# The strong-rain threshold is NEVER hardcoded: it is read live from this
# helper. Default points at the existing "Regenwarnung" helper (mm/h).
DEFAULT_THRESHOLD_ENTITY = "input_number.regenwarnung"
DEFAULT_WARNING_ENTITY = ""
DEFAULT_STEP_MINUTES = 10
DEFAULT_HORIZON_MINUTES = 60
# RV is released every 5 minutes on DWD OpenData.
DEFAULT_SCAN_INTERVAL_SECONDS = 300

# --- Classification labels (per task spec) ---
CLASS_DRY = "trocken"
CLASS_MINIMAL = "minimal / unsicher"
CLASS_POSSIBLE = "Regen möglich"
CLASS_RAIN = "Regen"
CLASS_STRONG = "starker Regen"
CLASS_MISSING = "fehlt"

UNIT_MMH = "mm/h"


def classify(mmh: float | None, strong_threshold: float | None) -> str:
    """Classify a rain rate (mm/h) per the project spec.

    Thresholds:
      trocken             = 0.0
      minimal / unsicher  > 0.0  .. < 0.2
      Regen möglich       >= 0.2 .. < 1.0
      Regen               >= 1.0 .. < strong_threshold
      starker Regen       >= strong_threshold   (from the HA helper)

    If ``strong_threshold`` is None (helper unavailable) nothing is promoted
    to "starker Regen" — the caller must surface the error instead of
    fabricating a threshold.
    """
    if mmh is None:
        return CLASS_MISSING
    if mmh <= 0.0:
        return CLASS_DRY
    if mmh < 0.2:
        return CLASS_MINIMAL
    if mmh < 1.0:
        return CLASS_POSSIBLE
    if strong_threshold is not None and mmh >= strong_threshold:
        return CLASS_STRONG
    return CLASS_RAIN
