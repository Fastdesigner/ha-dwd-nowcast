# DWD Nowcast (RADVOR RV) – Home Assistant

Liest den **DWD-RADVOR-„RV"-Radar-Nowcast** (echte Radardaten, kein Screenshot)
für die **exakte Hauskoordinate** und stellt ihn als Sensor mit
Forecast-Attributen bereit (10-Min-Raster, Horizont konfigurierbar).

- Quelle: `https://opendata.dwd.de/weather/radar/composite/rv/` (RADOLAN-Binär,
  DE1200-Gitter, 1 km, alle 5 Min, 0…+120 Min).
- Nur `numpy` nötig. Klassifizierung „starker Regen" über einen frei wählbaren
  Helfer (Default `input_number.regenwarnung`), nichts hartkodiert.
- Richtet sich beim ersten Start automatisch mit der HA-Hauskoordinate ein;
  Koordinate / Helfer / Horizont später über die Optionen änderbar.

Installation: HACS → Benutzerdefiniertes Repository (Integration) → Herunterladen
→ Home Assistant neu starten.

Details siehe `custom_components/dwd_nowcast/README.md`.
