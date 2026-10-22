import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.database import connect
from evidence_gap.tensor import from_database
db=connect(); tensor=from_database(db)
out={"gap":tensor.project_gap(),"proxy":tensor.project_proxy()}
Path("data/tensor.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(f"Tensor rebuilt deterministically from registry: {len(tensor.records)} alignment records")
