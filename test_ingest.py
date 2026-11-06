import unittest
from easymoney_macro_ingest import parse_observations

class ParseTests(unittest.TestCase):
    def test_missing_values_are_not_zero(self):
        result = parse_observations({'observations': [
            {'date':'2026-01-01','value':'.','realtime_start':'2026-01-02'},
            {'date':'2026-02-01','value':'2.5','realtime_start':'2026-02-02'}]})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], 2.5)
        self.assertEqual(result[0]['observation_date'], '2026-02-01')
    def test_invalid_response_rejected(self):
        with self.assertRaises(ValueError):
            parse_observations({'error_message':'invalid key'})

if __name__ == '__main__': unittest.main()
