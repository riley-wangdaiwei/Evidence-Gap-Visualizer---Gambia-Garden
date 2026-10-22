import sqlite3
from pathlib import Path

SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,title TEXT NOT NULL,source_type TEXT,url TEXT,doi TEXT,producer TEXT,collected_by TEXT,access_status TEXT,synthetic INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS data_products(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),name TEXT,product_type TEXT,geography_level TEXT,population TEXT,observation_period TEXT,synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS indicators(id TEXT PRIMARY KEY,data_product_id TEXT REFERENCES data_products(id),name TEXT,definition TEXT,unit TEXT,denominator TEXT,reference_period TEXT,synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS variables(id TEXT PRIMARY KEY,indicator_id TEXT REFERENCES indicators(id),original_name TEXT,definition TEXT,unit TEXT,age_band TEXT,synthetic INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,variable_id TEXT REFERENCES variables(id),value TEXT,unit TEXT,geography TEXT,geography_level TEXT,period TEXT,synthetic INTEGER DEFAULT 0,transformation TEXT);
CREATE TABLE IF NOT EXISTS gap_claims(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),claim TEXT,quote TEXT,location TEXT,review_status TEXT);
CREATE TABLE IF NOT EXISTS alignments(id TEXT PRIMARY KEY,target_indicator_id TEXT REFERENCES indicators(id),observed_indicator_id TEXT REFERENCES indicators(id),relation_class TEXT,rationale TEXT,review_status TEXT,evidence_quote TEXT,source_id TEXT REFERENCES sources(id));
CREATE TABLE IF NOT EXISTS barriers(id TEXT PRIMARY KEY,barrier_type TEXT,description TEXT,evidence TEXT,source_id TEXT REFERENCES sources(id),review_status TEXT);
CREATE TABLE IF NOT EXISTS search_runs(id TEXT PRIMARY KEY,provider TEXT,query TEXT,started_at TEXT,status TEXT,result_count INTEGER,details TEXT);
CREATE TABLE IF NOT EXISTS search_candidates(id TEXT PRIMARY KEY,search_run_id TEXT REFERENCES search_runs(id),title TEXT,url TEXT,doi TEXT,source_type TEXT,metadata_json TEXT,review_status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW');
CREATE TABLE IF NOT EXISTS formula_runs(id TEXT PRIMARY KEY,formula_id TEXT,version TEXT,weights TEXT,components TEXT,data_snapshot TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS formula_configs(formula_id TEXT,version TEXT,weights TEXT,rationale TEXT,author TEXT,created_at TEXT,PRIMARY KEY(formula_id,version));
CREATE TABLE IF NOT EXISTS research_tasks(id TEXT PRIMARY KEY,title TEXT,description TEXT,priority TEXT,status TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS source_links(source_id TEXT REFERENCES sources(id),related_source_id TEXT REFERENCES sources(id),link_type TEXT,PRIMARY KEY(source_id,related_source_id,link_type));
"""
def connect(path="data/registry.sqlite"):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(p); db.row_factory=sqlite3.Row; db.executescript(SCHEMA); return db
def insert_model(db, table, model):
    data=model.model_dump(mode="json"); data={k:(int(v) if isinstance(v,bool) else v) for k,v in data.items()}
    cols=", ".join(data); marks=", ".join("?" for _ in data)
    db.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})",tuple(data.values()))

def ensure_demo(db):
    """Insert clearly synthetic measurement catalog fixtures, never observations."""
    specs=[
      ("account_count","Account count","Number of savings accounts reported; not unique people.","accounts"),
      ("account_holders","Account holders","Number of account holders; unit and deduplication would require source documentation.","holders"),
      ("saved_12m","Saved in previous 12 months","Whether a person or household saved during the prior 12 months.","binary response")]
    for key,name,definition,unit in specs:
        sid=f"demo_source_{key}"; pid=f"demo_product_{key}"; iid=f"demo_indicator_{key}"; vid=f"demo_variable_{key}"
        db.execute("INSERT OR IGNORE INTO sources(id,title,source_type,access_status,synthetic) VALUES(?,?,?,?,1)",(sid,f"SYNTHETIC: {name} example","synthetic_demo","fixture"))
        db.execute("INSERT OR IGNORE INTO data_products(id,source_id,name,product_type,geography_level,population,synthetic) VALUES(?,?,?,?,?,?,1)",(pid,sid,f"SYNTHETIC: {name} product","illustrative_catalog","country","unspecified"))
        db.execute("INSERT OR IGNORE INTO indicators(id,data_product_id,name,definition,unit,synthetic) VALUES(?,?,?,?,?,1)",(iid,pid,name,definition,unit))
        db.execute("INSERT OR IGNORE INTO variables(id,indicator_id,original_name,definition,unit,synthetic) VALUES(?,?,?,?,?,1)",(vid,iid,key,definition,unit))
    for key,name,definition in [("activity","Savings activity","Evidence of saving during a stated reference period."),("ownership","Account ownership","Ownership of a savings account by a defined person or household."),("balance","Savings balance","Amount saved at a stated date or period.")]:
        db.execute("INSERT OR IGNORE INTO indicators(id,data_product_id,name,definition,unit,synthetic) VALUES(?,NULL,?,?,NULL,1)",(f"demo_target_{key}",f"SYNTHETIC TARGET: {name}",definition))
    return db
