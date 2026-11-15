# Measles Observatory

A responsive JavaScript + D3 dashboard and a dependency-free Python server for exploring country-year measles and vaccination data.

## Run locally

```sh
cd measles-observatory
python3 server.py
```

Open http://127.0.0.1:8000. No package installation is needed. Do not open index.html directly: browsers restrict local CSV/map loading.

## Explore

- **Global map:** choose incidence, MCV1, MCV2 or cases; scrub or play years; zoom and pan; filter income, Gavi eligibility and development status. Hover or keyboard-focus countries for values, and click or press Enter to see trends.
- **Trends:** choose a country; inspect separate coverage and incidence panels; brush the lower timeline to focus on years. Clear the brush to reset.
- **Regions:** global and six WHO regional dual-axis charts; year range and region selection; grouped vaccination bars and incidence bars for the toolbar year. Left axis: MCV1 percent; right axis: cases per million. Hover chart points/bars for values.
- **Upload:** validated UTF-8 CSV replaces demo observations across every view. Files stay in your browser; reload resets to demo. The template contains synthetic example rows.

## CSV schema

One row per ISO3 country/year. Column names are case-sensitive.

| Column | Meaning |
| --- | --- |
| country | Required country display name |
| iso3 | Required three-letter ISO 3166-1 alpha-3 map identifier |
| year | Required integer, 1900–2100 |
| population | Optional positive population |
| cases | Reported cases, zero or greater |
| incidence | Cases per **million**, zero or greater |
| mcv1 / mcv2 | Coverage percentages, 0–100 |
| region | AFRO, AMRO, EMRO, EURO, SEARO, WPRO, or blank |
| income_group | Low income, Lower middle income, Upper middle income, High income |
| development_status | Least developed, Developing, Economy in transition, Developed economy |
| gavi_eligible | true/false, yes/no, 1/0, or blank |

At least one observation across incidence, cases, mcv1 or mcv2 is required. Missing values remain blank; zero is a valid observation. Incidence is derived from cases/population only when incidence is blank. Duplicate country-years, non-finite numbers, invalid coverage and invalid region codes are rejected. Unmatched map codes still participate in charts and trigger a warning.

Coverage aggregation uses population weighting only if every contributing coverage observation has positive population; otherwise it uses the available-country mean. Incidence aggregation uses summed cases / summed population when every row has population and a reported or derivable case count; otherwise it uses the available incidence values with population weighting when possible. Cases are summed across reporting countries. These are summaries of the uploaded observations, not official regional estimates. Population weighting of vaccine coverage is an approximation; birth-cohort denominators would be preferable for official estimates. Lines break across missing years; MCV2 before introduction is missing, not zero. Classifications are read per row, so they can change over time.

## Python processing

The browser handles CSV imports so the deployed static app works independently of a Python runtime. Python supplies the local web server, an optional validation API, and offline normalization:

```sh
python3 server.py --validate path/to/data.csv > normalized.json
curl -X POST --data-binary @path/to/data.csv http://127.0.0.1:8000/api/validate
python3 -m unittest discover -s tests -v
```

The local API is optional; the UI does not send files to it. The static deployment includes only `dist/`. No user data is persisted.

## Sources and limitations

The included 1980–2025 data, demographic values and country classifications are **synthetic**, generated for UI demonstration, and are not suitable for health inference. Replace with your own cleaned surveillance and coverage dataset. No causal interpretation should be drawn from aligned charts.

Map source: https://github.com/datasets/geo-countries (Natural Earth, public domain), compacted for dashboard display. Geographic boundaries and naming do not imply endorsement. D3 v7 is vendored under its ISC license; see `dist/assets/D3-LICENSE.txt`. Google Fonts are optional; local sans-serif fallbacks work offline.

## Render deployment

The repository root includes `render.yaml` for a Python Web Service. Push the complete repository to GitHub, then choose **New → Blueprint** in Render and connect it. Render uses `measles-observatory` as its root directory, installs `requirements.txt`, and runs `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4`. The production Flask entry point is `app.py`; `server.py` remains the dependency-free local development server. `/healthz` is the health check endpoint. See the repository root README for manual Web Service and Static Site settings.
