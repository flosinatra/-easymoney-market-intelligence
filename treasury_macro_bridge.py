"""Safely transfer verified Treasury daily rates into the five-factor evidence input.
Does not claim a 1–5 Rates score or substitute nominal rates for real yields.
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from treasury_yields import workbook_yields

def merge(treasury, existing=None, as_of=None):
    existing=existing or {}
    as_of=as_of or datetime.now(timezone.utc)
    out={k:list(v) for k,v in existing.items() if isinstance(v,list)}
    try:
        observation=date.fromisoformat(treasury["observation_date"])
        retrieval=datetime.fromisoformat(treasury["retrieved_at_utc"].replace("Z","+00:00"))
        url=treasury["source_url"]
        if not url.startswith("https://home.treasury.gov/") or retrieval.tzinfo is None or retrieval>as_of or observation>as_of.date():
            return out
        if (as_of.date()-observation).days>4:
            return out
        yields=workbook_yields(treasury["yields_percent"])
        entries=[]
        for term in ("2-year","5-year","10-year","30-year"):
            val=yields.get(term)
            if type(val) not in (int,float) or not 0<=val<=30: continue
            entries.append({"indicator":"US Treasury "+term+" nominal yield","value":val,"unit":"percent",
                            "observation_date":observation.isoformat(),
                            "published_date":None,
                            "source":"US Treasury","source_url":url,
                            "publication_date_verified":False,
                            "retrieval_date":retrieval.date().isoformat(),
                            "note":"Publication date unverified; retrieval date is not substituted as publication date."})
        if entries:
            # Replace only the automatically generated Treasury rows, preserve other evidence.
            preserved=[x for x in out.get("Rates",[]) if not (isinstance(x,dict) and x.get("source")=="US Treasury" and x.get("indicator","").startswith("US Treasury "))]
            out["Rates"]=preserved+entries
    except (ValueError,KeyError,TypeError,AttributeError):
        pass
    return out

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--treasury",default="docs/treasury.json")
    ap.add_argument("--input",default="docs/macro_observations.json")
    a=ap.parse_args()
    try: treasury=json.loads(Path(a.treasury).read_text())
    except (OSError,ValueError):treasury={}
    try: existing=json.loads(Path(a.input).read_text())
    except (OSError,ValueError):existing={}
    output=merge(treasury,existing)
    Path(a.input).write_text(json.dumps(output,indent=2)+"\n")
    print("Treasury evidence bridged:",len(output.get("Rates",[])))
