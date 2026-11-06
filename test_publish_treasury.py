import unittest
from datetime import datetime,timezone
from publish_treasury import build_snapshot

ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"><entry><content><m:properties><d:NEW_DATE>2026-11-04T00:00:00</d:NEW_DATE><d:BC_2YEAR>3.50</d:BC_2YEAR><d:BC_10YEAR>4.20</d:BC_10YEAR></m:properties></content></entry></feed>'''
class TestPublish(unittest.TestCase):
 def test_snapshot_retains_dates_and_safety_flags(self):
  s=build_snapshot(ATOM,'https://home.treasury.gov/example',datetime(2026,11,5,tzinfo=timezone.utc))
  self.assertEqual(s['observation_date'],'2026-11-04')
  self.assertEqual(s['yields_percent']['10y'],4.2)
  self.assertFalse(s['research_ready'])
  self.assertFalse(s['live_intraday_market_data_verified'])
 def test_invalid_xml_rejected(self):
  with self.assertRaises(ValueError):build_snapshot(b'<feed/>','https://home.treasury.gov/example')
if __name__=='__main__':unittest.main()
