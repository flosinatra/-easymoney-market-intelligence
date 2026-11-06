"""Check whether a local EasyMoney package is structurally ready for GitHub hosting.
This checks packaging, NOT internet access, GitHub authorization or feed freshness.
"""
import json
from pathlib import Path

REQUIRED=("hosted_run.py","pipeline.py","collect_macro_context.py",
          "publish_treasury.py","docs/index.html",
          ".github/workflows/treasury.yml")
def check(root):
    root=Path(root)
    missing=[name for name in REQUIRED if not (root/name).is_file()]
    html=(root/"docs/index.html").read_text() if (root/"docs/index.html").exists() else ""
    workflow=(root/".github/workflows/treasury.yml").read_text() if (root/".github/workflows/treasury.yml").exists() else ""
    checks={
        "required_files_present":not missing,
        "dashboard_uses_collection_receipts":"hosted_collection_receipt.json" in html,
        "scheduled_workflow_defined":"schedule:" in workflow and "workflow_dispatch:" in workflow,
        "hosted_collector_invoked":"python hosted_run.py" in workflow,
        "tests_run_before_collection":("python -m unittest discover -q" in workflow and
            workflow.index("python -m unittest discover -q")<workflow.index("python hosted_run.py")) if
            "python -m unittest discover -q" in workflow and "python hosted_run.py" in workflow else False,
    }
    return {"package_ready":all(checks.values()),"checks":checks,
            "missing_files":missing,"hosted_data_verified":False,"github_deployed":False}
if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    args=parser.parse_args()
    result=check(args.root)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["package_ready"] else 1)
