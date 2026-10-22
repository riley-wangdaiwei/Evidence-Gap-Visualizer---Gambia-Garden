"""Canonical local registry and candidate-review workflow."""
import json
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,title TEXT NOT NULL,source_type TEXT,url TEXT,doi TEXT,producer TEXT,collected_by TEXT,access_status TEXT,synthetic INTEGER NOT NULL DEFAULT 0,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',retrieved_at TEXT,publication_year INTEGER,underlying_data_id TEXT);
CREATE TABLE IF NOT EXISTS data_products(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),name TEXT,product_type TEXT,geography_level TEXT,population TEXT,observation_period TEXT,synthetic INTEGER DEFAULT 0,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW');
CREATE TABLE IF NOT EXISTS indicators(id TEXT PRIMARY KEY,data_product_id TEXT REFERENCES data_products(id),name TEXT,definition TEXT,unit TEXT,denominator TEXT,reference_period TEXT,synthetic INTEGER DEFAULT 0,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',is_target INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS variables(id TEXT PRIMARY KEY,indicator_id TEXT REFERENCES indicators(id),original_name TEXT,definition TEXT,unit TEXT,age_band TEXT,synthetic INTEGER DEFAULT 0,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW');
CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,variable_id TEXT REFERENCES variables(id),value TEXT,unit TEXT,geography TEXT,geography_level TEXT,period TEXT,synthetic INTEGER DEFAULT 0,transformation TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',population TEXT,observation_year INTEGER,publication_year INTEGER,temporal_status TEXT,source_id TEXT REFERENCES sources(id),original_variable_name TEXT,original_age_band TEXT,original_definition TEXT,denominator TEXT);
CREATE TABLE IF NOT EXISTS gap_claims(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),claim TEXT,quote TEXT,location TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',target_id TEXT,population TEXT,geography TEXT,limitation TEXT,synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS alignments(id TEXT PRIMARY KEY,target_indicator_id TEXT REFERENCES indicators(id),observed_indicator_id TEXT REFERENCES indicators(id),relation_class TEXT,rationale TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',evidence_quote TEXT,source_id TEXT REFERENCES sources(id),measurement_loss TEXT,synthetic INTEGER DEFAULT 0,derivation_status TEXT DEFAULT 'HUMAN_REVIEWED');
CREATE TABLE IF NOT EXISTS barriers(id TEXT PRIMARY KEY,barrier_type TEXT,description TEXT,evidence TEXT,source_id TEXT REFERENCES sources(id),review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',target_id TEXT,variable_id TEXT,verification_status TEXT,synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS search_runs(id TEXT PRIMARY KEY,provider TEXT,query TEXT,started_at TEXT,status TEXT,result_count INTEGER,details TEXT,target_id TEXT,population TEXT,geography TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',project_id TEXT);
CREATE TABLE IF NOT EXISTS search_candidates(id TEXT PRIMARY KEY,search_run_id TEXT REFERENCES search_runs(id),title TEXT,url TEXT,doi TEXT,source_type TEXT,metadata_json TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW');
CREATE TABLE IF NOT EXISTS review_candidates(id TEXT PRIMARY KEY,entity_type TEXT NOT NULL,payload_json TEXT NOT NULL,source_id TEXT,url TEXT,doi TEXT,retrieved_at TEXT NOT NULL,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',synthetic INTEGER NOT NULL DEFAULT 0,lineage_review TEXT);
CREATE TABLE IF NOT EXISTS formula_runs(id TEXT PRIMARY KEY,formula_id TEXT,version TEXT,weights TEXT,components TEXT,data_snapshot TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS formula_configs(formula_id TEXT,version TEXT,weights TEXT,rationale TEXT,author TEXT,created_at TEXT,PRIMARY KEY(formula_id,version));
CREATE TABLE IF NOT EXISTS research_tasks(id TEXT PRIMARY KEY,title TEXT,description TEXT,priority TEXT,status TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS source_links(source_id TEXT REFERENCES sources(id),related_source_id TEXT REFERENCES sources(id),link_type TEXT,PRIMARY KEY(source_id,related_source_id,link_type));
CREATE TABLE IF NOT EXISTS dedup_suppressions(id TEXT PRIMARY KEY,source_id TEXT,matched_id TEXT,match_basis TEXT,title TEXT,url TEXT,doi TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS macro_series(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),producer TEXT,collected_by TEXT,collection_method TEXT,frequency TEXT,aggregation_level TEXT,unit TEXT,definition TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS research_claims(id TEXT PRIMARY KEY,title TEXT NOT NULL,claim TEXT,identification_limits TEXT,source_id TEXT REFERENCES sources(id),target_indicator_id TEXT REFERENCES indicators(id),review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS claim_requirements(id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES research_claims(id),required_variable TEXT NOT NULL,variable_id TEXT REFERENCES variables(id),proxy_variable_id TEXT REFERENCES variables(id),analysis_limited TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',synthetic INTEGER DEFAULT 0);
"""

REVIEW_COLUMNS = {
    "sources": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'", "retrieved_at": "TEXT", "publication_year": "INTEGER", "underlying_data_id": "TEXT"},
    "data_products": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'"},
    "indicators": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'", "is_target": "INTEGER NOT NULL DEFAULT 0"},
    "variables": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'"},
    "observations": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'", "population": "TEXT", "observation_year": "INTEGER", "publication_year": "INTEGER", "temporal_status": "TEXT", "source_id": "TEXT", "original_variable_name": "TEXT", "original_age_band": "TEXT", "original_definition": "TEXT", "denominator": "TEXT"},
    "gap_claims": {"review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'", "target_id": "TEXT", "population": "TEXT", "geography": "TEXT", "limitation": "TEXT", "synthetic": "INTEGER DEFAULT 0"},
    "alignments": {"measurement_loss": "TEXT", "synthetic": "INTEGER DEFAULT 0", "derivation_status": "TEXT DEFAULT 'HUMAN_REVIEWED'"},
    "barriers": {"target_id": "TEXT", "variable_id": "TEXT", "verification_status": "TEXT", "synthetic": "INTEGER DEFAULT 0"},
    "search_runs": {"target_id": "TEXT", "population": "TEXT", "geography": "TEXT", "review_status": "TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW'", "project_id": "TEXT"},
    "research_claims": {"target_indicator_id": "TEXT", "synthetic": "INTEGER DEFAULT 0"},
    "claim_requirements": {"proxy_variable_id": "TEXT", "synthetic": "INTEGER DEFAULT 0"},
    "macro_series": {"synthetic": "INTEGER DEFAULT 0"},
}

def connect(path="data/registry.sqlite"):
    p = Path(path)
    if str(path) != ":memory:":
        p.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    for table, columns in REVIEW_COLUMNS.items():
        known = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in known:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    return db

def insert_model(db, table, model):
    data = model.model_dump(mode="json") if hasattr(model, "model_dump") else dict(model)
    data = {k: (int(v) if isinstance(v, bool) else v) for k, v in data.items()}
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    db.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})", tuple(data.values()))

def ensure_demo(db):
    """Compatibility no-op: no synthetic targets or observations are seeded."""
    return db

def enqueue_bundle(db, bundle, *, source_id, retrieved_at, url=None, doi=None, synthetic=False, lineage_review=None):
    """Save a complete source-linked bundle as one review candidate."""
    cid = bundle.get("id") or f"candidate_{source_id}"
    db.execute("""INSERT OR REPLACE INTO review_candidates
        (id,entity_type,payload_json,source_id,url,doi,retrieved_at,review_status,synthetic,lineage_review)
        VALUES(?,?,?,?,?,?,?,'PENDING_HUMAN_REVIEW',?,?)""",
        (cid, "bundle", json.dumps(bundle, ensure_ascii=False), source_id, url, doi, retrieved_at, int(synthetic), lineage_review))
    return cid

def approve_bundle(db, candidate_id):
    """Promote a reviewed bundle atomically to linked canonical entities."""
    candidate = db.execute("SELECT * FROM review_candidates WHERE id=?", (candidate_id,)).fetchone()
    if not candidate or candidate["review_status"] != "PENDING_HUMAN_REVIEW":
        raise ValueError("Candidate is missing or no longer pending review")
    bundle = json.loads(candidate["payload_json"])
    db.execute("BEGIN")
    try:
        for table in ("sources", "data_products", "indicators", "variables", "observations", "alignments", "gap_claims", "barriers", "research_claims", "claim_requirements", "macro_series"):
            for index, original in enumerate(bundle.get(table, [])):
                record = dict(original)
                record["review_status"] = "HUMAN_REVIEWED"
                record["synthetic"] = int(candidate["synthetic"])
                insert_model(db, table, record)
                original["review_status"]="HUMAN_REVIEWED"
                original["synthetic"]=int(candidate["synthetic"])
        db.execute("UPDATE review_candidates SET review_status='HUMAN_REVIEWED' WHERE id=?", (candidate_id,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return bundle
