# BMI706 · Measles Observatory

An interactive dashboard for exploring measles incidence and vaccination coverage by country, year and WHO region. The frontend is JavaScript + D3; Python builds the data, serves the site locally and runs it on Render.

## Run locally

```sh
cd measles-observatory
python3 server.py
```

Open http://127.0.0.1:8000 and press Ctrl+C to stop. No package installation is needed. Do not open `index.html` directly: browsers block the data and map files from loading that way. Use `python3 server.py --port 8001` if port 8000 is busy.

## Explore

- **Global map:** choose measles incidence or vaccination coverage (with an MCV1/MCV2 dose toggle); scrub or play years; zoom and pan; filter by income group, Gavi eligibility and development status. Hover or keyboard-focus a country for its values, and click or press Enter to open its trends.
- **Trends per country:** choose a country to see separate coverage and incidence panels. Brush the lower timeline to focus on a period; the stat cards show the last year of the selection (or the latest year when nothing is selected).
- **Regional comparison:** pick any combination of Global and the six WHO regions (one chart each) and a start/end year. Trajectory charts show MCV1 (left axis, %) and incidence (right axis, per million). The stat cards and the vaccination (%) and incidence (cases per 100,000) bar charts use the end year.

## Data

The dashboard loads two files built from the WHO source files in the `data` folder next to this repository (`../data`):

```sh
cd measles-observatory
python3 build_who_data.py                 # reads ../../data by default
python3 build_who_data.py --data-dir PATH # or point it elsewhere
```

| Dashboard field | WHO source |
| --- | --- |
| incidence | `who_measles_incidence_rate.csv`, country rows (cases per million total population) |
| mcv1, mcv2 | `who_measles_coverage_mcv.csv`, WUENIC estimates only (ADMIN and OFFICIAL rows are ignored) |
| country, region, income_group, development_status, gavi_eligible | `who_countries_income.csv` ("High income: OECD/nonOECD" → "High income") |
| cases, population | Not available in the WHO files; left blank |
| `dist/who_measles_official.csv` | WHO's published global and regional incidence, from the same incidence file |

Rerun the script whenever the WHO files are updated, then commit the regenerated `dist/who_measles.csv` and `dist/who_measles_official.csv`. The outbreak and campaign (SIA) files are not used yet.

### How summaries are calculated

- **Incidence:** with no income, Gavi or development filter applied, global and single-region values are WHO's official estimates. Otherwise (filters applied, or several regions combined) the value is the median reporting country.
- **Coverage:** WHO publishes no regional coverage in these files, so summaries are the median reporting country.
- If a dataset includes population, coverage and incidence summaries are population weighted when every contributing row has population. The WHO data has none, so this does not apply today.

Medians resist single-country outbreaks but are not official estimates. Because there are no case counts, the "Reported cases" indicator and stat are hidden. Classifications are current values applied to every year. Missing values stay blank (grey on the map) and break chart lines; MCV2 before its introduction is missing, not zero. No causal interpretation should be drawn from aligned charts.

### CSV schema

`dist/who_measles.csv` has one row per ISO3 country/year; the optional Python validator uses the same schema. Column names are case-sensitive.

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

At least one of incidence, cases, mcv1 or mcv2 is required. Zero is a valid observation. Incidence is derived from cases/population only when incidence is blank. Duplicate country-years, non-finite numbers, invalid coverage and invalid region codes are rejected.

## Python tools and tests

Run these from `measles-observatory`:

```sh
python3 -m unittest discover -s tests -v                 # data and validator tests
node tests/test_frontend.cjs                             # frontend calculation tests
python3 server.py --validate path/to/data.csv > out.json # validate and normalize a CSV
curl -X POST --data-binary @path/to/data.csv http://127.0.0.1:8000/api/validate
```

The validation API is optional; the dashboard does not use it.

## Deploy on Render

1. Push this repository, including `render.yaml` and the whole `measles-observatory` folder, to GitHub.
2. In Render select **New → Blueprint**, connect the repository and choose its branch.
3. Render reads `render.yaml`. Review and deploy the `measles-observatory` service.
4. When it is live, open the `onrender.com` URL Render provides.

Alternatively, create **New → Web Service** with these settings:

| Setting | Value |
| --- | --- |
| Language | Python 3 |
| Root Directory | `measles-observatory` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4` |
| Health Check Path | `/healthz` |

The production entry point is `app.py` (Flask); `server.py` is the dependency-free local server. Free web services can sleep when idle.

For a frontend-only deployment, create a Render **Static Site** with Root Directory `measles-observatory`, Build Command `echo "No build required"` and Publish Directory `dist`. This serves the full dashboard; only the optional validation API needs the Web Service.

## Credits

Data: World Health Organization (measles incidence; WHO/UNICEF Estimates of National Immunization Coverage). Map: [geo-countries](https://github.com/datasets/geo-countries) (Natural Earth, public domain), simplified for display; boundaries and names do not imply endorsement. D3 v7 is vendored under its ISC license (`dist/assets/D3-LICENSE.txt`). Google Fonts are optional; local sans-serif fallbacks work offline.
