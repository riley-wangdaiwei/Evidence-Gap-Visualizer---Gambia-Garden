import streamlit as st
from evidence_gap.database import connect
from evidence_gap.tensor import from_database
from components.dark_atlas import matrix,categorical_scale,RELATION_COLORS,add_cell_layers,add_friction_markers
from components.layer_controls import controls
from components.legend import render as legend
from components.source_drawer import render as drawer

CLASSES=["DIRECT_MATCH","HARMONIZABLE","PROXY","CONCEPTUALLY_RELATED","INCOMPATIBLE","UNKNOWN_REQUIRES_REVIEW"]

def render():
    st.markdown("# Proxy / indicator alignment")
    st.markdown("Observed variables remain distinct from target measures; alignments are reviewed records.")
    db=connect(); tensor=from_database(db); relations=tensor.project_proxy()
    targets=list(dict.fromkeys(r["target_name"] for r in relations))
    observed=list(dict.fromkeys(r.get("observed_label") or r["observed_name"] for r in relations))
    left,main=st.columns([1,4],gap="large")
    with left:
        layers=controls()
        selected_claim_row=None
        claims=[dict(r) for r in db.execute("SELECT * FROM research_claims WHERE review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED') ORDER BY title")]
        selected_claim=st.selectbox("CLAIM AUDIT",["Select a reviewed claim",*[(r["title"] or r["id"]) for r in claims]])
        review=st.selectbox("REVIEW STATUS",["Approved records only","HUMAN_REVIEWED","SOURCE_VERIFIED"])
        selected_claim_row=next((r for r in claims if (r["title"] or r["id"])==selected_claim),None)
    allowed={"HUMAN_REVIEWED","SOURCE_VERIFIED"} if review=="Approved records only" else {review}
    relations=[r for r in relations if r.get("review_status") in allowed]
    targets=list(dict.fromkeys(r["target_name"] for r in relations))
    observed=list(dict.fromkeys(r.get("observed_label") or r["observed_name"] for r in relations))
    lookup={(r["target_name"],r.get("observed_label") or r["observed_name"]):r for r in relations}
    selected_barrier_id=None
    with main:
        if targets and observed:
            indices={c:i for i,c in enumerate(CLASSES)}
            z=[[indices.get(lookup.get((t,o),{}).get("relation_class","UNKNOWN_REQUIRES_REVIEW"),5) for o in observed] for t in targets]
            hover=[["\n".join([f"{k}: {v}" for k,v in lookup.get((t,o),{}).items() if k in (("relation_class","rationale","measurement_loss","source_title","source_id","review_status","derivation_status") if layers.get("sources") else ("relation_class","rationale","measurement_loss","review_status","derivation_status"))]) or "UNKNOWN_REQUIRES_REVIEW" for o in observed] for t in targets]
            cell_text=[[lookup.get((t,o),{}).get("relation_class","UNKNOWN_REQUIRES_REVIEW") for o in observed] for t in targets]
            fig=matrix(observed,targets,z,"Reviewed target ↔ observed-measure relationships",categorical_scale(CLASSES,RELATION_COLORS),text=cell_text,hovertext=hover,zmax=len(CLASSES)-1)
            if layers.get("vectors"):
                for yi,t in enumerate(targets):
                    for xi,o in enumerate(observed):
                        relation=lookup.get((t,o),{})
                        if relation and relation.get("relation_class")!="UNKNOWN_REQUIRES_REVIEW":
                            add_cell_layers(fig,x_index=xi,y_index=yi,vector=True,source_count=relation.get("independent_source_count",0),derivation_status=relation.get("derivation_status") or relation.get("review_status") or "HUMAN_REVIEWED")
            if layers.get("friction"):
                barriers=[dict(r) for r in db.execute("SELECT * FROM barriers WHERE review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')")]
                friction_points=[]
                for yi,t in enumerate(targets):
                    for xi,o in enumerate(observed):
                        relation=lookup.get((t,o),{})
                        for barrier in barriers:
                            if barrier.get("target_id")==relation.get("target_indicator_id"):
                                friction_points.append({"x":xi+.3,"y":yi-.3,"id":barrier["id"],"type":barrier["barrier_type"],"description":barrier["description"]})
                add_friction_markers(fig,friction_points)
            fig.data[0].visible=layers.get("heatmap",True)
            event=st.plotly_chart(fig,width="stretch",theme=None,on_select="rerun",selection_mode="points",key="proxy_alignment_matrix")
            try:
                points=event.selection.points
                if points and points[-1].get("customdata"): selected_barrier_id=points[-1]["customdata"][0]
            except (AttributeError,KeyError,TypeError): pass
        else:
            st.info("No approved alignments are in the registry. The configured topics remain unknown; no observed-measure columns are fabricated.")
        legend("proxy")
        st.dataframe(relations,width="stretch",hide_index=True)
    with left:
        if selected_claim_row:
            claim=selected_claim_row
            st.markdown("#### WHAT THE CLAIM NEEDS")
            requirements=[dict(r) for r in db.execute("SELECT * FROM claim_requirements WHERE claim_id=? AND review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')",(claim["id"],))]
            for req in requirements:
                found=db.execute("SELECT id,original_name,definition,age_band,unit FROM variables WHERE id=? AND review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')",(req.get("variable_id"),)).fetchone() if req.get("variable_id") else None
                if found:
                    status="FOUND"
                    variable_id=found["id"]
                else:
                    proxy=db.execute("""SELECT v.id,v.original_name,a.relation_class,a.rationale,a.measurement_loss FROM alignments a JOIN variables v ON v.indicator_id=a.observed_indicator_id
                        WHERE v.id=? AND a.target_indicator_id=? AND a.relation_class IN ('PROXY','CONCEPTUALLY_RELATED') AND a.review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')
                        AND v.review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED') LIMIT 1""",(req.get("proxy_variable_id"),claim.get("target_indicator_id"))).fetchone()
                    status="PROXY ONLY" if proxy else "MISSING"
                    variable_id=proxy["id"] if proxy else None
                st.markdown(f"**{req['required_variable']} — {status}**")
                if found: st.caption(f"Observed field: {found['original_name']} / {found['definition']} / age: {found['age_band']} / unit: {found['unit']}")
                if not found and proxy: st.caption(f"Explicitly linked proxy: {proxy['original_name']} / {proxy['relation_class']} / loss: {proxy['measurement_loss'] or proxy['rationale'] or 'not documented'}")
                if req.get("analysis_limited"): st.caption(f"Analysis limited: {req['analysis_limited']}")
            if not requirements: st.info("This claim has no approved variable requirements recorded yet.")
            st.markdown("#### WHAT REMAINS UNIDENTIFIED")
            st.write(claim.get("identification_limits") or "No identification limits documented yet; the claim does not establish causality by itself.")
            drawer({"claim":claim.get("claim"),"source_id":claim.get("source_id"),"review_status":claim.get("review_status"),"requirements":requirements})
        else:
            st.caption("Claim Audit content is loaded from reviewed research_claims and claim_requirements records.")
        if selected_barrier_id:
            selected_barrier=db.execute("SELECT * FROM barriers WHERE id=?",(selected_barrier_id,)).fetchone()
            if selected_barrier:
                st.markdown("#### SELECTED FRICTION MARKER")
                drawer(dict(selected_barrier))
