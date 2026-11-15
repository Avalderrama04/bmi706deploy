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
    def test_demo_is_valid(self):
        path=Path(__file__).resolve().parents[1]/'dist/demo.csv'
        rows=validate_csv(path.read_text())
        self.assertGreater(len(rows),3000)
        self.assertTrue(all(r['year']>=1980 for r in rows))
    def test_requires_observations(self):
        with self.assertRaises(ValueError):
            validate_csv('country,iso3,year,mcv1\nIndia,IND,2025,\n')
    def test_quoted_country(self):
        self.assertEqual(validate_csv('country,iso3,year,cases\n"Example, Country",IND,2025,0\n')[0]['country'],'Example, Country')

if __name__=='__main__': unittest.main()
