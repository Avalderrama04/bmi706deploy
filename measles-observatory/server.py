"""Local dashboard server and CSV validation. Uses only Python's standard library."""
import argparse
import csv
import io
import json
import math
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MEASURES = ('incidence', 'cases', 'mcv1', 'mcv2')

def validate_csv(text):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    columns = reader.fieldnames or []
    if not {'country', 'iso3', 'year'}.issubset(columns):
        raise ValueError('Required columns: country, iso3, year')
    if not any(k in columns for k in MEASURES):
        raise ValueError('Include incidence, cases, mcv1 or mcv2')
    result, seen = [], set()
    for line, raw in enumerate(reader, 2):
        row = {k: (v or '').strip() for k, v in raw.items() if k is not None}
        iso = row['iso3'].upper()
        if not row['country'] or len(iso) != 3 or not iso.isascii() or not iso.isalpha():
            raise ValueError(f'Row {line}: country and three-letter ISO3 code are required')
        row['iso3'] = iso
        for k in ('year', 'population', *MEASURES):
            value = row.get(k, '')
            try:
                row[k] = float(value) if value else None
            except ValueError:
                raise ValueError(f'Row {line}: {k} must be numeric or blank') from None
            if row[k] is not None and not math.isfinite(row[k]):
                raise ValueError(f'Row {line}: {k} must be finite')
        if row['year'] is None or not row['year'].is_integer() or not 1900 <= row['year'] <= 2100:
            raise ValueError(f'Row {line}: year must be an integer from 1900 to 2100')
        row['year'] = int(row['year'])
        for k in ('population', *MEASURES):
            v = row[k]
            if v is not None and (v < 0 or (k in ('mcv1', 'mcv2') and v > 100) or (k == 'population' and v == 0)):
                raise ValueError(f'Row {line}: invalid {k}')
        key = (iso, row['year'])
        if key in seen:
            raise ValueError(f'Row {line}: duplicate country/year')
        seen.add(key)
        flag = row.get('gavi_eligible', '').lower()
        if flag not in ('', 'true', 'false', '1', '0', 'yes', 'no'):
            raise ValueError(f'Row {line}: invalid gavi_eligible')
        row['gavi_eligible'] = flag in ('true', '1', 'yes')
        if row.get('region', '') not in ('', 'AFRO', 'AMRO', 'EMRO', 'EURO', 'SEARO', 'WPRO'):
            raise ValueError(f'Row {line}: invalid WHO region code')
        if row['incidence'] is None and row['cases'] is not None and row['population']:
            row['incidence'] = row['cases'] / row['population'] * 1_000_000
        result.append(row)
    if not result or not any(r[k] is not None for r in result for k in MEASURES):
        raise ValueError('Dataset contains no numeric observations')
    return result

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Make the browser re-check files on every load so edits show up without a hard refresh.
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_POST(self):
        if self.path != '/api/validate':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 20 * 1024 * 1024:
                raise ValueError('CSV must be between 1 byte and 20 MB')
            rows = validate_csv(self.rfile.read(length).decode('utf-8-sig'))
            payload, status = {'rows': rows, 'count': len(rows)}, 200
        except (ValueError, UnicodeError) as exc:
            payload, status = {'error': str(exc)}, 400
        body = json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--validate', type=Path, help='Validate a CSV and print normalized JSON, without starting the server')
    args = parser.parse_args()
    if args.validate:
        try:
            print(json.dumps(validate_csv(args.validate.read_text(encoding='utf-8-sig')), indent=2, allow_nan=False))
        except ValueError as exc:
            parser.exit(1, f'{exc}\n')
    else:
        print(f'Measles Observatory: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT / 'dist'))).serve_forever()
