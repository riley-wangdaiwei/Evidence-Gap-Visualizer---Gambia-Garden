import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st
import yaml

from components.dark_atlas import RELATION_COLORS, categorical_scale, matrix


ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "data" / "preview"
CANDIDATE_DIR = ROOT / "data" / "candidate_2026-10-31"
TIME_BINS = [
    "2010-2014",
    "2015-2019",
    "2020-2022",
    "2023-2026",
    "OBSERVATION_PERIOD_UNKNOWN",
]
ALIGNMENT_CLASSES = [
    "DIRECT_MATCH",
    "HARMONIZABLE",
    "PROXY",
    "CONCEPTUALLY_RELATED",
    "INCOMPATIBLE",
    "UNKNOWN_REQUIRES_REVIEW",
]
DISPLAY_COLORS = {
    **RELATION_COLORS,
    "NOT_ASSESSED": "#454B50",
    "NOT_APPLICABLE": "#26333D",
}

FIXED_SCOPE = [
    ("Project", "Gambia Evidence Gap Explorer"),
    ("Pilot", "Youth Drug Prevention in The Gambia"),
    (
        "Primary test claim",
        "Whether youth prevention programme participation reduces subsequent substance use among under-18s.",
    ),
    (
        "Geography",
        "The Gambia first; LGA/named border area only where the source explicitly reports it.",
    ),
    (
        "Population scope",
        "Inventory keeps relevant mixed-age/adult/age-unknown sources as context with an explicit scope label, never relabelled as under-18 evidence.",
    ),
    (
        "Time scope",
        "Observation period 2010-2026 for research/data, publication time kept separate; earlier laws/policies as historical context only.",
    ),
    (
        "Layer A",
        "10 fixed parents; Layer B operational boxes carry population, substance, observation period, outcome, unit, denominator, geography, method, can-support, and cannot-support.",
    ),
    (
        "Source frame",
        "Seed source list + logged search additions, not exhaustive; all counts candidate/pending review and search not exhaustive.",
    ),
]


def _read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _candidate_csv(entity):
    matches = sorted(CANDIDATE_DIR.glob(f"{entity}*.csv"))
    return matches[0] if matches else None


def _load_rows(entity):
    seed_path = SEED_DIR / f"{entity}.csv"
    seed = _read_csv(seed_path) if seed_path.is_file() else []
    candidate_path = _candidate_csv(entity) if CANDIDATE_DIR.is_dir() else None
    candidate = _read_csv(candidate_path) if candidate_path else []
    return seed, candidate


def _value(row, *keys, default="UNKNOWN"):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _is_unknown(value):
    return not value or value.strip().upper() in {"UNKNOWN", "N/A", "NOT RECORDED"}


def _merge_sources(seed_rows, candidate_rows):
    sources = []
    seen_ids = {}
    seen_urls = {}
    duplicate_rows = []
    for row in [*seed_rows, *candidate_rows]:
        source_id = _value(row, "source_id", default="")
        url = _value(row, "source_url_or_doi", default="")
        duplicate_of = None
        if source_id and source_id in seen_ids:
            duplicate_of = seen_ids[source_id]["source_id"]
            reason = "source_id"
        elif url and url.casefold() in seen_urls:
            duplicate_of = seen_urls[url.casefold()]["source_id"]
            reason = "source_url_or_doi"
        else:
            reason = ""
        if duplicate_of:
            duplicate_rows.append(
                {
                    "duplicate_source_id": source_id or "UNKNOWN",
                    "duplicate_url": url or "UNKNOWN",
                    "retained_source_id": duplicate_of,
                    "duplicate_key": reason,
                    "review_status": _value(row, "review_status"),
                }
            )
            continue
        sources.append(dict(row))
        if source_id:
            seen_ids[source_id] = row
        if url:
            seen_urls[url.casefold()] = row
    return sources, duplicate_rows


