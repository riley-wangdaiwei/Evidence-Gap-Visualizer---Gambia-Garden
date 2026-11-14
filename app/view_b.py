"""View-B-only presentation for the existing Gambia evidence inventory."""

import re

import plotly.graph_objects as go
import streamlit as st


TOPICS = [
    ("Prevention programme landscape and design", ["Types of prevention programmes", "Programme goals and target issues", "Programme components / activities", "Implementing organizations and delivery settings", "Programme availability and implementation period"]),
    ("Target population, eligibility, and access", ["Intended age groups / target population", "Eligibility criteria", "Availability and geographic access", "Awareness, referral, and entry into programmes", "Barriers to access"]),
    ("Baseline substance use and prior risk", ["Substance use before programme participation", "Baseline prevalence or reported use", "Age of initiation / prior initiation", "Frequency or intensity of prior use", "Prior risk and protective factors"]),
    ("Programme participation and exposure", ["Enrolment / number reached", "Participation rate / coverage", "Participation frequency and intensity", "Duration of participation", "Attendance, retention, and completion", "Type or level of programme exposure"]),
    ("Subsequent substance-use outcomes", ["Any subsequent substance use", "Subsequent alcohol use", "Subsequent cannabis use", "Subsequent use of other substances", "Initiation / new use after participation", "Frequency, intensity, or changes in use", "Substance-related harms or consequences"]),
    ("Follow-up and longitudinal linkage", ["Follow-up interval and timing", "Repeated measurement / pre-post data", "Individual-level linkage between participation and outcomes", "Cohort tracking and retention", "Attrition and missing follow-up data"]),
    ("Population and geographic differences", ["Age-group breakdowns", "Gender breakdowns", "Geographic breakdowns (national / region / LGA)", "Urban / rural or other population breakdowns", "Socioeconomic or other population-group differences"]),
    ("Context and potential confounding factors", ["Family and household context", "Peer and school environment", "Socioeconomic conditions", "Community and local context", "Other factors that may influence participation and substance use"]),
    ("Measurement and data-production context", ["Indicator and variable definitions", "Survey / administrative / programme measurement methods", "Sampling and population coverage", "Data collection period and frequency", "Data producer, collector, custodian, and access context"]),
    ("Other / not yet classified", ["Unclassified records"]),
]

# Deterministic display mapping from existing names, definitions and notes only.
TERMS = {
    "Types of prevention programmes": ("prevention programme", "prevention program", "programme type", "program type"),
    "Programme goals and target issues": ("programme goal", "program goal", "prevention", "target issue"),
    "Programme components / activities": ("programme activity", "program activity", "intervention", "component"),
    "Implementing organizations and delivery settings": ("implement", "delivery", "organization", "organisation", "school-based", "clinic", "setting"),
    "Programme availability and implementation period": ("availability", "implemented", "implementation period"),
    "Intended age groups / target population": ("youth", "adolescent", "under-18", "under 18", "age group", "population"),
    "Eligibility criteria": ("eligib", "criteria"), "Availability and geographic access": ("access", "geographic", "region", "lga", "national"),
    "Awareness, referral, and entry into programmes": ("awareness", "referral", "enrol", "entry into"), "Barriers to access": ("barrier", "access constraint"),
    "Substance use before programme participation": ("baseline", "before participation", "pre-programme", "pre-program"),
    "Baseline prevalence or reported use": ("prevalence", "reported use", "current use", "past-month", "past month"),
    "Age of initiation / prior initiation": ("initiation", "first use", "age at first"), "Frequency or intensity of prior use": ("frequency", "intensity", "days used"), "Prior risk and protective factors": ("risk factor", "protective factor"),
    "Enrolment / number reached": ("enrol", "number reached", "participants reached"), "Participation rate / coverage": ("participation rate", "coverage", "reach rate"),
    "Participation frequency and intensity": ("attendance frequency", "sessions attended", "intensity of participation"), "Duration of participation": ("duration", "months participated", "length of participation"),
    "Attendance, retention, and completion": ("attendance", "retention", "completion", "dropout"), "Type or level of programme exposure": ("programme exposure", "program exposure", "dose", "received intervention"),
    "Any subsequent substance use": ("subsequent use", "substance use after", "post-programme use", "post-program use"),
    "Subsequent alcohol use": ("alcohol", "drinking"), "Subsequent cannabis use": ("cannabis", "marijuana"), "Subsequent use of other substances": ("heroin", "cocaine", "tobacco", "drug market", "other substance"),
    "Initiation / new use after participation": ("new use", "initiation after", "started using"), "Frequency, intensity, or changes in use": ("frequency", "change in use", "reduction", "increase in use"), "Substance-related harms or consequences": ("harm", "consequence", "overdose", "health outcome"),
    "Follow-up interval and timing": ("follow-up", "follow up", "time point", "post-test"), "Repeated measurement / pre-post data": ("pre-post", "pre/post", "repeated measure", "longitudinal"),
    "Individual-level linkage between participation and outcomes": ("linked individual", "individual-level", "participant outcome"), "Cohort tracking and retention": ("cohort", "tracked", "retention"), "Attrition and missing follow-up data": ("attrition", "missing follow-up", "loss to follow-up"),
    "Age-group breakdowns": ("age group", "age-by", "age breakdown", "age-specific"), "Gender breakdowns": ("gender", "female", "male", "sex disaggregated"),
    "Geographic breakdowns (national / region / LGA)": ("geography", "geographic", "region", "lga", "district"), "Urban / rural or other population breakdowns": ("urban", "rural", "population group"), "Socioeconomic or other population-group differences": ("socioeconomic", "poverty", "income", "wealth"),
    "Family and household context": ("family", "household", "parent"), "Peer and school environment": ("peer", "school", "classroom"), "Socioeconomic conditions": ("socioeconomic", "poverty", "income", "wealth"), "Community and local context": ("community", "local context", "community-level"), "Other factors that may influence participation and substance use": ("confound", "risk factor", "protective factor"),
    "Indicator and variable definitions": ("indicator", "variable", "definition", "measure"), "Survey / administrative / programme measurement methods": ("survey", "administrative", "method", "measurement"), "Sampling and population coverage": ("sample", "sampling", "coverage", "denominator"), "Data collection period and frequency": ("collection period", "collection frequency", "observed_time", "observation period"), "Data producer, collector, custodian, and access context": ("producer", "collector", "custodian", "access"),
}


