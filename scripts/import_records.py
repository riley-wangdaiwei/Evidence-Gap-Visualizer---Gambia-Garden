import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.candidate_import import read_candidate_csv,enqueue_candidates
from evidence_gap.database import connect

parser=argparse.ArgumentParser(description="Validate and queue source-linked CSV bundles for human review")
parser.add_argument("--input",required=True)
parser.add_argument("--db",default="data/registry.sqlite")
parser.add_argument("--validate-only",action="store_true")
args=parser.parse_args()
try:
    candidates=read_candidate_csv(args.input)
    if args.validate_only:
        print(f"Valid review candidates: {len(candidates)} (not imported)")
    else:
        ids=enqueue_candidates(connect(args.db),candidates)
        print(f"Queued candidates: {len(ids)}; all remain PENDING_HUMAN_REVIEW")
except Exception as exc:
    print(f"Import rejected: {exc}",file=sys.stderr)
    raise SystemExit(2)
