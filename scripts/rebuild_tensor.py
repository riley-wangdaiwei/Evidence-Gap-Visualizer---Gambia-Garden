import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.database import connect
from evidence_gap.batch_loader import load_configured_batch
from evidence_gap.tensor import from_database
db=connect(); batch=load_configured_batch(db); tensor=from_database(db)
out={"gap":tensor.project_gap(),"proxy":tensor.project_proxy()}
Path("data/tensor.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(f"Tensor rebuilt from configured batch {batch['folder']}: {len(tensor.records)} target/population/geography cells, {len(tensor.proxy_records or [])} approved alignments")