def load_inventory():
    entities = (
        "sources",
        "data_products",
        "indicators",
        "variables",
        "observations",
        "alignments",
        "barriers",
        "concept_boxes",
        "gap_claims",
        "data_production_audit",
        "mapping",
        "search_runs",
        "search_candidates",
    )
    raw = {}
    for entity in entities:
        raw[entity] = _load_rows(entity)

    seed_sources, candidate_sources = raw["sources"]
    sources, duplicate_sources = _merge_sources(seed_sources, candidate_sources)
    seed_boxes, candidate_boxes = raw["concept_boxes"]
    parents = [
        row
        for row in seed_boxes
        if row.get("box_type") == "layer_a_parent"
    ]
    return {
        "raw": raw,
        "sources": sources,
        "duplicate_sources": duplicate_sources,
        "source_aliases": {
            row["duplicate_source_id"]: row["retained_source_id"]
            for row in duplicate_sources
            if row["duplicate_source_id"] != "UNKNOWN"
        },
        "parents": parents,
        "candidate_loaded": CANDIDATE_DIR.is_dir(),
        "candidate_files": sorted(
            path.name for path in CANDIDATE_DIR.glob("*.csv")
        )
        if CANDIDATE_DIR.is_dir()
        else [],
    }


def _scope_panel():
    with st.expander("Fixed Method & Scope", expanded=False):
        for label, value in FIXED_SCOPE:
            st.markdown(f"**{label}:** {value}")


def _canonical_parent_maps(parents):
    by_name = {}
    by_code = {}
    ordered = []
    for row in parents:
        name = _value(row, "box_title", "layer_a_parent_name")
        code = _value(row, "layer_a_parent", "operational_box_id")
        ordered.append(name)
        by_name[name.casefold()] = name
        by_code[code.casefold()] = name
        parent_id = _value(row, "operational_box_id", default="")
        if parent_id:
            by_code[parent_id.casefold()] = name
    return ordered, by_name, by_code


def _parent_for_value(value, by_name, by_code):
    if not value:
        return None
    return by_name.get(value.casefold()) or by_code.get(value.casefold())


def _source_parent_assignments(inventory):
    ordered, by_name, by_code = _canonical_parent_maps(inventory["parents"])
    assignments = defaultdict(set)
    seed_sources, _ = inventory["raw"]["sources"]
    seed_mappings, _ = inventory["raw"]["mapping"]
    _, candidate_mappings = inventory["raw"]["mapping"]
    seed_ids = {row.get("source_id") for row in seed_sources}
    for row in seed_mappings:
        source_id = row.get("source_id", "")
        if source_id not in seed_ids:
            continue
        parent = _parent_for_value(
            _value(row, "layer_a_parent_name", default=""),
            by_name,
            by_code,
        ) or _parent_for_value(
            _value(row, "layer_a_parent", default=""), by_name, by_code
        )
        if parent:
            assignments[source_id].add(parent)
    for row in seed_sources:
        source_id = row.get("source_id", "")
        parent = _parent_for_value(
            _value(row, "layer_a_parent_name", default=""), by_name, by_code
        ) or _parent_for_value(
            _value(row, "layer_a_parent", default=""), by_name, by_code
        )
        if parent:
            assignments[source_id].add(parent)
    for duplicate in inventory["duplicate_sources"]:
        duplicate_id = duplicate["duplicate_source_id"]
        retained_id = duplicate["retained_source_id"]
        assignments[retained_id].update(assignments.get(duplicate_id, set()))

    candidate_ids = {
        row.get("source_id")
        for row in inventory["sources"]
        if str(row.get("source_id", "")).startswith("LLM_CAND_SOURCE_")
    }
    for row in candidate_mappings:
        source_id = row.get("source_id", "")
        if source_id not in candidate_ids:
            continue
        parent = _parent_for_value(
            _value(row, "layer_a_parent_name", default=""),
            by_name,
            by_code,
        ) or _parent_for_value(
            _value(row, "layer_a_parent", default=""), by_name, by_code
        )
        if parent:
            assignments[source_id].add(parent)
    return ordered, assignments


def _time_bin(source):
    observed = _value(source, "observed_time", "observation_year", default="")
    match = re.search(r"(?:19|20)\d{2}", observed)
    if not match:
        return TIME_BINS[-1]
    year = int(match.group(0))
    if 2010 <= year <= 2014:
        return TIME_BINS[0]
    if 2015 <= year <= 2019:
        return TIME_BINS[1]
    if 2020 <= year <= 2022:
        return TIME_BINS[2]
    if 2023 <= year <= 2026:
        return TIME_BINS[3]
    return TIME_BINS[-1]


