{% set e = 'sensor.dwd_nowcast_hausstandort' %}
{% set fc = state_attr(e,'forecast') or [] %}
{% set err = state_attr(e,'error') %}
{% if err %}> ⚠️ **{{ err }}**
{% endif %}
| Zeit | Min | Niederschlag | Klassifizierung | Rohwert | Hinweis |
|:--|--:|--:|:--|--:|:--|
{% for r in fc -%}
| {{ 'Jetzt' if r.minutes == 0 else r.time }} | +{{ r.minutes }} | {{ '%.1f mm/h'|format(r.precipitation) if r.precipitation is not none else '–' }} | {{ r.classification }} | {{ r.raw if r.raw is not none else '–' }} | {{ r.warning }} |
{% endfor %}

<small>Datensatz: {{ state_attr(e,'data_timestamp') }} · Abruf: {{ state_attr(e,'last_update') }}<br>
Zelle {{ state_attr(e,'grid_cell') }} @ {{ state_attr(e,'cell_coordinate') }} · Koordinate {{ state_attr(e,'coordinate') }}<br>
Schwelle „starker Regen": {{ state_attr(e,'threshold_value') }} mm/h ({{ state_attr(e,'threshold_entity') }}, verfügbar: {{ state_attr(e,'threshold_available') }})<br>
Quelle: {{ state_attr(e,'source_product') }} ({{ state_attr(e,'source_file') }}) · echte Daten: {{ state_attr(e,'data_real') }} · alles trocken: {{ state_attr(e,'all_dry') }}</small>
