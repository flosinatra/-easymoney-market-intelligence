import unittest
import os, json
from unittest.mock import patch
from collect_desk import collect, fred_calendar
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
class ConfigurationTests(unittest.TestCase):
 def test_missing_key_is_explicit_and_no_series_network_calls(self):
  with patch.dict(os.environ,{'REQUIRE_FRED_API_KEY':'true'},clear=True),patch('collect_desk.read',side_effect=OSError('offline')) as read:
   r=collect();self.assertEqual(len(r['series']),0);self.assertEqual(r['errors']['PAYEMS'],'FRED_API_KEY_MISSING');self.assertEqual(read.call_count,1)
 def test_calendar_fallback_does_not_invent_time(self):
  from datetime import datetime,timezone
  body=json.dumps({'count':1,'release_dates':[{'date':'2026-11-10','release_name':'Consumer Price Index'}]})
  with patch.dict(os.environ,{'FRED_API_KEY':'test-value'}),patch('collect_desk.read',return_value=body):
   r=fred_calendar(datetime(2026,11,6,tzinfo=timezone.utc));self.assertIsNone(r['events'][0]['time']);self.assertFalse(r['times_verified'])
 def test_api_failure_never_leaks_key(self):
  with patch.dict(os.environ,{'FRED_API_KEY':'secret-test-value'}),patch('collect_desk.read',side_effect=OSError('secret-test-value')):
   self.assertNotIn('secret-test-value',json.dumps(collect()))
if __name__=='__main__':unittest.main()
