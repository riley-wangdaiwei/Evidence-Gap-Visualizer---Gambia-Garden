import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evidence_gap.adapters.csv_excel import TabularAdapter
from evidence_gap.database import connect,insert_model
from evidence_gap.normalization import source_from_candidate
ap=argparse.ArgumentParser(); ap.add_argument("input"); args=ap.parse_args(); db=connect()
for c in TabularAdapter().read(args.input): insert_model(db,"sources",source_from_candidate(c))
db.commit(); print("Imported source candidates to registry; review before analysis.")
