import streamlit as st
from evidence_gap.database import connect,ensure_demo
from evidence_gap.tensor import from_database
from evidence_gap.gap_claims import state_for
from components.dark_atlas import matrix
from components.layer_controls import controls
from components.legend import render as legend
from components.source_drawer import render as drawer
def render():
    st.markdown("# Missing evidence")
    st.markdown("Where is direct, usable evidence missing for the selected target question?")
    st.caption("SYNTHETIC TARGET CATALOG · no real search has been run")
    left,main=st.columns([1,4],gap="large")
    with left:
        controls(); st.selectbox("GEOGRAPHY",["Not available: no geocoded observations"],disabled=True); st.selectbox("OBSERVATION PERIOD",["Not available: no observations"],disabled=True)
    db=ensure_demo(connect()); db.commit(); tensor=from_database(db); rows=tensor.project_gap()
    unknown=state_for().value
    targets=[r[0] for r in db.execute("SELECT name FROM indicators WHERE id LIKE 'demo_target_%' ORDER BY id")]
    populations=["Adults","Youth","Households","Institutions"]
    with main:
        fig=matrix(populations,targets,[[0]*len(populations) for _ in targets],"Evidence status · UNKNOWN until searched",[[0,"#454B50"],[1,"#454B50"]])
        fig.update_xaxes(title="Population group")
        fig.update_yaxes(title="Evidence domain / target indicator")
        fig.update_traces(text=[["UNKNOWN" for _ in populations] for _ in targets],texttemplate="%{text}",showscale=False)
        st.plotly_chart(fig,width="stretch")
        legend("gap")
        st.markdown("#### STATUS REGISTER")
        st.dataframe([{"target":t,"status":unknown,"source_count":0,"observation_level":"NOT ESTABLISHED"} for t in targets],width="stretch",hide_index=True)
    with left: drawer({"state":unknown,"direct_evidence_count":0,"independent_source_count":0,"level":"UNKNOWN","last_search":"NOT SEARCHED","registry_alignment_records":len(rows)})
