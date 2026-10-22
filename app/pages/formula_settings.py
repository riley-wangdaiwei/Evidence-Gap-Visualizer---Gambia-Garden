import streamlit as st
import yaml
import json
from pathlib import Path
from evidence_gap.formulas import FormulaConfig,weighted_score,record_formula_run
from evidence_gap.database import connect
def render():
    st.markdown("# Formula settings")
    cfg=yaml.safe_load(Path("config/measures.yaml").read_text(encoding="utf-8")); weights=cfg["components"]
    st.caption(f"{cfg['formula_id']} / VERSION {cfg['version']}")
    st.markdown("Weights must total 100%. An unknown component makes this score unknown.")
    cols=st.columns(2); edited={}; components={}
    for i,(name,value) in enumerate(weights.items()):
        with cols[i%2]: edited[name]=st.number_input(name.replace("_"," ").upper(),min_value=0,max_value=100,value=int(value),step=1)
    st.markdown("#### COMPONENT VALUES")
    st.caption("Leave unsupported components blank. Unknown is stored as null, never zero.")
    value_cols=st.columns(2)
    for i,name in enumerate(weights):
        with value_cols[i%2]: components[name]=st.number_input(f"{name.replace('_',' ').upper()} VALUE",min_value=0.0,max_value=1.0,value=None,step=.05,placeholder="Unknown")
    total=sum(edited.values()); st.markdown(f"**TOTAL: {total}%**")
    valid=FormulaConfig(cfg["formula_id"],cfg["version"],edited).validate()
    score=weighted_score(FormulaConfig(cfg["formula_id"],cfg["version"],edited),components) if valid else None
    st.markdown(f"**COMPONENT RESULT: {'UNKNOWN' if score is None else round(score,4)}**")
    st.dataframe([{"component":name,"weight_percent":edited[name],"value":"UNKNOWN" if components[name] is None else components[name],"weighted_contribution":"UNKNOWN" if components[name] is None else edited[name]*components[name]/100} for name in edited],width="stretch",hide_index=True)
    st.success("Valid configuration") if valid else st.error("Cannot save: weights must sum to 100%.")
    version=st.text_input("VERSION",value=str(cfg["version"]))
    author=st.text_input("AUTHOR / REVIEWER")
    rationale=st.text_area("RATIONALE")
    db=connect()
    version_exists=bool(db.execute("SELECT 1 FROM formula_configs WHERE formula_id=? AND version=?",(cfg["formula_id"],version.strip())).fetchone())
    if version_exists: st.warning("This formula version already exists. Choose a new version to preserve its history.")
    if st.button("Save formula version",disabled=(not valid or version_exists)):
        if not version.strip() or not rationale.strip(): st.error("A version and rationale are required.")
        else:
            db.execute("INSERT INTO formula_configs(formula_id,version,weights,rationale,author,created_at) VALUES(?,?,?,?,?,datetime('now'))",(cfg["formula_id"],version.strip(),yaml.safe_dump(edited,sort_keys=True),rationale.strip(),author.strip() or None))
            snapshot_tables=("sources","data_products","indicators","variables","observations","alignments","gap_claims","barriers","macro_series")
            snapshot_rows={table:[dict(r) for r in db.execute(f"SELECT * FROM {table} WHERE review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED') AND COALESCE(synthetic,0)=0")] for table in snapshot_tables}
            run=record_formula_run(FormulaConfig(cfg["formula_id"],version.strip(),edited),components,snapshot_rows)
            counts={table:len(rows) for table,rows in snapshot_rows.items()}
            db.execute("INSERT INTO formula_runs(id,formula_id,version,weights,components,data_snapshot,created_at) VALUES(?,?,?,?,?,?,?)",(run["id"],run["formula_id"],run["version"],json.dumps(run["weights"],sort_keys=True),json.dumps(run["components"],sort_keys=True),json.dumps({"sha256":run["data_snapshot"],"approved_record_counts":counts},sort_keys=True),run["created_at"]))
            db.commit(); st.success(f"Saved {cfg['formula_id']} version {version.strip()} and recorded a formula run.")
    saved=[dict(r) for r in connect().execute("SELECT formula_id,version,weights,rationale,author,created_at FROM formula_configs ORDER BY created_at DESC")]
    st.markdown("#### SAVED VERSIONS")
    st.dataframe(saved,width="stretch",hide_index=True)
    st.markdown("#### RECORDED RUNS")
    runs=[dict(r) for r in connect().execute("SELECT formula_id,version,weights,components,data_snapshot,created_at FROM formula_runs ORDER BY created_at DESC")]
    st.dataframe(runs,width="stretch",hide_index=True)
