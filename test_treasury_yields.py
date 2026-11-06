import unittest
from datetime import datetime,timezone
from treasury_yields import parse_treasury_csv

NOW=datetime(2026,11,5,15,0,tzinfo=timezone.utc)
HEAD='Date,1 Mo,2 Yr,10 Yr,30 Yr\n'

class TreasuryTests(unittest.TestCase):
    def test_normal_and_sort(self):
        d=parse_treasury_csv(HEAD+'11/04/2026,3.8,3.5,4.1,4.7\n11/03/2026,3.9,3.6,4.2,4.8\n',NOW)
        self.assertEqual(d['latest_observation_date'],'2026-11-04')
        self.assertEqual(d['observations'][-1]['yield_percent']['10y'],4.1)
        self.assertFalse(d['intraday_quote'])
        self.assertFalse(d['source_publication_time_verified'])
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            parse_treasury_csv(HEAD+'11/04/2026,3,3,4,4\n11/04/2026,3,3,4,4\n',NOW)
    def test_future_rejected(self):
        with self.assertRaisesRegex(ValueError,'Future'):
            parse_treasury_csv(HEAD+'11/06/2026,3,3,4,4\n',NOW)
    def test_missing_tenor_is_not_invented(self):
        d=parse_treasury_csv(HEAD+'11/04/2026,3,3,,4\n',NOW)
        self.assertIsNone(d['observations'][0]['yield_percent']['10y'])
    def test_invalid_yield_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid yield'):
            parse_treasury_csv(HEAD+'11/04/2026,3,3,banana,4\n',NOW)
    def test_missing_headers_rejected(self):
        with self.assertRaisesRegex(ValueError,'headers'):
            parse_treasury_csv('Date,Price\n11/04/2026,4\n',NOW)

if __name__=='__main__':unittest.main()
