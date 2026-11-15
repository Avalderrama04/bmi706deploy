# BMI706 · Measles Observatory

An interactive measles incidence and vaccination dashboard built with JavaScript/D3 and Python. Includes CSV upload, a global choropleth, country trends with timeline brushing, and WHO regional comparisons.

Run locally:

```sh
cd measles-observatory
python3 server.py
```

Open http://127.0.0.1:8000. The bundled data is synthetic demonstration data, not surveillance estimates.

## Deploy on Render

1. Push this repository, including `render.yaml` and the entire `measles-observatory` folder, to GitHub.
2. In Render select **New → Blueprint**, connect the GitHub repository and select its branch.
3. Render reads `render.yaml` at the repository root. Review and deploy the `measles-observatory` service.
4. When the deployment is live, open the `onrender.com` URL Render provides.

Alternatively, create **New → Web Service** with these settings:

| Setting | Value |
| --- | --- |
| Language | Python 3 |
| Root Directory | `measles-observatory` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4` |
| Health Check Path | `/healthz` |

The hosted Python app serves the JavaScript frontend and an optional CSV validation API. Browser uploads stay local and do not persist on the service. Free web services can sleep when idle.

For a frontend-only deployment, create a Render **Static Site** with Root Directory `measles-observatory`, Build Command `echo "No build required"`, and Publish Directory `dist`. This serves all three visualizations and browser CSV imports; the optional Python API requires the Web Service setup above.

See [the app README](measles-observatory/README.md) for the CSV schema, calculations, tests and data limitations.
