import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.candidate_import import read_candidate_csv,enqueue_candidates
from evidence_gap.database import connect
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--import-valid",action="store_true"); args=ap.parse_args()
    try: candidates=read_candidate_csv(args.input)
    except Exception as e: print(f"Could not read input: {e}"); return 2
    if not candidates: print("No source-linked review bundles found."); return 1
    print(f"Valid candidate bundles: {len(candidates)}")
    if args.import_valid:
        ids=enqueue_candidates(connect(),candidates)
        print(f"Queued {len(ids)} candidate bundles as PENDING_HUMAN_REVIEW; nothing promoted to formal records.")
    return 0
if __name__=="__main__": raise SystemExit(main())
