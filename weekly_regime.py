"""Weekly Regime: preserve the existing five 1–5 scores and arithmetic mean.
This module does not invent score thresholds, market regime labels or macro evidence.
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path

FACTORS = ("Growth", "Inflation", "Rates", "Credit", "Liquidity")
FIELDS = ("Week of Date", "Growth 1-5", "Inflation 1-5", "Rates 1-5",
          "Credit 1-5", "Liquidity 1-5", "Growth Evidence", "Inflation Evidence",
          "Rates Evidence", "Credit Evidence", "Liquidity Evidence",
          "Regime Score", "Regime", "Lead Driver", "Failure #1", "Failure #2", "Notes")

def assess(record):
    """A weekly record is an explicitly supplied, source-supported set of judgments."""
    result = {"gate": "Weekly Regime", "gate_result": "NOT_ASSESSED",
              "factor_scores": {}, "factor_evidence": {}, "regime_score": None,
              "regime": None, "lead_driver": None, "failures": [],
              "notes": None, "missing": [], "invalid": [], "week_of": record.get("Week of Date"),
              "method": "Arithmetic mean of five existing 1–5 broad-risk-support scores"}
    try:
        week = date.fromisoformat(record["Week of Date"])
        if week.weekday() != 0:
            result["invalid"].append("Week of Date must be a Monday")
    except (KeyError, TypeError, ValueError):
        result["invalid"].append("Week of Date must be an ISO date")
    for factor in FACTORS:
        key = factor + " 1-5"
        score = record.get(key)
        evidence = record.get(factor + " Evidence")
        if type(score) is not int or not 1 <= score <= 5:
            result["missing" if score is None else "invalid"].append(key)
        elif not isinstance(evidence, dict) or not isinstance(evidence.get("summary"), str) or not evidence["summary"].strip() or not isinstance(evidence.get("source"), str) or not evidence["source"].strip() or not isinstance(evidence.get("published_date"), str):
            result["missing"].append(factor + " Evidence (summary/source/published_date)")
        else:
            try:
                published = date.fromisoformat(evidence["published_date"])
                if published > date.today():
                    raise ValueError()
            except ValueError:
                result["invalid"].append(factor + " Evidence published_date")
                continue
            result["factor_scores"][factor] = score
            result["factor_evidence"][factor] = evidence
    if len(result["factor_scores"]) == 5 and not result["invalid"]:
        result["regime_score"] = round(sum(result["factor_scores"].values()) / 5, 2)
        result["gate_result"] = "SCORED_AWAITING_REGIME_INTERPRETATION"
    for name, outkey in (("Regime", "regime"), ("Lead Driver", "lead_driver"), ("Notes", "notes")):
        if isinstance(record.get(name), str) and record[name].strip():
            result[outkey] = record[name].strip()
    result["failures"] = [record[k].strip() for k in ("Failure #1", "Failure #2")
                          if isinstance(record.get(k), str) and record[k].strip()]
    if result["gate_result"] == "SCORED_AWAITING_REGIME_INTERPRETATION" and result["regime"] and result["lead_driver"] and len(result["failures"]) == 2:
        result["gate_result"] = "DOCUMENTED_RESEARCH_ONLY"
    return result

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--input", default="docs/weekly_regime_input.json")
    p.add_argument("--out", default="docs/weekly_regime_assessment.json")
    args=p.parse_args()
    try: record=json.loads(Path(args.input).read_text())
    except (OSError, ValueError): record={}
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    report=assess(record)
    output.write_text(json.dumps(report,indent=2)+"\\n")
    print(report["gate_result"])
