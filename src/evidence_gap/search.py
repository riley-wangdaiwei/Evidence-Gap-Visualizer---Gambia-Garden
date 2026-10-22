"""Explicit metadata search; network access is opt-in at the CLI."""
from datetime import datetime, timezone
import json
import urllib.parse
import urllib.request
import time
from .adapters.crossref import parse_crossref
from .adapters.openalex import parse_openalex
from .deduplication import deduplicate
def search(provider, query, limit=10):
    time.sleep(1)
    if provider=="crossref":
        url="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":query,"rows":limit})
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"GambiaEvidenceGapExplorer/0.1"}),timeout=20) as r: data=json.load(r)
        items=[parse_crossref(x) for x in data.get("message",{}).get("items",[])]
    elif provider=="openalex":
        url="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":query,"per-page":limit})
        with urllib.request.urlopen(url,timeout=20) as r: data=json.load(r)
        items=[parse_openalex(x) for x in data.get("results",[])]
    else: raise ValueError(f"Unsupported provider: {provider}")
    return deduplicate(items)
def search_record(provider,query,status,count): return {"provider":provider,"query":query,"started_at":datetime.now(timezone.utc).isoformat(),"status":status,"result_count":count}
