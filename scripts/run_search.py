import argparse,sys
from pathlib import Path
import yaml
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.search import search
from evidence_gap.database import connect
from evidence_gap.provenance import stable_id,now_iso
ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/project.yaml"); ap.add_argument("--query"); ap.add_argument("--provider",choices=["crossref","openalex"],default="crossref"); ap.add_argument("--limit",type=int,default=10); args=ap.parse_args()
project=yaml.safe_load(Path(args.config).read_text(encoding="utf-8")); args.query=args.query or project["target_question"]
try: records=search(args.provider,args.query,args.limit)
except Exception as e: print(f"Search failed: {e}"); raise SystemExit(2)
db=connect()
run_id=stable_id("search",args.provider,args.query,now_iso())
db.execute("INSERT INTO search_runs VALUES(?,?,?,?,?,?,?)",(run_id,args.provider,args.query,now_iso(),"complete",len(records),"Explicit metadata discovery; results remain candidates"))
for r in records:
    db.execute("INSERT OR IGNORE INTO search_candidates(id,search_run_id,title,url,doi,source_type,metadata_json,review_status) VALUES(?,?,?,?,?,?,?,?)",(r.id,run_id,r.title,r.url,r.doi,r.source_type,json.dumps(r.metadata,default=str),"PENDING_HUMAN_REVIEW"))
db.commit(); print(f"{len(records)} metadata candidates saved to PENDING_HUMAN_REVIEW; none promoted to sources.")