def _document_rows(inventory):
    parents, assignments = _source_parent_assignments(inventory)
    parent_axis = [*parents, "UNMAPPED / REVIEW_REQUIRED"]
    records = []
    for source in inventory["sources"]:
        source_id = _value(source, "source_id")
        assigned = sorted(assignments.get(source_id, set()), key=parents.index)
        if not assigned:
            assigned = ["UNMAPPED / REVIEW_REQUIRED"]
        for parent in assigned:
            if parent not in parent_axis:
                parent = "UNMAPPED / REVIEW_REQUIRED"
        records.append(
            {
                **source,
                "source_id": source_id,
                "_parents": assigned,
                "_time_bin": _time_bin(source),
                "source_family": _value(
                    source, "source_family_id", default=""
                )
                or source_id,
            }
        )
    return records, parent_axis


def _product_records(inventory):
    seed_products, candidate_products = inventory["raw"]["data_products"]
    product_rows = [*seed_products, *candidate_products]
    source_by_id = {row.get("source_id"): row for row in inventory["sources"]}
    audit_rows = [
        *inventory["raw"]["data_production_audit"][0],
        *inventory["raw"]["data_production_audit"][1],
    ]
    audit_by_source = {}
    for row in audit_rows:
        audit_by_source.setdefault(row.get("source_id"), row)
    barriers = [
        *inventory["raw"]["barriers"][0],
        *inventory["raw"]["barriers"][1],
    ]
    barriers_by_source = defaultdict(list)
    for row in barriers:
        barriers_by_source[row.get("source_id")].append(row)

    products_by_source = defaultdict(list)
    product_seen = set()
    for product in product_rows:
        product_id = _value(product, "data_product_id", default="")
        key = (product.get("source_id", ""), product_id)
        if key in product_seen:
            continue
        product_seen.add(key)
        products_by_source[product.get("source_id", "")].append(product)

    output = []
    for source_id, source in source_by_id.items():
        alias_ids = [
            duplicate["duplicate_source_id"]
            for duplicate in inventory["duplicate_sources"]
            if duplicate["retained_source_id"] == source_id
        ]
        linked_ids = [source_id, *alias_ids]
        products = [
            product
            for linked_id in linked_ids
            for product in products_by_source.get(linked_id, [])
        ]
        if not products:
            products = [{}]
        for product in products:
            product_source_id = _value(product, "source_id", default=source_id)
            audit = audit_by_source.get(product_source_id) or audit_by_source.get(source_id, {})
            barrier_text = "; ".join(
                _value(item, "barrier_statement", "documented_barrier")
                for item in [
                    *barriers_by_source.get(source_id, []),
                    *barriers_by_source.get(product_source_id, []),
                ]
            )
            output.append(
                {
                    "source_id": product_source_id,
                    "data_product_id": _value(
                        product, "data_product_id", default="NO_DATA_PRODUCT_RECORDED"
                    ),
                    "title": _value(product, "data_product_name", "title")
                    if product
                    else _value(source, "title"),
                    "source_link": _value(source, "source_url_or_doi"),
                    "funder": _value(audit, "funder", default="")
                    if audit
                    else _value(source, "funder"),
                    "collector": _value(audit, "collector", default="")
                    if audit
                    else _value(source, "collector"),
                    "producer": _value(audit, "producer", default="")
                    if audit
                    else _value(source, "producer"),
                    "indicator_authority": _value(
                        audit, "indicator_authority"
                    ),
                    "custodian": _value(audit, "custodian"),
                    "access_rule": _value(
                        audit, "access_rule", default=""
                    )
                    if audit
                    else _value(source, "access_rule"),
                    "collection_frequency": _value(audit, "collection_frequency"),
                    "funding_period": _value(audit, "funding_period"),
                    "documented_barrier": barrier_text
                    or _value(audit, "documented_barrier"),
                    "evidence_reference": _value(audit, "evidence_reference"),
                    "interpretation_status": _value(audit, "interpretation_status"),
                    "review_status": _value(
                        product, "review_status", default=""
                    )
                    if product
                    else _value(source, "review_status"),
                }
            )
    return output


