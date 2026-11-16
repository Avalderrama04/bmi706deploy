"""Build dist/who_measles.csv (the dashboard's dataset) from the WHO source files.

Inputs (default: ../../data, i.e. the `data` folder next to the repository):
  who_measles_incidence_rate.csv  -> incidence (cases per million, COUNTRIES rows only)
  who_measles_coverage_mcv.csv    -> mcv1 / mcv2 (WUENIC estimates only)
  who_countries_income.csv        -> country name, WHO region, income group,
                                     development status, Gavi eligibility

Also writes dist/who_measles_official.csv: WHO's published global and regional
incidence, which the dashboard uses for unfiltered summaries.

WHO files do not include case counts or population, so those columns stay blank.
Classifications are current values and are applied to every year.

Usage: python3 build_who_data.py [--data-dir PATH]
"""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ['country', 'iso3', 'year', 'population', 'cases', 'incidence', 'mcv1', 'mcv2',
          'region', 'income_group', 'development_status', 'gavi_eligible']
REGIONS = {'AFRO', 'AMRO', 'EMRO', 'EURO', 'SEARO', 'WPRO'}
INCOME = {'High income: OECD': 'High income', 'High income: nonOECD': 'High income',
          'Upper middle income': 'Upper middle income', 'Lower middle income': 'Lower middle income',
          'Low income': 'Low income'}


def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def number(value):
    value = (value or '').strip()
    return '' if value == '' else f'{float(value):g}'


def build(data_dir):
    countries = {r['CODE']: r for r in read(data_dir / 'who_countries_income.csv')}
    obs = {}
    names = {}

    def row(iso, year):
        return obs.setdefault((iso, int(year)), {'incidence': '', 'mcv1': '', 'mcv2': ''})

    for r in read(data_dir / 'who_measles_incidence_rate.csv'):
        if r['GROUP'] == 'COUNTRIES' and r['DISEASE'] == 'MEASLES' and r['INCIDENCE_RATE'].strip():
            row(r['CODE'], r['YEAR'])['incidence'] = number(r['INCIDENCE_RATE'])
            names.setdefault(r['CODE'], r['NAME'])
    for r in read(data_dir / 'who_measles_coverage_mcv.csv'):
        if r['COVERAGE_CATEGORY'] == 'WUENIC' and r['ANTIGEN'] in ('MCV1', 'MCV2') and r['COVERAGE'].strip():
            row(r['ISO_3_CODE'], r['YEAR'])[r['ANTIGEN'].lower()] = number(r['COVERAGE'])
            names.setdefault(r['ISO_3_CODE'], r['COUNTRYNAME'])

    out = []
    for (iso, year), values in sorted(obs.items()):
        if len(iso) != 3:
            continue
        c = countries.get(iso, {})
        region = c.get('WHOREGIONC', '')
        gavi = c.get('GRP_GAVICTY', '').strip().lower()
        out.append({
            'country': c.get('NAMEWORKEN') or names.get(iso, iso), 'iso3': iso, 'year': year,
            'population': '', 'cases': '', **values,
            'region': region if region in REGIONS else '',
            'income_group': INCOME.get(c.get('WBINCOMESTATUS', ''), ''),
            'development_status': c.get('DEVELOPMENTSTATUS', ''),
            'gavi_eligible': gavi if gavi in ('true', 'false') else '',
        })
    official = []
    codes = {'AFR': 'AFRO', 'AMR': 'AMRO', 'EMR': 'EMRO', 'EUR': 'EURO', 'SEAR': 'SEARO', 'WPR': 'WPRO', 'GLOBAL': 'GLOBAL'}
    for r in read(data_dir / 'who_measles_incidence_rate.csv'):
        if r['GROUP'] in ('WHO_REGIONS', 'GLOBAL') and r['DISEASE'] == 'MEASLES' and r['CODE'] in codes:
            official.append({'region': codes[r['CODE']], 'year': int(r['YEAR']), 'incidence': number(r['INCIDENCE_RATE'])})
    official.sort(key=lambda r: (r['region'], r['year']))
    return out, official


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data-dir', type=Path, default=ROOT.parent.parent / 'data')
    args = parser.parse_args()
    rows, official = build(args.data_dir)
    with (ROOT / 'dist' / 'who_measles_official.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['region', 'year', 'incidence'])
        w.writeheader()
        w.writerows(official)
    with (ROOT / 'dist' / 'who_measles.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote dist/who_measles.csv: {len(rows)} rows, {len({r['iso3'] for r in rows})} countries, "
          f"{min(r['year'] for r in rows)}-{max(r['year'] for r in rows)}")
