"""Evidence assembler for original five-factor Weekly Regime gate.

Only accepts dated, attributed observations. Does not infer 1-5 scores.
"""
from datetime import date, datetime, timezone
import json
from pathlib import Path

FACTORS=("Growth","Inflation","Rates","Credit","Liquidity")
def assemble(observations, as_of=None, max_age_days=45):
    as_of=as_of or datetime.now(timezone.utc).date()
    if isinstance(as_of,datetime): as_of=as_of.date()
    result={"as_of":as_of.isoformat(),"gate":"Weekly Regime",
            "status":"EVIDENCE_INCOMPLETE","factors":{},"scores":None,
            "regime_score":None,"method":"Preserve workbook 1–5 scores and five-factor mean"}
    for factor in FACTORS:
        valid=[];rejected=[]
        for item in observations.get(factor,[]):
            if not isinstance(item,dict):
                rejected.append("invalid_record");continue
            try:
                day=date.fromisoformat(item["observation_date"])
                published=date.fromisoformat(item["published_date"])
                if item.get("publication_date_verified") is False:
                    rejected.append("publication_date_unverified");continue
                source=item["source"].strip()
                name=item["indicator"].strip()
                value=item["value"]
                if not source or not name or type(value) not in (int,float,str) or value=="":
                    raise ValueError()
                if published>as_of or day>as_of or published<day:
                    raise ValueError()
                if (as_of-published).days>max_age_days:
                    rejected.append("stale");continue
                valid.append({"indicator":name,"value":value,
                              "unit":item.get("unit"),"observation_date":day.isoformat(),
                              "published_date":published.isoformat(),"source":source,
                              "source_url":item.get("source_url"),
                              "expectation":item.get("expectation"),
                              "previous":item.get("previous")})
            except (KeyError,TypeError,ValueError,AttributeError):
                rejected.append("invalid_or_future_dated")
        result["factors"][factor]={"status":"EVIDENCE_AVAILABLE_NOT_SCORED" if valid else "MISSING_VERIFIED_EVIDENCE",
                                   "observations":valid,"rejected":rejected,"score_1_to_5":None}
    if all(result["factors"][f]["observations"] for f in FACTORS):
        result["status"]="EVIDENCE_PRESENT_AWAITING_WORKBOOK_SCORING"
    return result

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="docs/macro_observations.json")
    ap.add_argument("--out",default="docs/macro_factor_evidence.json")
    args=ap.parse_args()
    try: data=json.loads(Path(args.input).read_text())
    except (OSError,ValueError):data={}
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    result=assemble(data)
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"])
