"""Load repository-provided batch files as review candidates only."""
from pathlib import Path
from .candidate_import import read_candidate_csv, enqueue_candidates

def load_configured_batch(db, project_file="config/project.yaml"):
    import yaml
    config=yaml.safe_load(Path(project_file).read_text(encoding="utf-8")) or {}
    folder=Path(config.get("default_batch_dir","data/youth"))
    if not folder.is_dir(): return {"folder":str(folder),"files":0,"queued":0}
    files=sorted(folder.glob("*.csv"))
    count=0
    for path in files:
        count+=len(enqueue_candidates(db,read_candidate_csv(path)))
    return {"folder":str(folder),"files":len(files),"queued":count}
