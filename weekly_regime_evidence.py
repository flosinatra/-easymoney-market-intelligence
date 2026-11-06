"""Connect collected Treasury observations to Weekly Regime Rates evidence.
This never assigns a 1–5 score: workbook judgment is separate from source facts.
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from treasury_yields import workbook_yields

def build(treasury, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    result={"factor":"Rates","status":"UNVERIFIED","source":"U.S. Treasury daily par yield curve",
            "observation_date":treasury.get("observation_date"),
            "retrieved_at_utc":treasury.get("retrieved_at_utc"),
            "source_url":treasury.get("source_url"),"observations":{},
            "score_1_to_5":None,"scoring_status":"REQUIRES_EXISTING_WORKBOOK_JUDGMENT",
            "limitations":["Nominal daily Treasury yields do not alone determine broad risk supportiveness",
                           "No verified Fed path, real yields, credit, liquidity or policy surprise in this packet"]}
    try:
        observed=date.fromisoformat(treasury["observation_date"])
        retrieved=datetime.fromisoformat(treasury["retrieved_at_utc"].replace("Z","+00:00"))
        if retrieved.tzinfo is None or retrieved>as_of or observed>as_of.date():
            return result
        if (as_of.date()-observed).days>4:
            result["status"]="STALE"
            return result
        yields=workbook_yields(treasury["yields_percent"])
        for key in ("2-year","5-year","10-year","30-year"):
            val=yields.get(key)
            if type(val) in (float,int) and 0<=val<=30:
                result["observations"][key+"_yield_percent"]=val
        if result["observations"]:
            result["status"]="DAILY_NOMINAL_RATE_CONTEXT_ONLY"
    except (ValueError,KeyError,TypeError,AttributeError):
        pass
    return result

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--treasury",default="docs/treasury.json")
    parser.add_argument("--out",default="docs/weekly_regime_rates_evidence.json")
    a=parser.parse_args()
    try: data=json.loads(Path(a.treasury).read_text())
    except (ValueError,OSError): data={}
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(build(data),indent=2)+"\\n")
    print("Rates evidence packet:",build(data)["status"])
