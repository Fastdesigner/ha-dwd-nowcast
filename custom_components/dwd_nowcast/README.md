# DWD Nowcast (RADVOR RV) – Hausstandort

Eigenständige Home-Assistant-Integration, die den **DWD-RADVOR-„RV"-Radar-Nowcast**
(echte Radardaten, kein Screenshot) für die **exakte Hauskoordinate** ausliest und
als Sensor mit **Forecast-Attributen** bereitstellt.

- Datenquelle: `https://opendata.dwd.de/weather/radar/composite/rv/`
  (RADOLAN-Binärformat, DE1200-Gitter 1100×1200, 1 km, Release alle 5 Min,
  Vorhersage 0…+120 Min in 5-Min-Schritten).
- Wert je 5-Min-Member = mm/5min → **mm/h = Wert × 12**.
- Nur **numpy** nötig (in HA vorhanden). Kein GDAL, kein h5py.
- Nur die **Hauszelle** wird ausgewertet; `rv.py:_grid_index` liefert bereits
  `(row, col)`, sodass eine spätere **3×3-Nachbarschaft** trivial ergänzbar ist.

## Entität

`sensor.dwd_nowcast_hausstandort`
- **State:** aktueller Niederschlag (mm/h, Lead 0)
- **Attribute:**
  - `forecast`: Liste (Default 13 Punkte: Jetzt, +10 … +120) mit
    `datetime`, `time`, `minutes`, `precipitation` (mm/h), `unit`, `raw`
    (mm/5min Rohwert), `classification`, `warning`
  - `classification_now`, `max_precipitation`, `next_rain_in_min`
  - Debug: `last_update`, `data_timestamp`, `coordinate`, `grid_cell`,
    `cell_coordinate`, `threshold_entity`, `threshold_value`,
    `threshold_available`, `warning_active`, `warning_text`, `data_real`,
    `all_dry`, `source_file`, `source_product`, `error`

## Klassifizierung (Schwelle live aus Helfer, nicht hartkodiert)

| Klasse | Bedingung (mm/h) |
|---|---|
| trocken | = 0.0 |
| minimal / unsicher | > 0.0 … < 0.2 |
| Regen möglich | ≥ 0.2 … < 1.0 |
| Regen | ≥ 1.0 … < Starkregen-Helfer |
| starker Regen | ≥ Starkregen-Helfer |

Helfer (Default `input_number.regenwarnung`). Fehlt er, wird **kein** Ersatzwert
gesetzt – `threshold_available=false` und `error` weisen darauf hin, und nichts
wird zu „starker Regen" hochgestuft.

## Installation

1. Ordner `dwd_nowcast/` nach `<HA>/config/custom_components/dwd_nowcast/` kopieren.
2. Home Assistant **neu starten**.
3. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „DWD Nowcast"
   → Hauskoordinate + Starkregen-Helfer bestätigen.

## Dashboard-Karte (Markdown)

Wird per MCP auf das Klima-Dashboard gelegt; Vorlage siehe `dashboard_card.md`.
