import tempfile
import unittest
from pathlib import Path
from deployment_preflight import check
ROOT=Path(__file__).resolve().parent
class DeploymentPreflightTests(unittest.TestCase):
    def test_current_package_ready(self):
        result=check(ROOT)
        self.assertTrue(result["package_ready"],result)
        self.assertFalse(result["github_deployed"])
        self.assertFalse(result["hosted_data_verified"])
    def test_missing_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            result=check(d)
            self.assertFalse(result["package_ready"])
            self.assertIn("hosted_run.py",result["missing_files"])
