import streamlit as st
from evidence_gap.database import connect,ensure_demo
from evidence_gap.tensor import from_database
from components.dark_atlas import matrix,empty_matrix
from components.layer_controls import controls
from components.legend import render as legend
from components.source_drawer import render as drawer
def render():
    st.markdown("# Proxy / indicator alignment")
    st.markdown("Candidate measures stay distinct: account counts ≠ account holders ≠ people who saved.")
    st.caption("SYNTHETIC CATALOG FIXTURES · not observations about The Gambia")
    left,main=st.columns([1,4],gap="large")
    with left:
        controls(); st.selectbox("REVIEW STATUS",["All","HUMAN_REVIEWED","SOURCE_VERIFIED"]); st.selectbox("ACCESS",["All","Open","Restricted"])
    db=ensure_demo(connect()); db.commit(); tensor=from_database(db); rows=tensor.project_proxy()
    with main:
        if rows:
            targets=list(dict.fromkeys(r.get("target_name") or "UNKNOWN TARGET" for r in rows)); observed=list(dict.fromkeys(r.get("observed_name") or "UNKNOWN MEASURE" for r in rows))
            classes={"DIRECT_MATCH":0,"HARMONIZABLE":1,"PROXY":2,"CONCEPTUALLY_RELATED":3,"INCOMPATIBLE":4,"UNKNOWN_REQUIRES_REVIEW":5}
            lookup={(r.get("target_name"),r.get("observed_name")):classes.get(r.get("relation_class"),5) for r in rows}
            z=[[lookup.get((t,o)) for o in observed] for t in targets]
            fig=matrix(observed,targets,z,"Recorded alignment classes",[[0,"#4B918C"],[.4,"#B58B48"],[.8,"#A34D42"],[1,"#454B50"]])
        else:
            fig=empty_matrix("No saved alignment records","Observed indicator / variable","Target concept","NO RECORDED RELATIONSHIPS · alignment remains UNKNOWN_REQUIRES_REVIEW")
        st.plotly_chart(fig,width="stretch")
        legend("proxy")
        st.dataframe(rows,width="stretch",hide_index=True)
    with left: drawer({"class":"UNKNOWN_REQUIRES_REVIEW","rationale":"Definitions and source documentation are absent in synthetic fixtures.","source_id":"NONE","review_status":"HUMAN_REVIEW_REQUIRED","stored_alignment_records":len(rows)})