def _source_record(inventory, source_id):
    source_id = inventory["source_aliases"].get(source_id, source_id)
    return next(
        (row for row in inventory["sources"] if row.get("source_id") == source_id),
        {},
    )


def _measure_records(inventory):
    seed_variables, candidate_variables = inventory["raw"]["variables"]
    all_variables = [*seed_variables, *candidate_variables]
    seed_observations, candidate_observations = inventory["raw"]["observations"]
    observations = [*seed_observations, *candidate_observations]
    products = [
        *inventory["raw"]["data_products"][0],
        *inventory["raw"]["data_products"][1],
    ]
    products_by_source = defaultdict(list)
    for product in products:
        products_by_source[product.get("source_id", "")].append(product)
    observations_by_key = defaultdict(list)
    for observation in observations:
        key = (
            observation.get("source_id", ""),
            observation.get("variable_id", ""),
        )
        observations_by_key[key].append(observation)

    unique = []
    seen = set()
    for variable in all_variables:
        source_id = _value(variable, "source_id", default="")
        variable_id = _value(variable, "variable_id", default="")
        name = _value(variable, "variable_name", default="")
        if not variable_id and not name:
            continue
        key = (source_id, variable_id or name)
        if key in seen:
            continue
        seen.add(key)
        source_products = products_by_source.get(source_id, [])
        product = source_products[0] if len(source_products) == 1 else {}
        matched_observations = observations_by_key.get((source_id, variable_id), [])
        details = "; ".join(
            " | ".join(
                [
                    f"time={_value(item, 'observed_time', 'observation_period')}",
                    f"unit={_value(item, 'unit')}",
                    f"denominator={_value(item, 'denominator')}",
                    f"geography={_value(item, 'geography_level', 'geographic_level')}",
                    f"value={_value(item, 'value')}",
                ]
            )
            for item in matched_observations
        )
        unique.append(
            {
                **variable,
                "_measure_key": variable_id or f"{source_id}:{name}",
                "_measure_label": f"{variable_id or 'NO_ID'} · {name or 'Unnamed variable'}",
                "_product_id": _value(
                    product, "data_product_id", default="UNKNOWN"
                )
                if product
                else "UNKNOWN",
                "_product_name": _value(
                    product, "data_product_name", "title", default="UNKNOWN"
                )
                if product
                else "UNKNOWN",
                "_observation_details": details or "No linked observation row",
                "_observation_count": len(matched_observations),
            }
        )
    return unique


def _claims(inventory):
    indicator_rows = [
        *inventory["raw"]["indicators"][0],
        *inventory["raw"]["indicators"][1],
    ]
    indicators_by_id = {}
    for row in indicator_rows:
        for key in (row.get("indicator_id"), row.get("indicator_code")):
            if key:
                indicators_by_id[key] = row
    claims = [
        {
            "id": "CORE_UNDER18_PREVENTION_CAUSAL",
            "label": "CORE · Under-18 prevention participation → subsequent substance use",
            "status": "CORE CLAIM",
            "match_ids": {"CORE_UNDER18_PREVENTION_CAUSAL", "Claim-CAUSE-01"},
        }
    ]
    for target_id in ("I009", "I013", "I014", "I015"):
        row = indicators_by_id.get(target_id, {})
        detail = _value(row, "indicator_note", "indicator_type", default="")
        suffix = f" — {detail}" if detail and detail != "UNKNOWN" else ""
        claims.append(
            {
                "id": target_id,
                "label": f"{target_id} · Existing pilot target{suffix}",
                "status": "EXISTING PILOT TARGET",
                "match_ids": {target_id},
            }
        )
    memo_claims = [
        (
            "MEMO_CASE_GYTS",
            "GYTS 2017 · tobacco-only, school-going ages 13–15",
            {
                "CLAIM-DESC-GYTS-CURRENT-TOBACCO",
                "CLAIM-DESC-GYTS-CIGARETTE-FREQUENCY",
            },
        ),
        (
            "MEMO_CASE_WENDU",
            "WENDU 2023 · age-by-region and substance tables remain separate",
            {"CLAIM-DESC-UNDER18-ARRESTS"},
        ),
        (
            "MEMO_CASE_JALLOW",
            "Jallow pilot · under-18 subgroup and observation time UNKNOWN",
            set(),
        ),
        (
            "MEMO_CASE_DLEAG_UNDP",
            "DLEAG–UNDP initiative · existence only, not reach, coverage, or effect",
            {"CLAIM-DESC-PROGRAMME-EXISTENCE"},
        ),
    ]
    for claim_id, label, stored_claim_ids in memo_claims:
        claims.append(
            {
                "id": claim_id,
                "label": f"TEAM_CANDIDATE / MEMO CASE · {label} · not a source finding",
                "status": "TEAM_CANDIDATE / MEMO CASE",
                "match_ids": {claim_id, *stored_claim_ids},
            }
        )
    return claims


