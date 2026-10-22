import streamlit as st
import yaml
from pathlib import Path
from evidence_gap.formulas import FormulaConfig
from evidence_gap.database import connect
def render():
    st.markdown("# Formula settings")
    cfg=yaml.safe_load(Path("config/measures.yaml").read_text(encoding="utf-8")); weights=cfg["components"]
    st.caption(f"{cfg['formula_id']} / VERSION {cfg['version']}")
    st.markdown("Weights must total 100%. An unknown component makes this score unknown.")
    cols=st.columns(2); edited={}
    for i,(name,value) in enumerate(weights.items()):
        with cols[i%2]: edited[name]=st.number_input(name.replace("_"," ").upper(),min_value=0,max_value=100,value=int(value),step=1)
    total=sum(edited.values()); st.markdown(f"**TOTAL: {total}%**")
    valid=FormulaConfig(cfg["formula_id"],cfg["version"],edited).validate()
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
            db.commit(); st.success(f"Saved {cfg['formula_id']} version {version.strip()}.")
    saved=[dict(r) for r in connect().execute("SELECT formula_id,version,weights,rationale,author,created_at FROM formula_configs ORDER BY created_at DESC")]
    st.markdown("#### SAVED VERSIONS")
    st.dataframe(saved,width="stretch",hide_index=True)
