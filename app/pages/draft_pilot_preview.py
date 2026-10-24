"""Unreviewed visual preview built directly from local staging CSVs.

This module never opens the registry or approved tensor and performs no writes.
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PILOT = ["I009", "I013", "I014", "I015"]
PARKED = ["I002", "I011", "I019", "I022", "I023", "I024"]
DATA_DIRS = [ROOT / "data" / "preview", ROOT / "data" / "imports"]
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
TIME_BINS = ["2010–2014", "2015–2019", "2020–2022", "2023–2026", "Observation time unknown"]
INDIRECT_RELATIONS = {"PROXY", "HARMONIZABLE", "CONCEPTUALLY_RELATED"}


def read_csv(filename):
    for directory in DATA_DIRS:
        path = directory / filename
        if path.exists():
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
    return []


def frame_banner(view_name):
    st.markdown(
        f"<div style='border:2px solid #B87942;padding:16px 18px;margin:0 0 12px 0;"
        f"background:#15110d;color:#f2c98c;font:700 18px/1.4 monospace'>{DRAFT_BANNER}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**{SCOPE}**")
    st.caption(f"{view_name} / local staging CSV preview / candidate-only / registry and approved tensor untouched")


def observation_time_bin(row):
    raw = row.get("observation_year") or ""
    match = re.search(r"\d{4}", raw)
    if not match:
        return TIME_BINS[-1]
    year = int(match.group(0))
    for label, lower, upper in (
        (TIME_BINS[0], 2010, 2014),
        (TIME_BINS[1], 2015, 2019),
        (TIME_BINS[2], 2020, 2022),
        (TIME_BINS[3], 2023, 2026),
    ):
        if lower <= year <= upper:
            return label
    return TIME_BINS[-1]


def detail_text(row):
    aid = row.get("alignment_id", "UNKNOWN") or "UNKNOWN"
    relation = row.get("relationship_class", "UNKNOWN_REQUIRES_REVIEW") or "UNKNOWN_REQUIRES_REVIEW"
    observed = row.get("observed_indicator_or_variable", "UNKNOWN") or "UNKNOWN"
    disposition = " | NOT LOCATED / GAP exception; excluded from evidence color" if aid == "AL024" and "not yet located" in observed.lower() else ""
    return (
        f"Pair: {aid}<br>Measured: {observed}<br>Relationship: {relation}{disposition}"
        f"<br>Source title: {row.get('title') or 'UNKNOWN'}"
        f"<br>Observation year (raw): {row.get('observation_year') or 'UNKNOWN'}"
        f"<br>Original age: {row.get('original_age_group') or 'UNKNOWN'}"
        f"<br>Geography: {row.get('geographic_level') or 'UNKNOWN'}"
    )


def short_label(value, limit=28):
    value = value or "(empty label)"
    return value if len(value) <= limit else value[: limit - 1] + "…"


def render_view_b(alignments, indicators):
    frame_banner("VIEW B: OBSERVED LABEL TO PILOT TARGET")
    st.markdown("Rows are pilot target indicators. Columns preserve the raw `observed_indicator_or_variable` values exactly as CSV labels.")
    pilot_rows = [r for r in alignments if r.get("target_indicator_id") in PILOT]
    outside = [r for r in alignments if r.get("alignment_id") in {"AL013", "AL014", "AL015", "AL016", "AL022", "AL025"}]
    labels = list(dict.fromkeys(r.get("observed_indicator_or_variable", "") for r in pilot_rows))
    grid = {}
    for row in pilot_rows:
        grid.setdefault((row.get("target_indicator_id"), row.get("observed_indicator_or_variable", "")), []).append(row)
    target_names = {r.get("indicator_id"): r.get("indicator_code", "") for r in indicators}
    z, text, hover = [], [], []
    for target in PILOT:
        zr=[]; tr=[]; hr=[]
        for label in labels:
            rows=grid.get((target,label), [])
            if not rows:
                zr.append(RELATIONS.index("UNKNOWN_REQUIRES_REVIEW")); tr.append("NO PAIR"); hr.append("No pilot alignment row for this pair; charcoal is not evidence of a searched gap")
                continue
            valid_relations = {
                row.get("relationship_class", "UNKNOWN_REQUIRES_REVIEW")
                for row in rows
                if not (row.get("alignment_id") == "AL024" and "not yet located" in (row.get("observed_indicator_or_variable") or "").lower())
            }
            has_not_located = any(row.get("alignment_id") == "AL024" and "not yet located" in (row.get("observed_indicator_or_variable") or "").lower() for row in rows)
            relation = next(iter(valid_relations)) if len(valid_relations) == 1 else "UNKNOWN_REQUIRES_REVIEW"
            relation_index = RELATIONS.index(relation) if relation in RELATIONS else RELATIONS.index("UNKNOWN_REQUIRES_REVIEW")
            zr.append(relation_index)
            if has_not_located and not valid_relations:
                shown = "NOT LOCATED / GAP"
            elif has_not_located:
                shown = f"NOT LOCATED / GAP + {relation}" if len(valid_relations) == 1 else "NOT LOCATED / GAP + MULTIPLE"
            else:
                shown = relation if len(valid_relations) == 1 else "MULTIPLE / REVIEW"
            tr.append(shown)
            hr.append("<br><br>".join(detail_text(row) for row in rows))
        z.append(zr); text.append(tr); hover.append(hr)
    scale=[]
    for i,name in enumerate(RELATIONS):
        lo=0 if i==0 else (i-.5)/(len(RELATIONS)-1)
        hi=1 if i==len(RELATIONS)-1 else (i+.5)/(len(RELATIONS)-1)
        scale.extend([[lo,RELATION_COLORS[name]],[hi,RELATION_COLORS[name]]])
    fig=go.Figure(go.Heatmap(x=list(range(len(labels))),y=[f"{t} · {target_names.get(t,'')}" for t in PILOT],z=z,zmin=0,zmax=len(RELATIONS)-1,colorscale=scale,showscale=False,text=text,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=2,ygap=2))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2"},margin={"l":270,"r":35,"t":35,"b":155},height=650)
    fig.update_xaxes(tickmode="array",tickvals=list(range(len(labels))),ticktext=[short_label(label) for label in labels],tickangle=-35,gridcolor="#26333D")
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
    frame_banner("VIEW A: PILOT THEMES BY OBSERVATION TIME")
    st.markdown("Rows are the four pilot targets in fixed order. Columns use only the first four-digit year in each pairing row's `observation_year`; publication year is not substituted. Geography is detail only, never an axis.")
    pilot_rows=[r for r in alignments if r.get("target_indicator_id") in PILOT]
    target_meta={r.get("indicator_id"):r for r in indicators if r.get("indicator_id") in PILOT}
    grid={}
    for row in pilot_rows:
        grid.setdefault((row.get("target_indicator_id"), observation_time_bin(row)), []).append(row)
    row_labels=[]; values=[]; labels=[]; hover=[]; counts=[]
    for target in PILOT:
        meta=target_meta.get(target,{})
        theme=meta.get("view_a_theme", "UNKNOWN")
        row_values=[]; row_labels_text=[]; row_hover=[]; row_counts=[]
        for time_bin in TIME_BINS:
            related=grid.get((target,time_bin), [])
            is_not_located=[r for r in related if r.get("alignment_id")=="AL024" and "not yet located" in (r.get("observed_indicator_or_variable") or "").lower()]
            usable=[r for r in related if r not in is_not_located]
            has_indirect=any(r.get("relationship_class") in INDIRECT_RELATIONS for r in usable)
            has_no_pair=not related
            if has_no_pair:
                status="NO ALIGNMENT"
            elif has_indirect and is_not_located:
                status="INDIRECT + NOT LOCATED / GAP"
            elif has_indirect:
                status="INDIRECT"
            elif is_not_located:
                status="NOT LOCATED / GAP"
            else:
                status="UNKNOWN / INCOMPATIBLE"
            row_values.append(0 if has_indirect else 1)
            row_labels_text.append(f"{status}\n({len(related)})" if related else status)
            details="<br><br>".join(detail_text(r) for r in related) if related else "No alignment in preview data. This is not a finding that evidence does not exist."
            row_hover.append(f"{target} · {theme}<br>Time bin: {time_bin}<br>Cell state: {status}<br>Pair count: {len(related)}<br><br>{details}")
            row_counts.append(len(related))
        row_labels.append(f"{target} · {theme}"); values.append(row_values); labels.append(row_labels_text); hover.append(row_hover); counts.append(row_counts)
    fig=go.Figure(go.Heatmap(x=TIME_BINS,y=row_labels,z=values,zmin=0,zmax=1,colorscale=[[0,"#B58B48"],[0.499,"#B58B48"],[0.5,"#454B50"],[1,"#454B50"]],showscale=False,text=labels,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=3,ygap=3))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2"},margin={"l":285,"r":35,"t":35,"b":90},height=590)
    fig.update_xaxes(tickangle=-20,gridcolor="#26333D")
    fig.update_yaxes(autorange="reversed",gridcolor="#26333D")
    st.plotly_chart(fig,width="stretch",theme=None,key="draft_pilot_view_a")
    st.caption("Amber = at least one PROXY / HARMONIZABLE / CONCEPTUALLY_RELATED pairing (candidate only). Charcoal labels distinguish UNKNOWN / INCOMPATIBLE, NO ALIGNMENT, and NOT LOCATED / GAP. No numeric values are averaged or combined. Geography remains in hover details only; no national values are copied to local areas.")
    st.markdown("**Cell pair counts by target × time bin:**")
    st.dataframe([{"target":target,"time_bin":time_bin,"state":labels[i][j].replace("\n", " "),"pair_count":counts[i][j]} for i,target in enumerate(PILOT) for j,time_bin in enumerate(TIME_BINS)],hide_index=True,width="stretch")
    st.markdown("**Parked targets excluded, not shown as gray cells:** " + ", ".join(PARKED))


def render():
    alignments=read_csv("alignments.csv")
    indicators=read_csv("indicators.csv")
    if not alignments:
        st.error("Draft preview unavailable: alignments.csv is missing or empty in data/preview/ and data/imports/.")
        return
    view_a,view_b=st.tabs(["View A · Pilot evidence gap","View B · Raw alignment categories"])
    with view_a:
        render_view_a(alignments,indicators)
    with view_b:
        render_view_b(alignments,indicators)