def _alignment_lookup(inventory):
    rows = [*inventory["raw"]["alignments"][0], *inventory["raw"]["alignments"][1]]
    lookup = defaultdict(list)
    for row in rows:
        relation = _value(row, "relationship_class", default="")
        if relation not in ALIGNMENT_CLASSES:
            continue
        claim_ids = {
            value
            for value in (
                row.get("claim_id"),
                row.get("target_indicator_id"),
            )
            if value and value.strip()
        }
        observed_ids = {
            value
            for value in (
                row.get("observed_indicator_or_variable"),
                row.get("variable_id"),
                row.get("observed_indicator_id"),
            )
            if value and value.strip()
        }
        for observed_value in list(observed_ids):
            observed_ids.update(
                re.findall(r"\b[A-Z][A-Z0-9_]*\b", observed_value)
            )
        for claim_id in claim_ids:
            for observed_id in observed_ids:
                lookup[(claim_id, observed_id)].append(row)
    return rows, lookup


def _fixed_method_content():
    _scope_panel()


def render_readme(inventory):
    st.markdown("# Gambia Evidence Gap Explorer")
    st.markdown("**Pilot:** Youth Drug Prevention in The Gambia")
    st.caption(
        "V1 one-time graph build · candidate inventory only · no human assessment or approval in this run"
    )
    st.markdown("### Fixed Method & Scope")
    for label, value in FIXED_SCOPE:
        st.markdown(f"**{label}:** {value}")
    st.markdown("### Layer A parents")
    parents, _, _ = _canonical_parent_maps(inventory["parents"])
    st.markdown(" · ".join(parents) if parents else "Not configured in seed concept boxes.")

    st.markdown("### Formula / weights (read-only)")
    formula_path = ROOT / "config" / "measures.yaml"
    if formula_path.is_file():
        config = yaml.safe_load(formula_path.read_text(encoding="utf-8")) or {}
        st.write(
            {
                "name": config.get("formula_id", "Not configured"),
                "version": config.get("version", "Not configured"),
                "components": config.get("components", "Not configured"),
                "unknown_policy": config.get("unknown_policy", "Not configured"),
            }
        )
        st.caption("Inventory counts are unweighted. No user-editable weight or source controls are provided.")
    else:
        st.info("Formula / weights: Not configured.")
    st.markdown("### Inventory provenance")
    if inventory["candidate_loaded"]:
        st.write(f"Candidate batch loaded from `data/candidate_2026-10-31/` ({len(inventory['candidate_files'])} CSV files).")
    else:
        st.warning("candidate batch not loaded")
    st.write(f"Seed input: `data/preview/` (read-only).")
    st.write(f"Documentary items after source_id / URL deduplication: {len(inventory['sources'])}.")
    if inventory["duplicate_sources"]:
        st.warning(
            f"{len(inventory['duplicate_sources'])} duplicate source_id/URL rows were reported; seed rows take precedence."
        )
        st.dataframe(inventory["duplicate_sources"], hide_index=True, use_container_width=True)
    st.caption("Every record remains CANDIDATE_PENDING_HUMAN_REVIEW. Nothing is approved or promoted in this run.")


