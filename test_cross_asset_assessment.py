import unittest
from datetime import datetime,timezone
from cross_asset_assessment import assess
NOW=datetime(2026,11,5,23,tzinfo=timezone.utc)
BASE={'observation_date':'2026-11-05','retrieved_at_utc':'2026-11-05T22:00:00+00:00','yields_percent':{'10-year':4.5,'2-year':4.3,'3-month':4.0}}
class CrossAssetTest(unittest.TestCase):
 def test_spreads_not_gate(self):
  r=assess(BASE,NOW);self.assertEqual(r['curve_spreads_basis_points']['10Y minus 2Y'],20.0);self.assertEqual(r['gate_result'],'NOT_ASSESSED')
 def test_collector_tenors_match_workbook_terms(self):
  d=dict(BASE,yields_percent={'10y':4.5,'2y':4.3,'3m':4.0})
  self.assertEqual(assess(d,NOW)['curve_spreads_basis_points'], assess(BASE,NOW)['curve_spreads_basis_points'])
 def test_stale(self):
  d=dict(BASE,observation_date='2026-10-01');self.assertEqual(assess(d,NOW)['evidence_status'],'STALE_DAILY_OBSERVATION')
 def test_future(self):
  d=dict(BASE,retrieved_at_utc='2026-11-06T22:00:00+00:00');self.assertEqual(assess(d,NOW)['evidence_status'],'UNVERIFIED')
 def test_missing(self):
  self.assertEqual(assess({},NOW)['evidence_status'],'UNVERIFIED')
 def test_no_negative_yields_assumed(self):
  d=dict(BASE,yields_percent={'10-year':-1,'2-year':4});self.assertEqual(assess(d,NOW)['evidence_status'],'INSUFFICIENT_DAILY_DATA')
if __name__=='__main__':unittest.main()
