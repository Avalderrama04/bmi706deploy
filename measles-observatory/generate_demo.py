"""Generate reproducible synthetic observations. These are NOT health estimates."""
import csv
import json
import math
import random
from pathlib import Path
ROOT = Path(__file__).resolve().parent
random.seed(706)
groups = {
    'AFRO': 'NGA COD ETH KEN UGA TZA ZAF MDG MOZ AGO ZMB ZWE SEN GHA CMR MLI NER TCD BFA SSD',
    'AMRO': 'USA CAN MEX BRA ARG COL PER VEN CHL BOL ECU GTM CUB HTI',
    'EMRO': 'PAK AFG IRN IRQ SAU YEM SOM SDN EGY MAR TUN',
    'EURO': 'GBR FRA DEU ESP ITA NOR SWE FIN POL UKR RUS TUR KAZ UZB ROU GRC PRT',
    'SEARO': 'IND IDN BGD NPL MMR THA LKA TLS BTN',
    'WPRO': 'CHN JPN AUS NZL PHL VNM MYS KHM LAO MNG PNG KOR',
}
world = json.loads((ROOT / 'dist/assets/world.geojson').read_text())
names = {f['properties']['ISO3166-1-Alpha-3']: f['properties']['name'] for f in world['features']}
fields = ['country','iso3','year','population','cases','incidence','mcv1','mcv2','region','income_group','development_status','gavi_eligible']
rows = []
for region, codes in groups.items():
    for code in codes.split():
        # All demographic values AND classifications below are illustrative.
        scale = random.uniform(1.4, 90) * 1e6
        phase = random.random()*6
        final = random.uniform(65,98)
        high = code in 'USA CAN GBR FRA DEU ESP ITA NOR SWE FIN JPN AUS NZL KOR SAU'.split()
        if high: final = random.uniform(89,98)
        income = 'High income' if high else random.choice(['Low income','Lower middle income','Upper middle income'])
        development = 'Developed economy' if high else random.choice(['Least developed','Developing','Economy in transition'])
        for year in range(1980,2026):
            t = (year-1980)/45
            population = int(scale*(.65+.6*t))
            coverage = min(99,max(12,final-(1-t)**1.5*random.uniform(35,55)+math.sin(year*.45+phase)*2))
            dose2 = None if year < 1998 else max(0,coverage-(14-9*t))
            incidence = max(0, 420*math.exp(-4*t)*(1.15-coverage/120)+(math.sin(year*.7+phase)+1)*12+(65 if year in [2019,2023] and not high else 0))
            if high: incidence *= .09
            cases = round(incidence*population/1e6)
            rows.append([names.get(code,code),code,year,population,cases,round(cases/population*1e6,3),round(coverage,1),round(dose2,1) if dose2 is not None else '',region,income,development,str(income=='Low income').lower()])
with (ROOT/'dist/demo.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(fields);w.writerows(rows)
with (ROOT/'dist/template.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(fields);w.writerows([r for r in rows if r[1] in ['IND','BRA','NGA'] and r[2] in [2023,2024,2025]])
# Retain every fourth boundary vertex for a compact dashboard basemap.
# Skip compaction when rerunning against the already-compacted bundled map.
if (ROOT/'dist/assets/world.geojson').stat().st_size < 5_000_000:
    raise SystemExit(0)
def compact(value):
    if isinstance(value,list):
        if value and isinstance(value[0],list) and value[0] and isinstance(value[0][0],(float,int)):
            points = value[::4] if len(value)>16 else value
            if points[-1]!=points[0]: points=points+[points[0]]
            return [[round(v,3) for v in point] for point in points]
        return [compact(v) for v in value]
    return value
for feature in world['features']:
    feature['geometry']['coordinates']=compact(feature['geometry']['coordinates'])
for feature in world['features']:
    g = feature['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        for i, ring in enumerate(poly):
            area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]))
            if (i == 0 and area > 0) or (i > 0 and area < 0):
                ring.reverse()
(ROOT/'dist/assets/world.geojson').write_text(json.dumps(world,separators=(',',':')))
