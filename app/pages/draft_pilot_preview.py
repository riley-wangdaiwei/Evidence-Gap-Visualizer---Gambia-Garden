"""Unreviewed visual preview built directly from local staging CSVs.

This module never opens the registry or approved tensor and performs no writes.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PILOT = ["I009", "I013", "I014", "I015"]
PARKED = ["I002", "I011", "I019", "I022", "I023", "I024"]
ALIGNMENTS = ROOT / "data" / "imports" / "alignments.csv"
INDICATORS = ROOT / "data" / "imports" / "indicators.csv"
RELATION_COLORS = {
    "DIRECT_MATCH": "#287B72",
    "HARMONIZABLE": "#4B918C",
    "PROXY": "#B58B48",
    "CONCEPTUALLY_RELATED": "#B87942",
    "INCOMPATIBLE": "#A34D42",
    "UNKNOWN_REQUIRES_REVIEW": "#454B50",
}
RELATIONS = list(RELATION_COLORS)
DRAFT_BANNER = "DRAFT PREVIEW - NOT HUMAN REVIEWED - CANDIDATE DATA ONLY - DO NOT PRESENT AS APPROVED EVIDENCE"
SCOPE = "Pilot scope: 4 targets only (I009, I013, I014, I015); parked targets are not no-gap; this map is a pilot, not complete, especially I002 cannabis is parked."


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def frame_banner(view_name):
    st.markdown(
        f"<div style='border:2px solid #B87942;padding:16px 18px;margin:0 0 12px 0;"
        f"background:#15110d;color:#f2c98c;font:700 18px/1.4 monospace'>{DRAFT_BANNER}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**{SCOPE}**")
    st.caption(f"{view_name} / local staging CSV preview / candidate-only / registry and approved tensor untouched")


def render_view_b(alignments, indicators):
    frame_banner("VIEW B: OBSERVED LABEL TO PILOT TARGET")
    st.markdown("Rows are pilot target indicators. Columns preserve the raw `observed_indicator_or_variable` values exactly as CSV labels.")
    pilot_rows = [r for r in alignments if r.get("target_indicator_id") in PILOT]
    outside = [r for r in alignments if r.get("alignment_id") in {"AL013", "AL014", "AL015", "AL016", "AL022", "AL025"}]
    labels = list(dict.fromkeys(r.get("observed_indicator_or_variable", "") for r in pilot_rows))
    grid = { (r.get("target_indicator_id"), r.get("observed_indicator_or_variable", "")): r for r in pilot_rows }
    target_names = {r.get("indicator_id"): r.get("indicator_code", "") for r in indicators}
    z, text, hover = [], [], []
    for target in PILOT:
        zr=[]; tr=[]; hr=[]
        for label in labels:
            row=grid.get((target,label))
            if not row:
                zr.append(RELATIONS.index("UNKNOWN_REQUIRES_REVIEW")); tr.append("NO PAIR"); hr.append("No pilot alignment row for this pair; charcoal is not evidence of a searched gap")
                continue
            aid=row.get("alignment_id", "")
            relation=row.get("relationship_class", "UNKNOWN_REQUIRES_REVIEW")
            not_located = aid == "AL024" and "not yet located" in label.lower()
            shown="NOT LOCATED / GAP ⚠" if not_located else relation
            zr.append(RELATIONS.index("UNKNOWN_REQUIRES_REVIEW") if not_located else RELATIONS.index(relation) if relation in RELATIONS else RELATIONS.index("UNKNOWN_REQUIRES_REVIEW"))
            tr.append(shown)
            hr.append(f"{aid} | {relation}" + (" | EXCEPTION: raw value says not yet located; displayed as gap, not direct evidence" if not_located else ""))
        z.append(zr); text.append(tr); hover.append(hr)
    scale=[]
    for i,name in enumerate(RELATIONS):
        lo=0 if i==0 else (i-.5)/(len(RELATIONS)-1)
        hi=1 if i==len(RELATIONS)-1 else (i+.5)/(len(RELATIONS)-1)
        scale.extend([[lo,RELATION_COLORS[name]],[hi,RELATION_COLORS[name]])
    fig=go.Figure(go.Heatmap(x=labels,y=[f"{t} · {target_names.get(t,'')}" for t in PILOT],z=z,zmin=0,zmax=len(RELATIONS)-1,colorscale=scale,showscale=False,text=text,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=2,ygap=2))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2"},margin={"l":10,"r":10,"t":25,"b":30},height=570)
    fig.update_xaxes(tickangle=-30,gridcolor="#26333D")
    fig.update_yaxes(autorange="reversed",gridcolor="#26333D")
    st.plotly_chart(fig, width="stretch", theme=None, key="draft_pilot_view_b")
    counts=Counter(r.get("relationship_class", "UNKNOWN_REQUIRES_REVIEW") for r in pilot_rows if r.get("alignment_id")!="AL024")
    counts["NOT LOCATED / GAP (AL024 exception)"] += 1
    st.caption("Relationship colors: " + " / ".join(f"{name} {RELATION_COLORS[name]}" for name in RELATIONS))
    colored=sum(counts[name] for name in RELATIONS if name!="UNKNOWN_REQUIRES_REVIEW")
    st.markdown(f"**Pilot alignment rows:** {len(pilot_rows)} / **non-charcoal relationship rows:** {colored} / **NOT LOCATED exception:** AL024")
    st.caption("Rendered row counts: " + " / ".join(f"{name}: {counts[name]}" for name in [*RELATIONS,"NOT LOCATED / GAP (AL024 exception)"]))
    st.markdown("**Pilot-external alignments excluded from this view:** " + ", ".join(f"{r.get('alignment_id')} → {r.get('target_indicator_id')}" for r in outside))
    st.markdown("**Parked targets excluded from the pilot view (not no-gap):** " + ", ".join(PARKED))
    with st.expander("Raw pilot alignment rows"):
        st.dataframe([{k:r.get(k,"") for k in ("alignment_id","observed_indicator_or_variable","target_indicator_id","relationship_class")} for r in pilot_rows], hide_index=True, width="stretch")


def render_view_a(alignments, indicators):
    frame_banner("VIEW A: PILOT THEMES BY GEOGRAPHY")
    st.markdown("Rows use the target themes in `indicators.csv`; the only preview column is national. Candidate alignments carry no provenance supporting a district-level value, so no region cells are rendered.")
    pilot_rows=[r for r in alignments if r.get("target_indicator_id") in PILOT]
    target_meta={r.get("indicator_id"):r for r in indicators if r.get("indicator_id") in PILOT}
    indirect={"PROXY","HARMONIZABLE","CONCEPTUALLY_RELATED"}
    row_labels=[]; values=[]; labels=[]; hover=[]
    for target in PILOT:
        meta=target_meta.get(target,{})
        theme=meta.get("view_a_theme", "UNKNOWN")
        related=[r for r in pilot_rows if r.get("target_indicator_id")==target]
        has_indirect=any(r.get("relationship_class") in indirect for r in related)
        # AL024 explicitly says the measure is not yet located; it cannot create indirect evidence.
        if target=="I015":
            usable=[r for r in related if r.get("alignment_id")!="AL024"]
            has_indirect=any(r.get("relationship_class") in indirect for r in usable)
        color="#B58B48" if has_indirect else "#454B50"
        status="INDIRECT / PROXY CANDIDATE ONLY" if has_indirect else "UNKNOWN / GAP CANDIDATE"
        row_labels.append(f"{target} · {theme}"); values.append([0 if has_indirect else 1]); labels.append([status])
        hover.append([f"{status}; candidate-only alignments: {', '.join(r.get('alignment_id','') for r in related) or 'none'}; no regional support loaded"])
    fig=go.Figure(go.Heatmap(x=["National"],y=row_labels,z=values,zmin=0,zmax=1,colorscale=[[0,"#B58B48"],[0.499,"#B58B48"],[0.5,"#454B50"],[1,"#454B50"]],showscale=False,text=labels,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=3,ygap=3))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2"},margin={"l":10,"r":10,"t":25,"b":25},height=470)
    fig.update_xaxes(gridcolor="#26333D")
    fig.update_yaxes(autorange="reversed",gridcolor="#26333D")
    st.plotly_chart(fig,width="stretch",theme=None,key="draft_pilot_view_a")
    st.caption("Amber = indirect/proxy relationship candidate only. Charcoal = unknown/gap candidate; no direct evidence inferred. Geography is national only.")
    st.markdown("**Parked targets excluded, not shown as gray cells:** " + ", ".join(PARKED))


def render():
    alignments=read_csv(ALIGNMENTS)
    indicators=read_csv(INDICATORS)
    if not alignments:
        st.error("Draft preview unavailable: data/imports/alignments.csv is missing or empty.")
        return
    view_a,view_b=st.tabs(["View A · Pilot evidence gap","View B · Raw alignment categories"])
    with view_a:
        render_view_a(alignments,indicators)
    with view_b:
        render_view_b(alignments,indicators)
