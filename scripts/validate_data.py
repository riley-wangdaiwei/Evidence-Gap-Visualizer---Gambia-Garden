import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.adapters.csv_excel import TabularAdapter
from evidence_gap.database import connect,insert_model
from evidence_gap.normalization import source_from_candidate
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--import-valid",action="store_true"); args=ap.parse_args()
    try: candidates=TabularAdapter().read(args.input)
    except Exception as e: print(f"Could not read input: {e}"); return 2
    if not candidates: print("No rows with a non-empty title/source_title."); return 1
    print(f"Valid candidate rows: {len(candidates)}")
    if args.import_valid:
        db=connect()
        for c in candidates: insert_model(db,"sources",source_from_candidate(c))
        db.commit(); db.close(); print("Imported valid source rows into data/registry.sqlite")
    return 0
if __name__=="__main__": raise SystemExit(main())
