import unittest
from collect_desk import parse_csv,parse_calendar
class DeskTests(unittest.TestCase):
 def test_reject_bad_schema(self):
  with self.assertRaises(ValueError):parse_csv('date,value\n2026-11-01,2','X','2026-11-06')
 def test_missing_nonfinite_future_and_duplicates(self):
  raw='observation_date,X\n2026-11-01,1\n2026-11-01,2\n2026-11-02,.\n2026-11-03,nan\n2026-11-04,inf\n2026-11-08,4'
  self.assertEqual(parse_csv(raw,'X','2026-11-06'),[['2026-11-01',2.]])
 def test_calendar_fold_and_timezone(self):
  s='BEGIN:VEVENT\nDTSTART;TZID=US-Eastern:20261110T083000\nSUMMARY:Consumer Price \n Index\nEND:VEVENT'
  self.assertEqual(parse_calendar(s)[0],dict(day='2026-11-10',time='08:30',name='Consumer Price Index'))
 def test_empty_calendar(self):
  with self.assertRaises(ValueError):parse_calendar('Unavailable')
if __name__=='__main__':unittest.main()
