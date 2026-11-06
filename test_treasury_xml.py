import unittest
from datetime import datetime,timezone
from treasury_xml import official_url,parse_xml
SAMPLE=b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"><entry><content><m:properties><d:NEW_DATE>2026-11-02T00:00:00</d:NEW_DATE><d:BC_2YEAR>4.59</d:BC_2YEAR><d:BC_10YEAR>4.91</d:BC_10YEAR></m:properties></content></entry></feed>'''
class Tests(unittest.TestCase):
 def test_url(self): self.assertIn('202611',official_url('202611'))
 def test_bad_month(self):
  with self.assertRaises(ValueError):official_url('202613')
 def test_parse(self):
  p=parse_xml(SAMPLE,datetime(2026,11,5,tzinfo=timezone.utc))
  self.assertEqual(p['observations'][0]['yield_percent']['10y'],4.91)
  self.assertFalse(p['intraday_quote'])
 def test_future(self):
  with self.assertRaises(ValueError):parse_xml(SAMPLE,datetime(2026,11,1,tzinfo=timezone.utc))
 def test_empty(self):
  with self.assertRaises(ValueError):parse_xml(b'<feed/>')
if __name__=='__main__':unittest.main()