def render_view_a(inventory):
    st.markdown("# View A · Topic Inventory")
    st.markdown(
        "Documentary items in topic scope, whether or not they answer a research claim. Heat encodes document counts."
    )
    _fixed_method_content()
    documents, parent_axis = _document_rows(inventory)
    counts = Counter(
        (parent, row["_time_bin"])
        for row in documents
        for parent in row["_parents"]
    )
    z = [[counts[(parent, period)] for period in TIME_BINS] for parent in parent_axis]
    maximum = max((max(line) for line in z), default=0)
    hover = [
        [
            f"{parent}<br>{period}<br>Documents: {counts[(parent, period)]}<br>"
            "Distinct source families and data products are shown in the detail table."
            for period in TIME_BINS
        ]
        for parent in parent_axis
    ]
    text = [[str(value) for value in line] for line in z]
    colorscale = [
        [0.0, "#17222C"],
        [0.45, "#4B918C"],
        [1.0, "#B58B48"],
    ]
    fig = matrix(
        TIME_BINS,
        parent_axis,
        z,
        "Document count · observation time (publication time is separate)",
        colorscale,
        text=text,
        hovertext=hover,
        zmax=max(maximum, 1),
    )
    fig.update_traces(
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar={"title": "Documents"},
    )
    st.plotly_chart(fig, use_container_width=True, theme=None, key="v1_topic_heatmap")
    st.caption(
        f"Distinct documentary items: {len(documents)} · distinct source families: "
        f"{len({row['source_family'] for row in documents})} · distinct data products: "
        f"{len({_value(row, 'data_product_id', default='') for row in [*inventory['raw']['data_products'][0], *inventory['raw']['data_products'][1]] if _value(row, 'data_product_id', default='')})}. "
        "Multi-topic documents count once globally; parent counts may be non-additive. "
        "Observation time only is used on X; missing/unclear times are in the final bin."
    )

    st.markdown("### Layer B box detail")
    st.caption("Proposed boxes are shown as proposals only; they are not adopted taxonomy.")
    box_rows = [
        row
        for row in [*inventory["raw"]["concept_boxes"][0], *inventory["raw"]["concept_boxes"][1]]
        if row.get("box_type") not in {"layer_a_parent", ""}
    ]
    if box_rows:
        st.dataframe(
            [
                {
                    key: _value(row, key)
                    for key in (
                        "operational_box_id",
                        "box_title",
                        "population",
                        "substance",
                        "observation_period",
                        "outcome",
                        "unit",
                        "denominator",
                        "geography",
                        "method",
                        "can_support",
                        "cannot_support",
                        "box_status",
                        "review_status",
                    )
                }
                for row in box_rows
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No Layer B box rows are available in the loaded CSV inventory.")

    st.markdown("### Documentary item provenance")
    detail_rows = []
    for row in documents:
        detail_rows.append(
            {
                "source_id": row["source_id"],
                "title": _value(row, "title"),
                "URL/DOI": _value(row, "source_url_or_doi"),
                "Layer A parent(s)": "; ".join(row["_parents"]),
                "observation time": _value(row, "observed_time", "observation_year"),
                "publication time": _value(row, "publication_time", "publication_year"),
                "original age": _value(row, "original_age", "original_age_group"),
                "geography": _value(row, "geography_level", "geographic_level"),
                "substance": _value(row, "substance"),
                "source type": _value(row, "source_type"),
                "access": _value(row, "access_rule", "access_status"),
                "review status": _value(row, "review_status"),
                "source family": row["source_family"],
                "duplicate source IDs": "; ".join(
                    duplicate["duplicate_source_id"]
                    for duplicate in inventory["duplicate_sources"]
                    if duplicate["retained_source_id"] == row["source_id"]
                )
                or "None",
                "data products": sum(
                    1
                    for product in [
                        *inventory["raw"]["data_products"][0],
                        *inventory["raw"]["data_products"][1],
                    ]
                    if product.get("source_id") == row["source_id"]
                ),
            }
        )
    st.dataframe(detail_rows, hide_index=True, use_container_width=True)


def render_view_b(inventory):
    st.markdown("# View B · Claim & Measure Audit")
    st.markdown(
        "Every cell is either an exact stored alignment class or the display-only neutral state NOT_ASSESSED."
    )
    _fixed_method_content()
    claims = _claims(inventory)
    measures = _measure_records(inventory)
    alignment_rows, alignment_lookup = _alignment_lookup(inventory)
    measure_ids = []
    for measure in measures:
        ids = {
            measure.get("_measure_key", ""),
            measure.get("variable_id", ""),
            measure.get("indicator_id", ""),
            measure.get("indicator_code", ""),
            measure.get("variable_name", ""),
        }
        measure_ids.append({value for value in ids if value})

    states = []
    hover = []
    for claim in claims:
        state_row = []
        hover_row = []
        for measure, ids in zip(measures, measure_ids):
            stored = []
            for claim_id in claim["match_ids"]:
                for observed_id in ids:
                    stored.extend(alignment_lookup.get((claim_id, observed_id), []))
            stored = list({id(row): row for row in stored}.values())
            alignment = stored[0] if stored else None
            state = _value(alignment, "relationship_class") if alignment else "NOT_ASSESSED"
            state_row.append(state)
            source = _source_record(inventory, measure.get("source_id", ""))
            hover_row.append(
                "<br>".join(
                    [
                        f"State: {state}",
                        f"Variable: {_value(measure, 'variable_name')}",
                        f"Definition: {_value(measure, 'variable_definition', 'definition_verbatim')}",
                        f"Source: {_value(source, 'title')} ({_value(source, 'source_id')})",
                        f"Time: {_value(measure, 'observed_time', 'observation_year')} / publication: {_value(measure, 'publication_time', 'publication_year')}",
                        f"Age: {_value(measure, 'original_age', 'original_age_group')}",
                        f"Geography: {_value(measure, 'geography_level', 'geographic_level')}",
                        f"Unit: {_value(measure, 'unit')}",
                        f"Denominator: {_value(measure, 'denominator')}",
                        f"Reason: {_value(alignment, 'relationship_reason') if alignment else 'No stored alignment row'}",
                        f"Measurement loss: {_value(alignment, 'measurement_loss') if alignment else 'UNKNOWN'}",
                        f"Identification limitation: {_value(alignment, 'identification_limitation') if alignment else 'UNKNOWN'}",
                        f"Review status: {_value(alignment, 'review_status') if alignment else _value(measure, 'review_status')}",
                    ]
                )
            )
        states.append(state_row)
        hover.append(hover_row)
    state_names = [*ALIGNMENT_CLASSES, "NOT_ASSESSED", "NOT_APPLICABLE"]
    state_index = {state: index for index, state in enumerate(state_names)}
    z = [[state_index.get(state, state_index["NOT_ASSESSED"]) for state in row] for row in states]
    labels_x = [measure["_measure_key"] for measure in measures]
    labels_y = [claim["label"] for claim in claims]
    display_text = [list(row) for row in states]
    if measures:
        fig = matrix(
            labels_x,
            labels_y,
            z,
            "Research claim × observed measure · stored relationships only",
            categorical_scale(state_names, DISPLAY_COLORS),
            text=display_text,
            hovertext=hover,
            zmax=len(state_names) - 1,
        )
        fig.update_layout(height=max(560, min(900, 42 * len(claims) + 200)))
        st.plotly_chart(fig, use_container_width=True, theme=None, key="v1_claim_measure_matrix")
    else:
        st.info("No measured variables were loaded; no measure columns have been fabricated.")

    cell_counts = Counter(state for row in states for state in row)
    stored_counts = Counter(
        state for row in states for state in row if state in ALIGNMENT_CLASSES
    )
    st.caption(
        f"Claims: {len(claims)} · measures: {len(measures)} · claim × measure cells: "
        f"{len(claims) * len(measures)} · stored-class cells: {sum(stored_counts.values())} · "
        f"NOT_ASSESSED: {cell_counts['NOT_ASSESSED']} · NOT_APPLICABLE: {cell_counts['NOT_APPLICABLE']}. "
        "NOT_ASSESSED is display-only and is never written as an alignment."
    )
    st.markdown("### Stored class / display-state counts")
    st.dataframe(
        [
            {"state": state, "display cells": cell_counts[state]}
            for state in [*ALIGNMENT_CLASSES, "NOT_ASSESSED", "NOT_APPLICABLE"]
        ],
        hide_index=True,
        use_container_width=True,
    )
    st.markdown("### Grouped measure lineage")
    parents, parent_assignments = _source_parent_assignments(inventory)
    grouped_measures = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for measure in measures:
        source_id = measure.get("source_id", "")
        assigned_parents = parent_assignments.get(source_id) or {
            "UNMAPPED / REVIEW_REQUIRED"
        }
        for parent in assigned_parents:
            grouped_measures[parent][source_id][
                (measure["_product_id"], measure["_product_name"])
            ].append(measure)
    for parent in [*parents, "UNMAPPED / REVIEW_REQUIRED"]:
        source_groups = grouped_measures.get(parent, {})
        with st.expander(f"{parent} · {sum(len(rows) for products in source_groups.values() for rows in products.values())} measures"):
            for source_id, product_groups in sorted(source_groups.items()):
                source = _source_record(inventory, source_id)
                with st.expander(f"{source_id} · {_value(source, 'title')}"):
                    for (product_id, product_name), product_measures in sorted(
                        product_groups.items()
                    ):
                        st.markdown(f"**{product_id} · {product_name}**")
                        st.dataframe(
                            [
                                {
                                    "indicator": _value(measure, "indicator_id", "indicator_code"),
                                    "variable_id": measure["_measure_key"],
                                    "variable": _value(measure, "variable_name"),
                                    "definition": _value(measure, "variable_definition"),
                                    "observation rows": measure["_observation_count"],
                                    "observation detail": measure["_observation_details"],
                                    "review status": _value(measure, "review_status"),
                                }
                                for measure in product_measures
                            ],
                            hide_index=True,
                            use_container_width=True,
                        )

    measured_source_ids = {row.get("source_id") for row in measures}
    contextual = [
        row
        for row in inventory["sources"]
        if row.get("source_id") not in measured_source_ids
    ]
    st.markdown("### Contextual documents · no observed variable linked")
    st.caption("These remain documentary context and are not represented as observed-variable columns.")
    st.dataframe(
        [
            {
                "source_id": _value(row, "source_id"),
                "title": _value(row, "title"),
                "URL/DOI": _value(row, "source_url_or_doi"),
                "original age": _value(row, "original_age", "original_age_group"),
                "geography": _value(row, "geography_level", "geographic_level"),
                "review status": _value(row, "review_status"),
            }
            for row in contextual
        ],
        hide_index=True,
        use_container_width=True,
    )
    st.markdown("### Literal interpretation guardrails")
    for guardrail in (
        "WENDU NIL cells stay as text, not 0.",
        "WENDU age x region and substance tables are never joined.",
        "OCIndex market scores (heroin 2.50, cocaine 7.50, cannabis 6.50, synthetic 5.00) and PREVENTION resilience (4.50) are on opposite scales and must not be compared as one scale.",
        "Kush is not equated with cannabis or a synthetic index item.",
        "GYTS is tobacco only, school-going 13-15 only.",
        "DLEAG-UNDP launch proves existence only, not reach, coverage or effect.",
    ):
        st.markdown(f"- {guardrail}")


def render_view_c(inventory):
    st.markdown("# View C · Data Production Flow")
    st.markdown(
        "Table-first production roles and evidence references. Role labels are kept separate; UNKNOWN is not inferred."
    )
    _fixed_method_content()
    rows = _product_records(inventory)
    st.caption(f"Data product/document rows: {len(rows)}")
    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
        column_config={
            "source_link": st.column_config.LinkColumn(
                "source link", display_text="Open source"
            )
        },
    )
    st.info(
        "No diagram is drawn: the loaded records do not supply a complete documented relation type plus evidence reference for every proposed edge. Unknown relations remain UNKNOWN; no arrows or production chain are inferred."
    )
