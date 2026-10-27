"""Draft-only topic inventory and claim-to-measure preview.

Reads candidate CSVs only. It never reads the registry/tensor or writes data.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_DIRS = [ROOT / "data" / "preview", ROOT / "data" / "imports"]
PILOT_TARGETS = ["I009", "I013", "I014", "I015"]
PARKED_TARGETS = ["I002", "I011", "I019", "I022", "I023", "I024"]
TIME_BINS = ["2010-2014", "2015-2019", "2020-2022", "2023-2026", "OBSERVATION_PERIOD_UNKNOWN"]
RELATIONS = ["DIRECT_MATCH", "HARMONIZABLE", "PROXY", "CONCEPTUALLY_RELATED", "INCOMPATIBLE", "UNKNOWN_REQUIRES_REVIEW"]
RELATION_COLORS = {
    "DIRECT_MATCH": "#287B72", "HARMONIZABLE": "#4B918C", "PROXY": "#B58B48",
    "CONCEPTUALLY_RELATED": "#B87942", "INCOMPATIBLE": "#A34D42", "UNKNOWN_REQUIRES_REVIEW": "#454B50",
}
INVENTORY_COLORS = {1: "#4B918C", 2: "#B58B48", 3: "#A34D42"}
DRAFT_BANNER = "DRAFT PREVIEW - NOT HUMAN REVIEWED - CANDIDATE DATA ONLY - DO NOT PRESENT AS APPROVED EVIDENCE"
SCOPE = "Existing pilot claims: I009, I013, I014, I015. Parked targets are not no-gap findings, especially I002 cannabis. The four memo cases are proposed and NOT YET IMPORTED. Inventory density is not claim fit; a dense box can still fail to answer a causal question. AL024 remains NOT LOCATED / GAP. No national-to-LGA copying, WENDU age-by-substance joins, or conversion of arrests/seizures/activity counts into prevalence/effects."

TOPICS = [
    (1, "Substance-specific use and patterns"),
    (2, "Substance-related health outcomes and harms"),
    (3, "Treatment, care, and service access"),
    (4, "Prevention policies and planned activities"),
    (5, "Prevention programme delivery, reach, participation, and dose"),
    (6, "Post-participation outcomes and follow-up"),
    (7, "Enforcement and supply-suppression records"),
    (8, "Social, livelihood, risk, and protective factors"),
    (9, "Cross-border flows or illicit-finance evidence (only if actually measured)"),
    (10, "Data production, indicator governance, and access restrictions"),
]
INDICATOR_TOPIC_PREFIXES = [
    ("SUBSTANCE_PREVALENCE_", 1), ("TREATMENT_", 3),
    ("PREVENTION_PROGRAM_AVAILABILITY", 4), ("PREVENTION_COVERAGE", 5),
    ("PREVENTION_PARTICIPATION_INTENSITY", 5), ("SUBSEQUENT_SUBSTANCE_USE_OUTCOME", 6),
    ("CROSS_BORDER_DRUG_FLOW", 9), ("DRUG_SEIZURE_", 7),
    ("DRUG_RELATED_CASES_ARRESTS", 7), ("DATA_SYSTEM_AVAILABILITY", 10),
]
VARIABLE_TOPICS = {
    "V001": 1, "V002": 1, "V003": 1, "V016": 1,
    "V005": 2, "V007": 2,
    "V004": 7, "V006": 7, "V008": 7, "V009": 7,
    "V010": 10, "V011": 10, "V012": 10,
    "V013": 5, "V014": 6,
}

# These are question templates supplied in the concept-box memo, not observations.
PROPOSED_CASES = [
    {
        "key": "MEMO_CASE_1", "label": "Case 1 - Descriptive: current tobacco use in school-going minors",
        "question": "Among school-going adolescents aged 13-15 in The Gambia, what was the prevalence of current tobacco use under the GYTS 2017 survey definition?",
        "population": "School-going adolescents aged 13-15; not every minor in The Gambia.",
        "substance": "Tobacco only; not a proxy for cannabis, Kush, or other illicit drugs.",
        "observation_period": "2017 survey observation year; not metadata-page creation year.",
        "outcome": "Survey-defined current tobacco use; item wording and numerator/denominator require questionnaire/codebook review.",
        "unit": "UNKNOWN until the questionnaire/estimate definition is checked.",
        "denominator": "UNKNOWN until the questionnaire/codebook is checked.",
        "geography": "The Gambia; school-going sample only.",
        "method": "GYTS 2017 survey definition; exact item and estimate method require review.",
        "can_support": "A descriptive measure for this school-going age group and tobacco, once item definition and estimate are verified.",
        "cannot_support": "Illicit-drug prevalence; non-school-going minors; all-under-18 prevalence; prevention effectiveness; or a 2026 trend without comparable waves.",
        "source": "WHO NCD Microdata Repository, Global Youth Tobacco Survey 2017, Gambia",
        "url": "https://extranet.who.int/ncdsmicrodata/index.php/catalog/776",
    },
    {
        "key": "MEMO_CASE_2", "label": "Case 2 - Descriptive administrative outcome: recorded drug-related arrests among minors",
        "question": "How many people aged 17 and below were recorded as arrested for drug-related offences in each Gambian administrative region during 2023?",
        "population": "Arrestees aged 17 and below; preserve the WENDU table's wording.",
        "substance": "Drug-related offences aggregated; the age-by-region table does not identify substance for each minor.",
        "observation_period": "Calendar year 2023.",
        "outcome": "Recorded arrestee count by region; not prevalence or self-reported use.",
        "unit": "Recorded arrestee count.",
        "denominator": "UNKNOWN; no population denominator is asserted by this count question.",
        "geography": "Each Gambian administrative region, using the table's own labels.",
        "method": "WENDU 2023 report table; exact extraction and table labels require review.",
        "can_support": "The recorded geographical distribution of arrest events/arrestees as reported.",
        "cannot_support": "Youth-use prevalence; substance-specific minor arrests; or a causal effect of prevention. Separate age-by-region and substance tables cannot be joined without a supplied cross-tab or linked records.",
        "source": "ECOWAS, Fourth WENDU Report: Statistics and Trends on Illicit Drug Use and Supply (2023), The Gambia section, pages 62-64",
        "url": "https://ecowas.int/wp-content/uploads/2024/10/EN-Rev-Final-Updated-WENDU-Report-2023-Final-Copy.pdf",
    },
    {
        "key": "MEMO_CASE_3", "label": "Case 3 - Measurement audit: Banjul school pilot and a minors-only estimate",
        "question": "In the all-boys senior-secondary-school pilot in Banjul Area Council, does the available measurement record support a separately reported lifetime cannabis-use estimate for respondents younger than 18?",
        "population": "Target subgroup: respondents under 18 at the named pilot school; subgroup availability must be verified, not inferred from 'students'.",
        "substance": "Cannabis, separate from tobacco and alcohol.",
        "observation_period": "Lifetime use at survey date; fieldwork/observation date UNKNOWN, not replaced by 2025 publication year.",
        "outcome": "Binary lifetime cannabis-use response and its subgroup denominator.",
        "unit": "UNKNOWN pending full-text/data review.",
        "denominator": "Under-18 respondent denominator UNKNOWN; verify subgroup table or authorized microdata.",
        "geography": "Banjul Area Council, named single-school pilot; not a national or representative regional sample.",
        "method": "Adapted WHO student drug-use questionnaire per article abstract; full-text method needs review.",
        "can_support": "Candidate source for questionnaire, broad substance list, and an all-sample descriptive result, subject to full-text review.",
        "cannot_support": "From the abstract alone: minor-only or national prevalence, representative regional comparison, or causal prevention effect.",
        "source": "Jallow et al., Drug Abuse among Senior Secondary School Students in Banjul Area Council Zone, The Gambia - A Pilot Study (2025), DOI 10.33425/2639-8451.1056",
        "url": "https://www.scivisionpub.com/journals/addiction-research/articles/drug-abuse-among-senior-secondary-school-students-in-banjul-area-council-zone-the-gambia-a-pilot-study",
    },
    {
        "key": "MEMO_CASE_4", "label": "Case 4 - Causal: youth-led prevention initiative and later use",
        "question": "Among participants confirmed to be younger than 18 in the DLEAG-UNDP youth-led prevention initiative, did participation reduce self-reported past-30-day Kush use at six months versus otherwise comparable nonparticipants?",
        "population": "Actual participants under 18; age eligibility/roster must be verified because the launch report says 'youth' without defining ages.",
        "substance": "Kush as a proposed specific outcome; the launch article does not establish it as the programme's sole/intended endpoint.",
        "observation_period": "Launch reported 27 March 2026; proposed fixed six-month follow-up from each participant's actual exposure date. Follow-up data are not asserted to exist.",
        "outcome": "Individual past-30-day self-reported Kush use at baseline and follow-up, compared with a credible comparison group.",
        "unit": "Individual binary self-report; aggregate effect measure UNKNOWN.",
        "denominator": "Participants under 18 and comparable nonparticipants; exact counts UNKNOWN.",
        "geography": "Programme sites UNKNOWN; no local or regional distribution inferred from launch coverage.",
        "method": "Proposed comparative follow-up evaluation; no outcome dataset reported.",
        "can_support": "The reported launch of a named initiative with DLEAG and UNDP involvement only.",
        "cannot_support": "Reach among minors, change in use, or programme impact. Participant-only change is insufficient for causal identification.",
        "source": "The Standard, DLEAG, UNDP launch youth-led drive to tackle drug abuse (2 April 2026)",
        "url": "https://standard.gm/dleag-undp-launch-youth-led-drug-prevention/",
    },
]

EMPTY_STATES = {
    "NOT_SEARCHED", "SEARCH_INCOMPLETE", "SEARCHED_NO_DIRECT_EVIDENCE_FOUND",
    "RESTRICTED_ACCESS", "NOT_REPORTED", "NOT_APPLICABLE", "UNKNOWN_REQUIRES_REVIEW",
}


def load_csv(filename):
    for directory in DATA_DIRS:
        path = directory / filename
        if path.exists():
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle)), str(path.relative_to(ROOT))
    return [], None


def norm(value):
    if value is None or not str(value).strip():
        return "UNKNOWN"
    return str(value).strip()


def observation_time_bin(raw_value):
    match = re.search(r"\d{4}", norm(raw_value))
    if not match:
        return TIME_BINS[-1]
    year = int(match.group(0))
    for label, low, high in ((TIME_BINS[0], 2010, 2014), (TIME_BINS[1], 2015, 2019), (TIME_BINS[2], 2020, 2022), (TIME_BINS[3], 2023, 2026)):
        if low <= year <= high:
            return label
    return None


def classify_empty_state(*raw_values):
    raw = " | ".join(norm(v) for v in raw_values).upper()
    if "NOT_APPLICABLE" in raw or "NOT APPLICABLE" in raw:
        return "NOT_APPLICABLE"
    if "NOT_SEARCHED" in raw or "NOT SEARCHED" in raw:
        return "NOT_SEARCHED"
    if "SEARCHED_NO_DIRECT_EVIDENCE_FOUND" in raw:
        return "SEARCHED_NO_DIRECT_EVIDENCE_FOUND"
    if "RESTRICTED_ACCESS" in raw or "RESTRICTED ACCESS" in raw or "RESTRICTED" in raw:
        return "RESTRICTED_ACCESS"
    if "UNKNOWN_NOT_REPORTED" in raw or "NOT_REPORTED" in raw or "NO REPORT" in raw:
        return "NOT_REPORTED"
    if "NOT_EXHAUSTIVE" in raw or "SEARCH_INCOMPLETE" in raw or "SEARCH INCOMPLETE" in raw:
        return "SEARCH_INCOMPLETE"
    return "UNKNOWN_REQUIRES_REVIEW"


def topic_for_indicator(row):
    code = norm(row.get("indicator_code"))
    for prefix, topic_id in INDICATOR_TOPIC_PREFIXES:
        if code.startswith(prefix):
            return topic_id
    # Institutional compliance ratings are not measured illicit-finance flows.
    return None


def make_measurements(tables, products_by_source, product_file_available):
    measures = []
    unmapped = []
    observations_by_variable = defaultdict(list)
    for obs in tables["observations.csv"]:
        observations_by_variable[norm(obs.get("variable_id"))].append(obs)

    def product_link(source_id):
        if source_id == "UNKNOWN":
            return [], [], "SOURCE_ID_UNKNOWN"
        found = products_by_source.get(source_id, [])
        if len(found) == 1 and norm(found[0].get("data_product_id")) != "UNKNOWN":
            product = found[0]
            return [norm(product.get("data_product_id"))], [norm(product.get("data_product_name"))], "EXACT_SOURCE_ID_UNIQUE_PRODUCT"
        if len(found) > 1:
            return [], [], "AMBIGUOUS_PRODUCTS_FOR_SOURCE_ID"
        return [], [], "DATA_PRODUCTS_CSV_MISSING" if not product_file_available else "NO_DATA_PRODUCT_LINK"

    for row in tables["indicators.csv"]:
        iid = norm(row.get("indicator_id"))
        source_id = norm(row.get("source_id"))
        if iid == "UNKNOWN" or source_id == "UNKNOWN":
            if iid != "UNKNOWN":
                unmapped.append({"record": iid, "type": "TARGET/INDICATOR ROW NOT LOADED AS AN OBSERVED MEASURE", "reason": "source_id is UNKNOWN"})
            continue
        topic_id = topic_for_indicator(row)
        product_ids, product_names, product_status = product_link(source_id)
        record = {
            "key": f"indicator:{iid}", "kind": "indicator", "id": iid,
            "label": f"{iid} | {norm(row.get('indicator_code'))}", "aliases": [iid],
            "topic_id": topic_id, "source_id": source_id, "title": norm(row.get("title")),
            "observation_year": norm(row.get("observation_year")), "periods": [norm(row.get("observation_year"))],
            "population": norm(row.get("original_age_group")), "substance": norm(row.get("substance")),
            "outcome": norm(row.get("definition_verbatim")) if norm(row.get("definition_verbatim")) != "UNKNOWN" else norm(row.get("target_definition")),
            "unit": norm(row.get("unit")), "denominator": norm(row.get("denominator")),
            "geography": norm(row.get("geographic_level")), "method": "UNKNOWN",
            "can_support": "UNKNOWN; candidate indicator is not a verified observation or claim fit.",
            "cannot_support": norm(row.get("indicator_note")), "product_ids": product_ids,
            "product_names": product_names, "product_link_status": product_status,
            "source_status": norm(row.get("review_status")), "observation_ids": [], "raw_row": row,
        }
        if topic_id is None:
            unmapped.append({"record": iid, "type": "OBSERVED INDICATOR CANDIDATE", "reason": "No topic mapping in the current controlled preview taxonomy; not forced into a parent."})
        measures.append(record)

    for row in tables["variables.csv"]:
        vid = norm(row.get("variable_id"))
        if vid == "UNKNOWN":
            unmapped.append({"record": "UNKNOWN VARIABLE ID", "type": "VARIABLE ROW", "reason": "ID is missing"})
            continue
        topic_id = VARIABLE_TOPICS.get(vid)
        source_id = norm(row.get("source_id"))
        product_ids, product_names, product_status = product_link(source_id)
        linked_observations = observations_by_variable.get(vid, [])
        period_groups = defaultdict(list)
        if linked_observations:
            for obs in linked_observations:
                period_groups[norm(obs.get("observation_year"))].append(obs)
        else:
            period_groups[norm(row.get("observation_year"))] = []
        record = {
            "key": f"variable:{vid}", "kind": "variable", "id": vid,
            "label": f"{vid} | {norm(row.get('variable_name'))}", "aliases": [vid],
            "topic_id": topic_id, "source_id": source_id, "title": norm(row.get("title")),
            "observation_year": norm(row.get("observation_year")),
            "periods": list(period_groups) or [norm(row.get("observation_year"))],
            "population": norm(row.get("original_age_group")), "substance": "UNKNOWN",
            "outcome": norm(row.get("variable_definition")) if norm(row.get("variable_definition")) != "UNKNOWN" else norm(row.get("variable_name")),
            "unit": norm(row.get("unit")), "denominator": norm(row.get("denominator")),
            "geography": norm(row.get("geographic_level")), "method": norm(row.get("measurement_method")),
            "can_support": "UNKNOWN; suitability for a specific claim has not been established.",
            "cannot_support": "UNKNOWN unless an explicit linked alignment documents measurement loss.",
            "product_ids": product_ids, "product_names": product_names, "product_link_status": product_status,
            "source_status": norm(row.get("review_status")),
            "observation_ids": [norm(o.get("observation_id")) for o in linked_observations],
            "period_observations": dict(period_groups), "raw_row": row,
        }
        if topic_id is None:
            unmapped.append({"record": vid, "type": "VARIABLE CANDIDATE", "reason": "No topic mapping in the current controlled preview taxonomy; not forced into a parent."})
        if not product_ids:
            unmapped.append({"record": vid, "type": "VARIABLE -> DATA PRODUCT", "reason": product_status})
        measures.append(record)

    known_variable_ids = {m["id"] for m in measures if m["kind"] == "variable"}
    for obs in tables["observations.csv"]:
        vid = norm(obs.get("variable_id"))
        if vid not in known_variable_ids:
            unmapped.append({"record": norm(obs.get("observation_id")), "type": "ORPHAN OBSERVATION", "reason": f"variable_id {vid} does not resolve to a loaded variables.csv row"})
    return measures, unmapped


def claim_boxes(tables):
    by_id = {norm(row.get("indicator_id")): row for row in tables["indicators.csv"]}
    existing = []
    for target_id in PILOT_TARGETS:
        row = by_id.get(target_id, {})
        existing.append({
            "key": target_id, "id": target_id,
            "label": f"{target_id} | {norm(row.get('indicator_code'))}",
            "question": norm(row.get("target_definition")),
            "population": norm(row.get("original_age_group")), "substance": norm(row.get("substance")),
            "observation_period": norm(row.get("observation_year")), "outcome": norm(row.get("target_definition")),
            "unit": norm(row.get("unit")), "denominator": norm(row.get("denominator")),
            "geography": norm(row.get("target_geography")), "method": "UNKNOWN",
            "can_support": norm(row.get("target_definition")), "cannot_support": norm(row.get("indicator_note")),
            "status": "EXISTING PILOT TARGET - NOT APPROVED",
            "source": norm(row.get("title")), "url": norm(row.get("source_url_or_doi")),
        })
    proposals = []
    for case in PROPOSED_CASES:
        proposals.append({
            "key": case["key"], "id": case["key"], "label": case["label"], "question": case["question"],
            **{k: case[k] for k in ("population", "substance", "observation_period", "outcome", "unit", "denominator", "geography", "method", "can_support", "cannot_support", "source", "url")},
            "status": "NOT YET IMPORTED - PROPOSED CASE; NO MEASURE PAIR INFERRED",
        })
    return existing + proposals


def index_measure_aliases(measures):
    aliases = defaultdict(list)
    for measure in measures:
        for alias in measure["aliases"]:
            aliases[alias].append(measure["key"])
    return aliases


def resolve_alignment_measure(raw_label, alias_index):
    keys = alias_index.get(norm(raw_label), [])
    if len(keys) == 1:
        return keys[0], "EXACT_MEASURE_ID"
    return None, "UNMAPPED / REVIEW_REQUIRED"


def raw_alignment_key(raw_label):
    return f"raw-alignment:{norm(raw_label)}"


def empty_state_observation(row):
    raw = " ".join([norm(row.get("value")), norm(row.get("observation_note")), norm(row.get("observation_definition_or_quote"))])
    return classify_empty_state(raw)


def empty_state_tables(tables):
    states = []
    for row in tables["search_runs.csv"]:
        states.append({
            "record": norm(row.get("search_run_id")), "type": "SEARCH RUN",
            "state": classify_empty_state(row.get("run_status"), row.get("access_failures")),
            "result_count_state": classify_empty_state(row.get("returned_count"), row.get("count_note")),
            "raw_status": norm(row.get("run_status")), "raw_count": norm(row.get("returned_count")),
            "detail": norm(row.get("access_failures")),
        })
    for row in tables["observations.csv"]:
        state = empty_state_observation(row)
        if state != "UNKNOWN_REQUIRES_REVIEW":
            states.append({"record": norm(row.get("observation_id")), "type": "OBSERVATION", "state": state,
                           "result_count_state": "UNKNOWN_REQUIRES_REVIEW", "raw_status": norm(row.get("observation_note")),
                           "raw_count": "UNKNOWN", "detail": norm(row.get("observation_definition_or_quote"))})
    for row in tables["sources.csv"]:
        state = classify_empty_state(row.get("access_status"), row.get("source_note"))
        if state != "UNKNOWN_REQUIRES_REVIEW":
            states.append({"record": norm(row.get("source_id")), "type": "SOURCE ACCESS", "state": state,
                           "result_count_state": "UNKNOWN_REQUIRES_REVIEW", "raw_status": norm(row.get("access_status")),
                           "raw_count": "UNKNOWN", "detail": norm(row.get("source_note"))})
    for row in tables["gap_claims.csv"]:
        state = classify_empty_state(row.get("claim_status"), row.get("evidence_quote"), row.get("claim_interpretation"))
        states.append({"record": norm(row.get("gap_claim_id")), "type": "SOURCE-REPORTED GAP CLAIM",
                       "state": state, "result_count_state": "UNKNOWN_REQUIRES_REVIEW",
                       "raw_status": norm(row.get("claim_status")), "raw_count": "UNKNOWN",
                       "detail": norm(row.get("claim_interpretation"))})
    for row in tables["data_products.csv"]:
        state = classify_empty_state(row.get("extraction_state"), row.get("access_status"))
        if state != "UNKNOWN_REQUIRES_REVIEW":
            states.append({"record": norm(row.get("data_product_id")), "type": "DATA PRODUCT",
                           "state": state, "result_count_state": "UNKNOWN_REQUIRES_REVIEW",
                           "raw_status": norm(row.get("extraction_state")), "raw_count": "UNKNOWN",
                           "detail": norm(row.get("data_product_name"))})
    return states


def record_details(row):
    parts = [
        f"Measure: {row.get('observed_indicator_or_variable') or 'UNKNOWN'}",
        f"Relationship: {row.get('relationship_class') or 'UNKNOWN_REQUIRES_REVIEW'}",
        f"Reason: {row.get('relationship_reason') or 'UNKNOWN'}",
        f"Measurement loss: {row.get('measurement_loss') or 'UNKNOWN'}",
        f"Source title: {row.get('title') or 'UNKNOWN'}",
        f"Observation year (raw): {row.get('observation_year') or 'UNKNOWN'}",
        f"Original age: {row.get('original_age_group') or 'UNKNOWN'}",
        f"Geography: {row.get('geographic_level') or 'UNKNOWN'}",
    ]
    if norm(row.get("alignment_id")) == "AL024":
        parts.insert(2, "DISPOSITION: NOT LOCATED / GAP; not direct evidence")
    return "<br>".join(parts)


def banner(view_name):
    st.markdown(
        f"<div style='border:2px solid #B87942;padding:16px 18px;margin:0 0 12px 0;"
        f"background:#15110d;color:#f2c98c;font:700 18px/1.4 monospace'>{DRAFT_BANNER}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**{SCOPE}**")
    st.caption(f"{view_name} / candidate CSVs only / no registry or approved tensor access")


def render_unmapped_lane(rows, state_rows, title):
    st.subheader("UNMAPPED / REVIEW_REQUIRED")
    st.caption(title)
    unique_rows=[]; seen=set()
    for row in rows:
        key=tuple(sorted((str(k),str(v)) for k,v in row.items()))
        if key not in seen:
            seen.add(key); unique_rows.append(row)
    st.markdown(f"**Unmapped/review-required records: {len(unique_rows)}**")
    if unique_rows:
        st.dataframe(unique_rows, hide_index=True, width="stretch")
    else:
        st.info("No unmapped rows were constructed from the loaded files. Missing files are not treated as proof of absence.")
    st.markdown("**Explicit empty/search/access states supported by loaded CSV fields**")
    st.caption("NOT_SEARCHED is shown only if explicitly recorded; a missing search row is not converted into NOT_SEARCHED. Other unsupported states remain UNKNOWN_REQUIRES_REVIEW.")
    if state_rows:
        st.dataframe(state_rows, hide_index=True, width="stretch")
    else:
        st.info("No explicit empty-state rows were available in the loaded CSVs.")


def build_inventory(measures, tables, product_file_available, alignments, alias_index):
    topic_names = dict(TOPICS)
    child_rows = []
    measure_time_products = defaultdict(set)
    measure_time_details = defaultdict(list)
    unmapped = []
    linked_product_ids = set()
    for measure in measures:
        fits = []
        for alignment in alignments:
            key, _ = resolve_alignment_measure(alignment.get("observed_indicator_or_variable"), alias_index)
            if key == measure["key"]:
                fits.append(f"{norm(alignment.get('target_indicator_id'))}: {norm(alignment.get('relationship_class'))}")
        measure["claim_fit_badge"] = "; ".join(fits) if fits else "UNKNOWN_REQUIRES_REVIEW - no exact alignment link"
        measure["topic_name"] = topic_names.get(measure.get("topic_id"), "UNMAPPED / REVIEW_REQUIRED")
        measure["period_bins"] = []
        obs_by_period = measure.get("period_observations", {})
        if obs_by_period:
            for period_raw, obs_rows in obs_by_period.items():
                measure["period_bins"].append((period_raw, observation_time_bin(period_raw), obs_rows))
        else:
            for period_raw in measure.get("periods", [measure.get("observation_year", "UNKNOWN")]):
                measure["period_bins"].append((period_raw, observation_time_bin(period_raw), []))
        child_rows.append({
            "parent": measure["topic_name"], "child_measure": measure["label"],
            "topic_mapping_status": "RULE_DERIVED FROM EXACT INDICATOR CODE / VARIABLE ID" if measure.get("topic_id") is not None else "UNMAPPED / REVIEW_REQUIRED",
            "source_title": measure["title"], "source_id": measure["source_id"],
            "population": measure["population"], "substance": measure["substance"],
            "observation_period_raw": "; ".join(dict.fromkeys(p[0] for p in measure["period_bins"])) or "UNKNOWN",
            "outcome": measure["outcome"], "unit": measure["unit"], "denominator": measure["denominator"],
            "geography": measure["geography"], "method": measure["method"],
            "what_it_can_support": measure["can_support"], "what_it_cannot_support": measure["cannot_support"],
            "data_product_ids": "; ".join(measure["product_ids"]) or "UNKNOWN",
            "data_products": "; ".join(measure["product_names"]) or "UNKNOWN",
            "claim_fit_badge": measure["claim_fit_badge"], "candidate_status": measure["source_status"],
            "observation_ids": "; ".join(measure["observation_ids"]) or "UNKNOWN",
        })
        if measure.get("topic_id") is None:
            unmapped.append({"record": measure["id"], "type": measure["kind"].upper(), "reason": "No exact topic mapping; retained in review lane."})
        if not measure["product_ids"]:
            unmapped.append({"record": measure["id"], "type": "MEASURE -> DATA PRODUCT", "reason": measure["product_link_status"]})
        for period_raw, time_bin, obs_rows in measure["period_bins"]:
            if time_bin is None:
                unmapped.append({"record": measure["id"], "type": "OBSERVATION PERIOD OUTSIDE DISPLAYED BINS", "reason": f"Raw observation_year retained: {period_raw}"})
                continue
            if measure.get("topic_id") is None:
                continue
            key = (measure["key"], time_bin)
            measure_time_details[key].append({"measure": measure, "raw_period": period_raw, "observation_rows": obs_rows})
            for product_id in measure["product_ids"]:
                measure_time_products[key].add(product_id)
                linked_product_ids.add(product_id)

    # Keep all 10 parents visible even if the loaded CSVs have no mapped child.
    for topic_id, topic_name in TOPICS:
        if not any(m.get("topic_id") == topic_id for m in measures):
            child_rows.append({
                "parent": topic_name, "child_measure": "No mapped child measure in loaded CSVs",
                "topic_mapping_status": "UNKNOWN_REQUIRES_REVIEW",
                "population": "UNKNOWN", "substance": "UNKNOWN", "observation_period_raw": "UNKNOWN",
                "outcome": "UNKNOWN", "unit": "UNKNOWN", "denominator": "UNKNOWN", "geography": "UNKNOWN",
                "method": "UNKNOWN", "what_it_can_support": "UNKNOWN", "what_it_cannot_support": "UNKNOWN",
                "data_product_ids": "UNKNOWN", "data_products": "UNKNOWN",
                "claim_fit_badge": "UNKNOWN_REQUIRES_REVIEW", "candidate_status": "UNKNOWN_REQUIRES_REVIEW",
                "observation_ids": "UNKNOWN",
            })

    for product in tables["data_products.csv"]:
        product_id = norm(product.get("data_product_id"))
        if product_id != "UNKNOWN" and product_id not in linked_product_ids:
            unmapped.append({"record": product_id, "type": "DATA PRODUCT", "reason": "No loaded operational measure is linked by exact source_id; product retained for review."})
    product_source_ids = {norm(row.get("source_id")) for row in tables["data_products.csv"]}
    for source in tables["sources.csv"]:
        sid = norm(source.get("source_id"))
        if sid not in product_source_ids:
            unmapped.append({"record": sid, "type": "SOURCE WITHOUT DATA PRODUCT", "reason": f"{norm(source.get('title'))}; no exact data_products.csv source_id link."})
    for alignment in alignments:
        key, method = resolve_alignment_measure(alignment.get("observed_indicator_or_variable"), alias_index)
        if key is None:
            unmapped.append({"record": norm(alignment.get("alignment_id")), "type": "RAW ALIGNMENT VALUE", "reason": f"{method}: {norm(alignment.get('observed_indicator_or_variable'))}; target {norm(alignment.get('target_indicator_id'))}."})
    if not product_file_available:
        unmapped.append({"record": "data_products.csv", "type": "MISSING PREVIEW INPUT", "reason": "Distinct product/system density cannot be calculated; document count is not used as a substitute."})
    for obs in tables["observations.csv"]:
        vid = norm(obs.get("variable_id"))
        if vid == "UNKNOWN" or not any(m["kind"] == "variable" and m["id"] == vid for m in measures):
            unmapped.append({"record": norm(obs.get("observation_id")), "type": "OBSERVATION", "reason": f"Unlinked variable_id {vid}; not assigned to a topic."})
    return child_rows, measure_time_products, measure_time_details, unmapped


def render_view_a(tables, measures, alignments, alias_index, product_file_available, state_rows, measure_unmapped):
    st.markdown("Layer A parents group Layer B operational measures. Heat counts distinct linked `data_product_id` values across all child measures in each parent/time bin, never documents and never claim fit. A separate claim-fit badge is shown in the box table.")
    child_rows, measure_time_products, measure_time_details, unmapped = build_inventory(measures, tables, product_file_available, alignments, alias_index)
    unmapped.extend(measure_unmapped)
    y_labels=[]; z=[]; cell_text=[]; hover=[]
    topic_child_list=defaultdict(list)
    for measure in measures:
        if measure.get("topic_id") is not None:
            topic_child_list[measure["topic_id"]].append(measure)
    for topic_id, topic_name in TOPICS:
        children=topic_child_list.get(topic_id, [])
        y_labels.append(f"{topic_id:02d} | {topic_name}")
        row_z=[]; row_text=[]; row_hover=[]
        for time_bin in TIME_BINS:
            details=[]; product_ids=set()
            for child in children:
                key=(child["key"],time_bin)
                details.extend(measure_time_details.get(key, []))
                product_ids.update(measure_time_products.get(key, set()))
            product_count=len(product_ids)
            if not children:
                value=0; label="UNKNOWN"
                status="UNKNOWN_REQUIRES_REVIEW - no child measure in loaded CSVs"
            elif not product_file_available or (details and product_count == 0):
                value=0; label="UNKNOWN"
                status="UNKNOWN_REQUIRES_REVIEW - product/system ID unavailable"
            elif product_count:
                value=min(product_count,3); label=f"{product_count} product(s)"
                status=f"INVENTORY_PRESENT - {product_count} distinct data product ID(s)"
                unknown_links=sum(1 for item in details if not item["measure"]["product_ids"])
                if unknown_links:
                    label += f" + {unknown_links} UNKNOWN link(s)"
                    status += f"; at least this many, with {unknown_links} unresolved product link(s)"
            else:
                value=0; label="UNKNOWN"
                status="UNKNOWN_REQUIRES_REVIEW - no topic/time-specific product state supplied"
            row_z.append(value); row_text.append(label)
            if details:
                detail_items=[]
                for item in details:
                    m=item["measure"]
                    detail_items.append(
                        f"Child: {m['label']}<br>Source: {m['title']} | source_id {m['source_id']}<br>Data product IDs: {', '.join(m['product_ids']) or 'UNKNOWN'}"
                        f"<br>Data products: {', '.join(m['product_names']) or 'UNKNOWN'}"
                        f"<br>Population: {m['population']}<br>Substance: {m['substance']}"
                        f"<br>Observation year (raw): {item['raw_period']}<br>Outcome: {m['outcome']}"
                        f"<br>Unit: {m['unit']}<br>Denominator: {m['denominator']}<br>Geography: {m['geography']}"
                        f"<br>Method: {m['method']}<br>Can support: {m['can_support']}<br>Cannot support: {m['cannot_support']}"
                        f"<br>Claim fit badge: {m['claim_fit_badge']}<br>Observation IDs: {', '.join(m['observation_ids']) or 'UNKNOWN'}"
                    )
                detail_html="<br><br>".join(detail_items)
            else:
                detail_html="No mapped child/product record for this topic/time cell. This UNKNOWN is not a no-evidence finding."
            row_hover.append(f"Parent: {topic_name}<br>Time: {time_bin}<br>Inventory state: {status}<br>Distinct product count: {product_count if product_count else 'UNKNOWN'}<br><br>{detail_html}")
        z.append(row_z); cell_text.append(row_text); hover.append(row_hover)
    colorscale=[[0,"#454B50"],[0.166,"#454B50"],[0.167,"#4B918C"],[0.5,"#4B918C"],[0.501,"#B58B48"],[0.833,"#B58B48"],[0.834,"#A34D42"],[1,"#A34D42"]]
    fig=go.Figure(go.Heatmap(x=TIME_BINS,y=y_labels,z=z,zmin=0,zmax=3,colorscale=colorscale,showscale=False,text=cell_text,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=2,ygap=2,connectgaps=False))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2","size":10},margin={"l":360,"r":35,"t":40,"b":95},height=max(580, len(y_labels)*50))
    fig.update_xaxes(tickangle=-15,gridcolor="#26333D")
    fig.update_yaxes(autorange="reversed",gridcolor="#26333D",automargin=True)
    st.plotly_chart(fig,width="stretch",theme=None,key="draft_topic_inventory")
    st.caption("Teal / amber / rust intensity = 1 / 2 / 3+ distinct linked product IDs. Charcoal UNKNOWN means the loaded CSVs do not establish a product count. Claim fit is not encoded in this heat. No national value is copied to an LGA; WENDU age-by-substance tables are not joined; arrests, seizures, and activity counts are not recast as prevalence or effects.")
    st.markdown("**Layer B operational boxes**")
    st.dataframe(child_rows,hide_index=True,width="stretch")
    state_summary = f"Layer A rows: {len(y_labels)} across 10 parents. Loaded CSVs: {', '.join(name for name,present in tables['available'].items() if present) or 'none'}. Distinct-product density source: data_products.csv {'available' if product_file_available else 'MISSING'}; source_id is used only when it resolves to exactly one known data_product_id; no document-count fallback."
    st.caption(state_summary)
    render_unmapped_lane(unmapped,state_rows,"Unmapped measures/products and unresolved links stay visible here; no row is dropped or forced into a topic.")


def render_view_b(tables, measures, claims, alignments, alias_index, state_rows, measure_unmapped):
    st.markdown("Only explicit alignment records create colored cells. Blank intersections mean no alignment row was supplied; they are not generated pairings, search results, or proof of absence.")
    raw_columns={}
    cell_rows=defaultdict(list)
    mapping_rows=[]
    active_claim_keys={claim["key"] for claim in claims}
    for row in alignments:
        raw=norm(row.get("observed_indicator_or_variable"))
        key,method=resolve_alignment_measure(raw,alias_index)
        if key is None:
            key=raw_alignment_key(raw)
            raw_columns.setdefault(key,{"key":key,"label":f"RAW | {raw}","raw":raw,"source_id":norm(row.get("source_id")),"title":norm(row.get("title")),"unmapped":True})
            mapping_rows.append({"alignment_id":norm(row.get("alignment_id")),"raw_observed":raw,"mapping":method,"claim":norm(row.get("target_indicator_id"))})
        target=norm(row.get("target_indicator_id"))
        if target in active_claim_keys:
            cell_rows[(target,key)].append(row)
    measure_columns=[{"key":m["key"],"label":m["label"],"measure":m,"unmapped":False} for m in measures]
    measure_columns.extend(raw_columns.values())
    # Include all measures in the matrix catalog, but leave unsupported claim/measure intersections empty.
    x_labels=[col["label"] for col in measure_columns]
    x_keys=[col["key"] for col in measure_columns]
    claim_labels=[claim["label"] for claim in claims]
    z=[]; text=[]; hover=[]
    for claim in claims:
        zr=[]; tr=[]; hr=[]
        for col in measure_columns:
            rows=cell_rows.get((claim["key"],col["key"]),[])
            if not rows:
                zr.append(None); tr.append(""); hr.append("")
                continue
            usable=[r for r in rows if not (norm(r.get("alignment_id"))=="AL024" and "not yet located" in norm(r.get("observed_indicator_or_variable")).lower())]
            has_not_located=any(norm(r.get("alignment_id"))=="AL024" and "not yet located" in norm(r.get("observed_indicator_or_variable")).lower() for r in rows)
            classes={norm(r.get("relationship_class")) for r in usable}
            relation=next(iter(classes)) if len(classes)==1 and next(iter(classes)) in RELATIONS else "UNKNOWN_REQUIRES_REVIEW"
            zr.append(RELATIONS.index(relation))
            if has_not_located and not usable:
                tr.append("NOT LOCATED / GAP")
            elif has_not_located:
                tr.append(f"{relation} + NOT LOCATED / GAP")
            elif len(classes)==1:
                tr.append(relation)
            else:
                tr.append("MULTIPLE / REVIEW_REQUIRED")
            claim_info=f"Claim: {claim['label']}<br>Status: {claim['status']}<br>Question: {claim['question']}"
            measure_info=f"Observed measure column: {col['label']}"
            hr.append(claim_info+"<br><br>"+measure_info+"<br><br>"+"<br><br>".join(record_details(r) for r in rows))
        z.append(zr); text.append(tr); hover.append(hr)
    palette=[]
    for i,name in enumerate(RELATIONS):
        lo=0 if i==0 else (i-0.5)/(len(RELATIONS)-1)
        hi=1 if i==len(RELATIONS)-1 else (i+0.5)/(len(RELATIONS)-1)
        palette.extend([[lo,RELATION_COLORS[name]],[hi,RELATION_COLORS[name]]])
    tick_labels=[label if len(label)<=32 else label[:31]+"..." for label in x_labels]
    fig=go.Figure(go.Heatmap(x=list(range(len(x_labels))),y=claim_labels,z=z,zmin=0,zmax=len(RELATIONS)-1,colorscale=palette,showscale=False,text=text,texttemplate="%{text}",hovertext=hover,hovertemplate="%{hovertext}<extra></extra>",xgap=2,ygap=2,connectgaps=False))
    fig.update_layout(paper_bgcolor="#0B1016",plot_bgcolor="#0A1119",font={"color":"#E8EEF2","size":9},margin={"l":390,"r":35,"t":40,"b":245},height=700)
    fig.update_xaxes(tickmode="array",tickvals=list(range(len(x_labels))),ticktext=tick_labels,tickangle=-45,gridcolor="#26333D")
    fig.update_yaxes(autorange="reversed",gridcolor="#26333D",automargin=True)
    st.plotly_chart(fig,width="stretch",theme=None,key="draft_claim_measure_matrix")
    st.caption(f"View B claim boxes: {len(claims)} (4 existing pilot targets + 4 memo cases). Relationship colors apply only to explicit alignment rows. Blank cells are unpaired, not inferred. Hover populated cells for reason and measurement loss; the full measure catalog below preserves long labels.")
    st.markdown("**Claim boxes and operational requirements**")
    st.dataframe([{k:claim[k] for k in ("label","status","question","population","substance","observation_period","outcome","unit","denominator","geography","method","can_support","cannot_support","source","url")} for claim in claims],hide_index=True,width="stretch")
    st.markdown("**All plausible observed-measure columns**")
    st.dataframe([{"column":col["label"],"entity_type":col["measure"]["kind"] if col.get("measure") else "RAW ALIGNMENT LABEL - UNMAPPED","source_id":col["measure"]["source_id"] if col.get("measure") else col.get("source_id"),"candidate_status":col["measure"]["source_status"] if col.get("measure") else "UNKNOWN_REQUIRES_REVIEW"} for col in measure_columns],hide_index=True,width="stretch")
    unmapped=list(measure_unmapped)
    for row in mapping_rows:
        unmapped.append({"record":row["alignment_id"],"type":"RAW ALIGNMENT VALUE","reason":f"{row['mapping']}: {row['raw_observed']} -> claim {row['claim']}"})
    for row in alignments:
        if norm(row.get("target_indicator_id")) not in active_claim_keys:
            unmapped.append({"record":norm(row.get("alignment_id")),"type":"ALIGNMENT OUTSIDE DISPLAYED CLAIMS","reason":f"target {norm(row.get('target_indicator_id'))}; raw measure {norm(row.get('observed_indicator_or_variable'))}; retained, not projected into an unrelated claim"})
    aligned_measure_keys={key for _,key in cell_rows}
    for measure in measures:
        if measure["key"] not in aligned_measure_keys:
            unmapped.append({"record":measure["id"],"type":"OBSERVED MEASURE WITHOUT EXPLICIT PILOT ALIGNMENT","reason":"Listed as a column; no relationship was inferred."})
    for claim in claims:
        if claim["key"].startswith("MEMO_CASE_"):
            unmapped.append({"record":claim["key"],"type":"PROPOSED CLAIM - NOT YET IMPORTED","reason":"No alignment is assigned to this proposed case; blank cells remain unpaired."})
    for target_id in PARKED_TARGETS:
        target=next((r for r in tables["indicators.csv"] if norm(r.get("indicator_id"))==target_id),None)
        if target:
            unmapped.append({"record":target_id,"type":"PARKED TARGET - NOT A NO-GAP FINDING","reason":norm(target.get("target_definition"))})
    render_unmapped_lane(unmapped,state_rows,"Raw unmatched labels, measures without an explicit pilot alignment, outside-scope alignments, and unimported claim proposals remain visible here.")


def render():
    filenames=["alignments.csv","indicators.csv","variables.csv","observations.csv","data_products.csv","sources.csv","gap_claims.csv","search_runs.csv","barriers.csv","search_candidates.csv","concept_boxes.csv","mapping.csv"]
    loaded={}; available={}
    for filename in filenames:
        loaded[filename],path=load_csv(filename)
        available[filename]=path is not None
    loaded["available"]=available
    if not loaded["alignments.csv"] and not loaded["indicators.csv"]:
        st.error("Draft preview unavailable: candidate alignments.csv and indicators.csv were not found in data/preview/ or data/imports/.")
        return
    products_by_source=defaultdict(list)
    for row in loaded["data_products.csv"]:
        products_by_source[norm(row.get("source_id"))].append(row)
    measures,measure_unmapped=make_measurements(loaded,products_by_source,available["data_products.csv"])
    aliases=index_measure_aliases(measures)
    claims=claim_boxes(loaded)
    states=empty_state_tables(loaded)
    view_a,view_b=st.tabs(["View A | Topic inventory","View B | Claim-measure audit"])
    with view_a:
        render_view_a(loaded,measures,loaded["alignments.csv"],aliases,available["data_products.csv"],states,measure_unmapped)
    with view_b:
        render_view_b(loaded,measures,claims,loaded["alignments.csv"],aliases,states,measure_unmapped)
    st.caption("Draft — candidate data only, not human reviewed.")
