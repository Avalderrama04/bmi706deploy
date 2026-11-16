import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import validate_csv

class DataTests(unittest.TestCase):
    def test_derives_incidence_and_preserves_missing_and_zero(self):
        rows=validate_csv('country,iso3,year,population,cases,mcv1,mcv2\nIndia,IND,2025,10000000,20,0,\n')
        self.assertEqual(rows[0]['incidence'],2)
        self.assertEqual(rows[0]['mcv1'],0)
        self.assertIsNone(rows[0]['mcv2'])
    def test_rejects_duplicate_country_year(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            validate_csv('country,iso3,year,mcv1\nIndia,IND,2025,80\nIndia,IND,2025,90\n')
    def test_rejects_invalid_values(self):
        for value in ['101','-1','NaN','Infinity','abc']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_csv(f'country,iso3,year,mcv1\nIndia,IND,2025,{value}\n')
    def test_who_dataset_is_valid(self):
        path=Path(__file__).resolve().parents[1]/'dist/who_measles.csv'
        rows=validate_csv(path.read_text())
        self.assertGreater(len(rows),5000)
        self.assertGreater(len({r['iso3'] for r in rows}),150)
        nga=next(r for r in rows if r['iso3']=='NGA' and r['year']==2023)
        self.assertEqual((nga['incidence'],nga['mcv1'],nga['mcv2']),(88.4,54,33))
    def test_official_aggregates_present(self):
        import csv
        path=Path(__file__).resolve().parents[1]/'dist/who_measles_official.csv'
        rows=list(csv.DictReader(path.open()))
        self.assertEqual({r['region'] for r in rows},{'GLOBAL','AFRO','AMRO','EMRO','EURO','SEARO','WPRO'})
        self.assertTrue(all(r['incidence'] for r in rows))
    def test_requires_observations(self):
        with self.assertRaises(ValueError):
            validate_csv('country,iso3,year,mcv1\nIndia,IND,2025,\n')
    def test_quoted_country(self):
        self.assertEqual(validate_csv('country,iso3,year,cases\n"Example, Country",IND,2025,0\n')[0]['country'],'Example, Country')

if __name__=='__main__': unittest.main()
