import unittest
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parent
class DeploymentContractTests(unittest.TestCase):
    def test_workflow_parses(self):
        workflow=yaml.safe_load((ROOT/'.github/workflows/treasury.yml').read_text())
        self.assertIn('jobs',workflow)
    def test_tests_run_before_collection(self):
        text=(ROOT/'.github/workflows/treasury.yml').read_text()
        self.assertLess(text.index('python -m unittest discover -q'),text.index('python hosted_run.py'))
    def test_dashboard_has_collection_receipt(self):
        html=(ROOT/'docs/index.html').read_text()
        self.assertIn('macro_collection_health.json',html)
        self.assertIn('latest scheduled download',html)
