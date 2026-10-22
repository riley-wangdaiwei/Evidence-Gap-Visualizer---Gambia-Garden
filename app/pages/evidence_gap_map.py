import streamlit as st
import yaml
from pathlib import Path
from evidence_gap.database import connect
from evidence_gap.tensor import from_database
from components.dark_atlas import matrix, categorical_scale, STATE_COLORS, add_cell_layers,add_friction_markers
from components.layer_controls import controls
from components.legend import render as legend
from components.source_drawer import render as drawer

def render():
    st.markdown("# Missing evidence")
    st.markdown("Where is sufficiently direct and usable evidence missing for the configured research question?")
    config=yaml.safe_load(Path("config/project.yaml").read_text(encoding="utf-8"))
    st.caption(f"{config['project_id']} / batch: {config.get('default_batch_dir','data/youth')}")
    db=connect(); tensor=from_database(db); records=tensor.project_gap()
    targets=list(dict.fromkeys(r["target_name"] for r in records))
    geos=list(dict.fromkeys(r["geography"] for r in records))
    populations=list(dict.fromkeys(r["population"] for r in records))
    left,main=st.columns([1,4],gap="large")
    with left:
        layers=controls()
        population=st.selectbox("AGE / POPULATION GROUP",populations) if populations else None
        years=sorted({r["observation_period"] for r in records if r.get("observation_period")})
        observation_year=st.selectbox("OBSERVATION PERIOD",["All",*years])
        source_options=sorted({s for r in records for s in r.get("source_ids",[]) if s})
        source_filter=st.selectbox("SOURCE",["All",*source_options])
        selected_target=st.selectbox("TARGET DETAIL",targets) if targets else None
        selected_geo=st.selectbox("GEOGRAPHY DETAIL",geos) if geos else None
    filtered=[r for r in records if (population is None or r["population"]==population)
              and (observation_year=="All" or r.get("observation_period")==observation_year)
              and (source_filter=="All" or source_filter in r.get("source_ids",[]))]
    lookup={(r["target_name"],r["geography"]):r for r in filtered}
    selected_barrier_id=None
    state_names=list(STATE_COLORS)
    state_index={s:i for i,s in enumerate(state_names)}
    z=[[state_index[lookup.get((t,g),{}).get("gap_state","NOT_SEARCHED_OR_UNKNOWN")] for g in geos] for t in targets]
    labels=[[lookup.get((t,g),{}).get("gap_state","NOT_SEARCHED_OR_UNKNOWN") for g in geos] for t in targets]
    hover=[["\n".join([f"{k}: {v}" for k,v in lookup.get((t,g),{}).items() if k in (("gap_state","flags","direct_evidence_count","independent_source_count","observation_period","publication_year","review_status","source_titles","source_ids") if layers.get("sources") else ("gap_state","flags","direct_evidence_count","independent_source_count","observation_period","publication_year","review_status"))]) or "NOT_SEARCHED_OR_UNKNOWN" for g in geos] for t in targets]
    with main:
        if not targets:
            st.info("No target topics are configured. Add topic definitions to config/taxonomy.yaml.")
        else:
            scale=categorical_scale(state_names,STATE_COLORS)
            cell_text=[[f"{labels[y][x]} ///" if labels[y][x]=="NOT_SEARCHED_OR_UNKNOWN" else labels[y][x] for x in range(len(geos))] for y in range(len(targets))]
            fig=matrix(geos,targets,z,"Evidence gap / availability state",scale,text=cell_text,hovertext=hover,zmax=len(state_names)-1)
            if layers.get("vectors"):
                for yi,t in enumerate(targets):
                    for xi,g in enumerate(geos):
                        cell=lookup.get((t,g),{})
                        if cell.get("direct_evidence_count"):
                            add_cell_layers(fig,x_index=xi,y_index=yi,vector=True,source_count=cell.get("independent_source_count",0),derivation_status=cell.get("review_status") or "RULE_DERIVED")
            if layers.get("friction"):
                friction_points=[]
                for yi,t in enumerate(targets):
                    for xi,g in enumerate(geos):
                        cell=lookup.get((t,g),{})
                        for barrier in cell.get("barriers",[]):
                            friction_points.append({"x":xi+.3,"y":yi-.3,"id":barrier["id"],"type":barrier["barrier_type"],"description":barrier["description"]})
                add_friction_markers(fig,friction_points)
            fig.data[0].visible=layers.get("heatmap",True)
            event=st.plotly_chart(fig,width="stretch",theme=None,on_select="rerun",selection_mode="points",key="evidence_gap_matrix")
            try:
                points=event.selection.points
                if points and points[-1].get("customdata"): selected_barrier_id=points[-1]["customdata"][0]
            except (AttributeError,KeyError,TypeError): pass
            legend("gap")
            st.dataframe([{"target":t,"geography":g,"state":lookup.get((t,g),{}).get("gap_state","NOT_SEARCHED_OR_UNKNOWN"),
                           "flags":", ".join(lookup.get((t,g),{}).get("flags",[])),
                           "direct records":lookup.get((t,g),{}).get("direct_evidence_count",0),
                           "independent sources":lookup.get((t,g),{}).get("independent_source_count",0)} for t in targets for g in geos],width="stretch",hide_index=True)
    with left:
        selected=lookup.get((selected_target,selected_geo),{}) if selected_target and selected_geo else {}
        barriers=[dict(r) for r in db.execute("SELECT * FROM barriers WHERE target_id=? AND review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')",(selected.get("target_id"),))] if selected else []
        if selected_barrier_id:
            chosen=db.execute("SELECT * FROM barriers WHERE id=?",(selected_barrier_id,)).fetchone()
            if chosen:
                st.markdown("#### SELECTED FRICTION MARKER")
                drawer(dict(chosen))
        selected["barriers"]=barriers
        drawer({"target":selected_target,"geography":selected_geo,"population":population or "UNKNOWN",
                "state":selected.get("gap_state","NOT_SEARCHED_OR_UNKNOWN"),"warning flags":selected.get("flags",[]),
                "sources":selected.get("source_titles",[]),"source IDs":selected.get("source_ids",[]),
                "original definition":selected.get("original_definition"),"original age band":selected.get("age_band"),
                "observation year":selected.get("observation_period"),"publication year":selected.get("publication_year"),
                "geographic level":selected.get("geography_level","UNKNOWN"),
                "direct evidence count":selected.get("direct_evidence_count",0),
                "independent source count":selected.get("independent_source_count",0),
                "review status":selected.get("review_status","NOT REVIEWED"),"barriers":barriers})
        if selected.get("gap_claims"):
            st.markdown("#### SOURCE-REPORTED GAP CLAIMS")
            st.dataframe(selected["gap_claims"],width="stretch",hide_index=True)