def _all(inventory, entity):
    return [*inventory["raw"][entity][0], *inventory["raw"][entity][1]]


def _val(row, *keys, default="Unknown"):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _unknown(value):
    return not value or str(value).strip().upper() in {"UNKNOWN", "N/A", "NOT RECORDED", "NOT SPECIFIED", "UNSPECIFIED"}


def _records(inventory):
    sources = {r.get("source_id", ""): r for r in inventory["sources"]}
    products = _all(inventory, "data_products")
    products_by_source = {}
    for product in products:
        products_by_source.setdefault(product.get("source_id", ""), []).append(product)
    result, seen = [], set()
    for entity in ("data_products", "indicators", "variables", "observations"):
        ids = {"data_products": ("data_product_id",), "indicators": ("indicator_id", "indicator_code"), "variables": ("variable_id",), "observations": ("observation_id",)}[entity]
        for source_row in _all(inventory, entity):
            sid = source_row.get("source_id", "")
            row = {**sources.get(sid, {}), **source_row}
            eid = _val(row, *ids, default="")
            kind = entity[:-1].upper()
            key = (kind, sid, eid or _val(row, "title"))
            if key in seen:
                continue
            seen.add(key)
            row.update(_entity_type=kind, _entity_id=eid or "Unknown", _source_id=sid or "Unknown")
            row["_source_family"] = _val(row, "source_family_id", default="") or sid or "Unknown"
            product = products_by_source.get(sid, [])
            row["_unit"] = _val(row, "data_product_id", default="") or (product[0].get("data_product_id") if len(product) == 1 else "") or row["_source_family"]
            observed = _val(row, "observed_time", "observation_period", "observation_year", default="")
            row["_observed"] = observed
            row["_years"] = sorted(set(re.findall(r"(?:19|20)\d{2}", observed)))
            fields = ("title", "data_product_name", "indicator_name", "indicator_code", "variable_name", "variable_definition", "indicator_definition", "definition_verbatim", "observation_definition_or_quote", "observation_note", "substance", "source_note", "mapping_reason", "layer_a_parent_name")
            text = " ".join(str(row.get(field, "")) for field in fields).casefold()
            row["_topics"] = [(parent, child) for parent, children in TOPICS[:-1] for child in children if any(term in text for term in TERMS.get(child, ()))] or [(TOPICS[-1][0], TOPICS[-1][1][0])]
            result.append(row)
    # Source documents without any linked product or measure stay discoverable.
    for sid, source in sources.items():
        if sid in {r["_source_id"] for r in result}:
            continue
        row = dict(source)
        row.update(_entity_type="SOURCE", _entity_id=sid, _source_id=sid, _source_family=_val(source, "source_family_id", default="") or sid, _unit=_val(source, "source_family_id", default="") or sid)
        row["_observed"] = _val(source, "observed_time", "observation_period", "observation_year", default="")
        row["_years"] = sorted(set(re.findall(r"(?:19|20)\d{2}", row["_observed"])))
        row["_topics"] = [(TOPICS[-1][0], TOPICS[-1][1][0])]
        result.append(row)
    return result


