"""Production WSGI entry point for Render. Start with gunicorn app:app."""
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
from server import ROOT, validate_csv

app = Flask(__name__, static_folder=str(ROOT / 'dist'), static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.get('/healthz')
def health():
    return jsonify(status='ok')

@app.post('/api/validate')
def validate():
    try:
        rows = validate_csv(request.get_data().decode('utf-8-sig'))
    except (ValueError, UnicodeError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(rows=rows, count=len(rows))

@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error='CSV must be smaller than 20 MB'), 413