def render(inventory):
    st.markdown("# Research explorer")
    st.markdown("## Does prevention programme participation reduce subsequent substance use among under-18s?")
    st.caption("Explore the existing evidence inventory. Cell colour shows distinct data products or source units represented, not effectiveness or evidence quality.")
    records = _records(inventory)
    st.caption(f"{len(records)} existing inventory records are retained; unknown and unclassified records remain visible.")
    specs = [("Age group", ("original_age", "original_age_group")), ("Gender", ("gender", "sex")), ("Geography", ("geography_level", "geographic_level", "geographic_coverage")), ("Substance", ("substance",)), ("Data type", ("data_type", "measurement_method", "record_entity_type")), ("Source type", ("source_type", "document_type"))]
    selected = {}
    for col, (label, fields) in zip(st.columns(6), specs):
        vals = sorted({(v if not _unknown(v) else "Unknown") for v in (_val(r, *fields) for r in records)})
        selected[label] = col.multiselect(label, vals, default=vals, key=f"v1_explorer_{label}")
    visible = []
    for row in records:
        if all((_val(row, *fields) if not _unknown(_val(row, *fields)) else "Unknown") in selected[label] for label, fields in specs):
            visible.append(row)
    group_names = [p for p, _ in TOPICS]
    groups = st.multiselect("Research subtopic groups (clear a group to collapse it)", group_names, default=group_names, key="v1_explorer_topics")
    years = sorted({year for row in visible for year in row["_years"]})
    if any(not row["_years"] for row in visible) or not years:
        years.append("Unknown observation period")
    rows = [(p, child) for p, children in TOPICS if p in groups for child in children]
    labels = [f"{p}  ›  {child}" for p, child in rows]
    cell_records, z, hover = {}, [], []
    for parent, child in rows:
        values, tips = [], []
        for year in years:
            items = [r for r in visible if (parent, child) in r["_topics"] and (year in r["_years"] if year != "Unknown observation period" else not r["_years"])]
            cell_records[(parent, child, year)] = items
            count = len({r["_unit"] for r in items})
            values.append(count)
            tips.append(f"{parent} / {child}<br>Observation period: {year}<br>Distinct source/data-product units: {count}<br>Inventory records: {len(items)}<br>Click to inspect")
        z.append(values)
        hover.append(tips)
    customdata = [[[row_idx, col_idx] for col_idx in range(len(years))] for row_idx in range(len(rows))]
    fig = go.Figure(go.Heatmap(x=years, y=labels, z=z, customdata=customdata, text=z, texttemplate="%{text}", hovertext=hover, hovertemplate="%{hovertext}<extra></extra>", colorscale=[[0,"#111922"],[0.25,"#24434A"],[0.6,"#347E78"],[1,"#9AC6A2"]], colorbar={"title":"Distinct<br>source units"}, xgap=2, ygap=2))
    fig.update_layout(height=max(680, 30 * len(rows) + 140), paper_bgcolor="#050505", plot_bgcolor="#050505", font={"color":"#eeeeee"}, margin={"l":430,"r":30,"t":30,"b":60}, xaxis={"title":"Observation year","side":"bottom","type":"category"}, yaxis={"autorange":"reversed","automargin":True,"tickmode":"array","tickvals":labels,"tickfont":{"size":10},"ticktext":[label.replace("  ›  ", "<br>") for label in labels]})
    event = st.plotly_chart(fig, width="stretch", theme=None, key="v1_research_explorer_heatmap", on_select="rerun", selection_mode="points")
    st.caption(f"{len(visible)} inventory records shown. Publication year is separate and is never treated as observation year. Zero means no matching record is represented in the inventory under these filters; it does not establish that no data exist.")
    detail_cell = None
    selected_points = getattr(getattr(event, "selection", None), "points", []) or []
    if selected_points:
        point = selected_points[-1]
        row_idx = col_idx = None

        def valid_indices(row_value, col_value):
            return (
                isinstance(row_value, int) and not isinstance(row_value, bool)
                and isinstance(col_value, int) and not isinstance(col_value, bool)
                and 0 <= row_value < len(rows) and 0 <= col_value < len(years)
            )

        point_index = point.get("point_index")
        if isinstance(point_index, (list, tuple)) and len(point_index) >= 2:
            if valid_indices(point_index[0], point_index[1]):
                row_idx, col_idx = point_index[0], point_index[1]
        elif isinstance(point_index, int) and not isinstance(point_index, bool) and len(years):
            candidate_row, candidate_col = divmod(point_index, len(years))
            if valid_indices(candidate_row, candidate_col):
                row_idx, col_idx = candidate_row, candidate_col

        custom = point.get("customdata")
        if row_idx is None and isinstance(custom, (list, tuple)) and len(custom) >= 2:
            if valid_indices(custom[0], custom[1]):
                row_idx, col_idx = custom[0], custom[1]

        if row_idx is None:
            y_value, x_value = point.get("y"), point.get("x")
            if isinstance(y_value, str) and y_value in labels:
                row_idx = labels.index(y_value)
            elif isinstance(y_value, int) and not isinstance(y_value, bool) and 0 <= y_value < len(rows):
                row_idx = y_value

            if isinstance(x_value, str) and x_value in years:
                col_idx = years.index(x_value)
            elif isinstance(x_value, int) and not isinstance(x_value, bool):
                year_value = str(x_value)
                if year_value in years:
                    col_idx = years.index(year_value)
                elif 0 <= x_value < len(years):
                    col_idx = x_value

        if valid_indices(row_idx, col_idx):
            detail_cell = (row_idx, col_idx)
        else:
            st.caption(f"Selection could not be read — use Inspect cell below. Raw point: {point!r}")

    inspect_cols = st.columns([3, 2, 1])
    inspect_row = inspect_cols[0].selectbox("Subtopic", range(len(labels)), format_func=lambda idx: labels[idx], key="v1_explorer_inspect_subtopic")
    inspect_col = inspect_cols[1].selectbox("Observation year", range(len(years)), format_func=lambda idx: years[idx], key="v1_explorer_inspect_year")
    inspect_clicked = inspect_cols[2].button("Inspect cell", key="v1_explorer_inspect_button")
    if inspect_clicked:
        detail_cell = (inspect_row, inspect_col)

    if detail_cell is None:
        return
    row_idx, col_idx = detail_cell
    parent, child = rows[row_idx]
    year = years[col_idx]
    items = cell_records[(parent, child, year)]
    st.markdown(f"### {child} · {year}")
    if not items:
        st.info("No matching inventory record is represented in this cell.")
    for row in items:
        title = _val(row, "data_product_name", "indicator_name", "variable_name", "title", default="Untitled record")
        with st.expander(f"{title} · {row['_entity_type']} · {row['_source_id']}", expanded=True):
            fields = [("Entity type / ID", f"{row['_entity_type']} / {row['_entity_id']}"), ("Source", _val(row, "title")), ("Source type", _val(row, "source_type")), ("Data product", _val(row, "data_product_name", "data_product_id")), ("Observation period", row["_observed"] or "Unknown"), ("Publication year", _val(row, "publication_year", "publication_time")), ("Population / age", _val(row, "population_or_record_type", "original_age", "original_age_group")), ("Gender", _val(row, "gender", "sex")), ("Geography", _val(row, "geography_level", "geographic_level", "geographic_coverage")), ("Substance", _val(row, "substance")), ("Indicator / variable / observation ID", _val(row, "indicator_code", "indicator_id", "variable_id", "observation_id")), ("Definition / observation", _val(row, "indicator_definition", "variable_definition", "observation_definition_or_quote", "definition_verbatim")), ("Unit / denominator", f"{_val(row, 'unit')} / {_val(row, 'denominator')}"), ("Original topic IDs", f"{_val(row, 'layer_a_parent')} / {_val(row, 'operational_box_id')}"), ("Mapping / review status", f"{_val(row, 'mapping_status')} / {_val(row, 'review_status')}"), ("Existing notes / uncertainty", _val(row, "observation_note", "indicator_note", "source_note", "mapping_reason", "scope_guardrail")), ("Source reference", _val(row, "source_url_or_doi"))]
            for label, value in fields:
                st.markdown(f"**{label}:** {value}")
            url = _val(row, "source_url_or_doi", default="")
            if url and url != "Unknown":
                st.markdown(f"[Open source reference]({url})")
