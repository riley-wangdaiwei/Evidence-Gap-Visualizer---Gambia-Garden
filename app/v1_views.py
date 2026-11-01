import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import yaml
from plotly.subplots import make_subplots

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
RELEVANCE_COMPONENTS = {
    "concept / definition text": 0.25,
    "Layer A topic overlap": 0.15,
    "substance compatibility": 0.15,
    "population overlap": 0.15,
    "outcome / construct overlap": 0.15,
    "observation-period compatibility": 0.05,
    "unit / denominator / method compatibility": 0.05,
    "geography compatibility": 0.05,
}
DISPLAY_COLORS = {
    **RELATION_COLORS,
    "NOT_ASSESSED": "#454B50",
    "NOT_APPLICABLE": "#26333D",
    "MULTIPLE_STORED": "#8B6FA8",
}
PROVENANCE_COLORS = {
    "OBSERVED": "#4B918C",
    "RULE_DERIVED": "#B58B48",
    "MODEL_SUGGESTED": "#9B70B3",
    "SIMULATED / ILLUSTRATIVE": "#68717A",
    "UNKNOWN": "#454B50",
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
    return not value or value.strip().upper() in {
        "UNKNOWN",
        "N/A",
        "NOT RECORDED",
        "NOT SPECIFIED",
        "UNSPECIFIED",
    }


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
    csv_inventory = []
    unparsed_rows = []
    for entity in entities:
        raw[entity] = _load_rows(entity)
        seed_path = SEED_DIR / f"{entity}.csv"
        candidate_path = _candidate_csv(entity) if CANDIDATE_DIR.is_dir() else None
        for batch, path, rows in (
            ("seed", seed_path, raw[entity][0]),
            ("candidate", candidate_path, raw[entity][1]),
        ):
            if path is None or not path.is_file():
                continue
            csv_inventory.append(
                {
                    "batch": batch,
                    "file": str(path.relative_to(ROOT)),
                    "rows": len(rows),
                    "columns": len(rows[0]) if rows else 0,
                }
            )
            for row_number, row in enumerate(rows, start=2):
                if None in row:
                    unparsed_rows.append(
                        {
                            "batch": batch,
                            "file": str(path.relative_to(ROOT)),
                            "row": row_number,
                            "extra_fields": row[None],
                            "parsed_record": {
                                key: value for key, value in row.items() if key is not None
                            },
                        }
                    )

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
        "csv_inventory": csv_inventory,
        "unparsed_rows": unparsed_rows,
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
        st.markdown(
            "**Exploratory relevance:** R(c,m) = Σ(wₖ × sₖ) / Σ(wₖ for known components); "
            "coverage C(c,m) = Σ(wₖ for known components). Fixed provisional weights are "
            "0.25 concept, 0.15 topic, 0.15 substance, 0.15 population, 0.15 outcome, "
            "0.05 period, 0.05 unit/method, 0.05 geography."
        )
        st.caption(
            "R and C are RULE_DERIVED navigation aids, not scientific fit, causal effects, "
            "or stored alignment classes. Missing inputs remain visible as UNKNOWN."
        )
        st.markdown(
            "**Flow edge types:** funded_by, collected_by, produced_by, "
            "indicator_defined_by, held_by/custodied_by, reported_to, accessible_through."
        )
        st.markdown(
            "**Provenance:** OBSERVED = explicitly recorded; RULE_DERIVED = deterministic "
            "calculation/layout; MODEL_SUGGESTED = model proposal; SIMULATED / ILLUSTRATIVE "
            "= synthetic visual only; UNKNOWN = not established."
        )


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


def _compact_parent_label(parent):
    normalized = parent.casefold()
    compact = (
        ("substance-specific", "T01 · Substance use"),
        ("health outcomes", "T02 · Health harms"),
        ("treatment/service", "T03 · Treatment access"),
        ("prevention policies", "T04 · Prevention policy"),
        ("programme delivery", "T05 · Programme delivery"),
        ("post-participation", "T06 · Post-participation"),
        ("enforcement/supply", "T07 · Enforcement / supply"),
        ("social/livelihood", "T08 · Social / livelihood"),
        ("cross-border", "T09 · Cross-border finance"),
        ("data production", "T10 · Data governance"),
    )
    for token, label in compact:
        if token in normalized:
            return label
    return "UNMAPPED / REVIEW_REQUIRED" if "unmapped" in normalized else parent[:35]


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
    observed = _value(
        source,
        "observed_time",
        "observation_period",
        "observation_year",
        default="",
    )
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
                    "reported_to": _value(audit, "reported_to", default="")
                    if audit
                    else _value(source, "reported_to", default=""),
                    "access_authority": _value(
                        audit, "access_authority", default=""
                    )
                    if audit
                    else _value(source, "access_authority", default=""),
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
    all_variables = [
        *inventory["raw"]["variables"][0],
        *inventory["raw"]["variables"][1],
    ]
    all_indicators = [
        *inventory["raw"]["indicators"][0],
        *inventory["raw"]["indicators"][1],
    ]
    observations = [
        *inventory["raw"]["observations"][0],
        *inventory["raw"]["observations"][1],
    ]
    products = [*inventory["raw"]["data_products"][0], *inventory["raw"]["data_products"][1]]
    products_by_source = defaultdict(list)
    for product in products:
        products_by_source[product.get("source_id", "")].append(product)
    observations_by_key = defaultdict(list)
    for observation in observations:
        for id_field in ("variable_id", "indicator_id", "observed_indicator_id"):
            record_id = observation.get(id_field, "")
            if record_id:
                observations_by_key[(observation.get("source_id", ""), record_id)].append(
                    observation
                )

    measures = []
    seen = set()
    linked_measure_ids = set()
    for kind, rows, id_field, name_fields, definition_fields in (
        (
            "INDICATOR",
            all_indicators,
            "indicator_id",
            ("indicator_name", "indicator_title", "indicator_code"),
            ("indicator_definition", "definition_verbatim", "indicator_note"),
        ),
        (
            "VARIABLE",
            all_variables,
            "variable_id",
            ("variable_name", "variable_title"),
            ("variable_definition", "definition_verbatim"),
        ),
    ):
        for row in rows:
            source_id = _value(row, "source_id", default="")
            measure_id = _value(row, id_field, default="")
            name = _value(row, *name_fields, default="")
            if not measure_id and not name:
                continue
            unique_key = (kind, source_id, measure_id or name)
            if unique_key in seen:
                continue
            seen.add(unique_key)
            if measure_id:
                linked_measure_ids.add((source_id, measure_id))
            source_products = products_by_source.get(source_id, [])
            product = source_products[0] if len(source_products) == 1 else {}
            matched_observations = observations_by_key.get((source_id, measure_id), [])
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
            measures.append(
                {
                    **row,
                    "_measure_type": kind,
                    "_measure_key": f"{kind[:1]}:{measure_id or name}",
                    "_measure_label": f"{kind[:1]} · {measure_id or 'NO_ID'} · {name or 'Unnamed measure'}",
                    "_measure_id": measure_id or name,
                    "_definition": _value(row, *definition_fields),
                    "_product_id": _value(product, "data_product_id", default="UNKNOWN")
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

    for observation in observations:
        source_id = _value(observation, "source_id", default="")
        linked_id = _value(observation, "variable_id", "indicator_id", default="")
        if linked_id and (source_id, linked_id) in linked_measure_ids:
            continue
        observation_id = _value(observation, "observation_id", default="")
        name = _value(observation, "variable_name", "indicator_name", default="")
        fallback_id = observation_id or linked_id or name
        unique_key = ("OBSERVATION", source_id, fallback_id)
        if not fallback_id or unique_key in seen:
            continue
        seen.add(unique_key)
        measures.append(
            {
                **observation,
                "_measure_type": "OBSERVATION",
                "_measure_key": f"O:{fallback_id}",
                "_measure_label": f"O · {fallback_id} · {name or 'Unlinked observation'}",
                "_measure_id": fallback_id,
                "_definition": _value(
                    observation, "definition_verbatim", "variable_definition", "indicator_definition"
                ),
                "_product_id": "UNKNOWN",
                "_product_name": "UNKNOWN",
                "_observation_details": (
                    f"time={_value(observation, 'observed_time', 'observation_period')} | "
                    f"unit={_value(observation, 'unit')} | "
                    f"denominator={_value(observation, 'denominator')} | "
                    f"value={_value(observation, 'value')}"
                ),
                "_observation_count": 1,
            }
        )
    return measures


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
            "description": (
                "Whether youth prevention programme participation reduces subsequent "
                "substance use among under-18s."
            ),
            "status": "CORE CLAIM",
            "match_ids": {"CORE_UNDER18_PREVENTION_CAUSAL", "Claim-CAUSE-01"},
            "source_id": "USER_DEFINED",
            "population": "Under-18",
            "geography": "The Gambia",
            "outcome": "Subsequent substance use",
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
                "description": _value(
                    row, "indicator_definition", "definition_verbatim", "indicator_note"
                ),
                "status": "EXISTING PILOT TARGET",
                "match_ids": {target_id},
                "source_id": _value(row, "source_id"),
                "unit": _value(row, "unit", default=""),
                "denominator": _value(row, "denominator", default=""),
                "method": _value(row, "measurement_method", "method", default=""),
                "geography": _value(row, "geography_level", "geographic_level", default=""),
                "observation_period": _value(row, "observed_time", "observation_period", default=""),
                "outcome": _value(row, "outcome", "construct", "indicator_type", default=""),
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
                "description": label,
                "status": "TEAM_CANDIDATE / MEMO CASE",
                "match_ids": {claim_id, *stored_claim_ids},
                "source_id": "TEAM_MEMO",
                "population": "School-going ages 13-15"
                if claim_id == "MEMO_CASE_GYTS"
                else "UNKNOWN",
                "geography": "The Gambia",
                "outcome": label,
            }
        )
    for row in [
        *inventory["raw"]["gap_claims"][0],
        *inventory["raw"]["gap_claims"][1],
    ]:
        gap_id = _value(row, "gap_claim_id", default="")
        if not gap_id:
            continue
        area = _value(row, "claim_area", "gap_claim_type", default="Source-stated gap")
        description = _value(
            row, "claim_interpretation", "evidence_quote", "definition_verbatim"
        )
        claims.append(
            {
                "id": gap_id,
                "label": f"SOURCE-STATED GAP · {_value(row, 'source_id')} · {area}",
                "description": description,
                "status": "SOURCE_STATED / CANDIDATE",
                "match_ids": {gap_id},
                "source_id": _value(row, "source_id"),
                "unit": _value(row, "unit", default=""),
                "denominator": _value(row, "denominator", default=""),
                "method": _value(row, "method", "measurement_method", default=""),
                "geography": _value(row, "geography_level", "geographic_level", default=""),
                "observation_period": _value(row, "observed_time", "observation_period", default=""),
                "population": _value(row, "original_age", "original_age_group", default=""),
                "substance": _value(row, "substance", default=""),
                "outcome": _value(row, "claim_area", "gap_claim_type", default=""),
            }
        )
    return claims


def _alignment_lookup(inventory):
    rows = [*inventory["raw"]["alignments"][0], *inventory["raw"]["alignments"][1]]
    lookup = defaultdict(list)
    for row in rows:
        relation = _value(row, "relationship_class", default="")
        if relation not in {*ALIGNMENT_CLASSES, "NOT_APPLICABLE"}:
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


STOP_WORDS = {
    "about",
    "after",
    "among",
    "and",
    "are",
    "been",
    "between",
    "from",
    "into",
    "more",
    "over",
    "participation",
    "programme",
    "should",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "under",
    "what",
    "when",
    "where",
    "which",
    "with",
    "youth",
}


def _entity_rows(inventory, entity):
    return [*inventory["raw"][entity][0], *inventory["raw"][entity][1]]


def _tokens(text):
    if _is_unknown(str(text or "")):
        return set()
    return {
        token.casefold()
        for token in re.findall(r"[a-zA-Z0-9]+", str(text))
        if len(token) > 1 and token.casefold() not in STOP_WORDS
    }


def _text_similarity(left, right):
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return None
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _year_range(value):
    years = [int(year) for year in re.findall(r"(?:19|20)\d{2}", str(value or ""))]
    return (min(years), max(years)) if years else None


def _age_interval(value):
    text = str(value or "").casefold()
    if not text or _is_unknown(text):
        return None
    numbers = [int(number) for number in re.findall(r"\d{1,2}", text)]
    if len(numbers) >= 2:
        return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
    if "adult" in text or "18+" in text:
        return 18, 100
    if any(term in text for term in ("under-18", "under 18", "minor", "adolescent", "child")):
        return 0, 17
    if "youth" in text:
        return 15, 24
    if numbers:
        return numbers[0], numbers[0]
    return None


def _relevance_components(claim, measure, source, parents):
    claim_text = " ".join(
        [
            str(claim.get("label", "")),
            str(claim.get("description", "")),
        ]
    )
    measure_text = " ".join(
        [
            str(measure.get("_measure_label", "")),
            str(measure.get("_definition", "")),
            str(measure.get("variable_name", "")),
            str(measure.get("indicator_name", "")),
        ]
    )
    outcome_vocabulary = {
        "use",
        "prevalence",
        "frequency",
        "participation",
        "reach",
        "coverage",
        "effect",
        "harms",
        "health",
        "treatment",
        "access",
        "arrest",
        "seizure",
        "supply",
        "risk",
        "knowledge",
        "attitude",
        "resilience",
        "initiation",
        "onset",
    }
    claim_outcomes = _tokens(
        _value(claim, "outcome", default="") or claim_text
    ) & outcome_vocabulary
    measure_outcomes = _tokens(
        " ".join(
            [
                _value(measure, "outcome", "construct", "indicator_type", default=""),
                measure_text,
            ]
        )
    ) & outcome_vocabulary
    components = {
        "concept / definition text": _text_similarity(claim_text, measure_text),
        "Layer A topic overlap": None,
        "substance compatibility": None,
        "population overlap": None,
        "outcome / construct overlap": (
            len(claim_outcomes & measure_outcomes) / len(claim_outcomes | measure_outcomes)
            if claim_outcomes and measure_outcomes
            else None
        ),
        "observation-period compatibility": None,
        "unit / denominator / method compatibility": None,
        "geography compatibility": None,
    }

    assigned_parents = parents.get(source.get("source_id", ""), set())
    if assigned_parents:
        components["Layer A topic overlap"] = max(
            (
                _text_similarity(claim_text, parent)
                for parent in assigned_parents
                if _text_similarity(claim_text, parent) is not None
            ),
            default=0.0,
        )

    measure_substance = _value(measure, "substance", default="")
    if not _is_unknown(measure_substance):
        known_substances = {
            "tobacco": ("tobacco", "nicotine", "cigarette", "smoking"),
            "cannabis": ("cannabis",),
            "kush": ("kush",),
            "heroin": ("heroin",),
            "cocaine": ("cocaine",),
            "synthetic": ("synthetic",),
        }
        claim_substances = {
            name
            for name, terms in known_substances.items()
            if any(term in claim_text.casefold() for term in terms)
        }
        measured_names = {
            name
            for name, terms in known_substances.items()
            if any(term in measure_substance.casefold() for term in terms)
        }
        if claim_substances:
            components["substance compatibility"] = float(
                bool(claim_substances & measured_names)
            )
        elif "substance" in claim_text.casefold():
            components["substance compatibility"] = 0.5

    claim_age = _age_interval(_value(claim, "population", default=""))
    if not claim_age and any(
        term in claim_text.casefold()
        for term in ("under-18", "under 18", "minor", "adolescent")
    ):
        claim_age = (0, 17)
    measure_age = _age_interval(
        _value(measure, "original_age", "original_age_group", default="")
    )
    if claim_age and measure_age:
        overlap = max(0, min(claim_age[1], measure_age[1]) - max(claim_age[0], measure_age[0]) + 1)
        total = max(1, measure_age[1] - measure_age[0] + 1)
        components["population overlap"] = overlap / total

    claim_period = _year_range(
        _value(claim, "observation_period", "observed_time", default="")
    )
    measure_period = _year_range(
        _value(measure, "observed_time", "observation_period", "observation_year", default="")
    )
    if claim_period and measure_period:
        overlap = max(
            0,
            min(claim_period[1], measure_period[1])
            - max(claim_period[0], measure_period[0])
            + 1,
        )
        total = max(1, measure_period[1] - measure_period[0] + 1)
        components["observation-period compatibility"] = overlap / total

    geography = _value(
        measure,
        "geography_level",
        "geographic_level",
        "geography",
        default=_value(source, "geography_level", "geographic_level", default=""),
    )
    claim_geography = _value(claim, "geography", default="The Gambia")
    if not _is_unknown(geography):
        geography_text = geography.casefold()
        source_context = " ".join(
            _value(source, key, default="")
            for key in ("title", "source_url_or_doi", "geography_level", "geographic_level")
        ).casefold()
        if (
            ("gambia" in geography_text or "gambia" in source_context)
            and "gambia" in claim_geography.casefold()
        ):
            components["geography compatibility"] = 1.0
        elif any(term in geography_text for term in ("regional", "multi-country", "west africa")):
            components["geography compatibility"] = 0.5
        elif "national" in geography_text and "gambia" in claim_geography.casefold():
            components["geography compatibility"] = 0.5
        else:
            components["geography compatibility"] = 0.0

    claim_unit = " ".join(
        str(claim.get(key) or "")
        for key in ("unit", "denominator", "method")
        if not _is_unknown(str(claim.get(key) or ""))
    )
    measure_unit = " ".join(
        str(measure.get(key) or "")
        for key in ("unit", "denominator", "measurement_method", "method")
        if not _is_unknown(str(measure.get(key) or ""))
    )
    if claim_unit and measure_unit:
        components["unit / denominator / method compatibility"] = _text_similarity(
            claim_unit, measure_unit
        )
    return components


def _relevance_score(components):
    known_weight = sum(
        weight
        for name, weight in RELEVANCE_COMPONENTS.items()
        if components.get(name) is not None
    )
    if not known_weight:
        return None, 0.0
    score = sum(
        RELEVANCE_COMPONENTS[name] * components[name]
        for name in RELEVANCE_COMPONENTS
        if components.get(name) is not None
    ) / known_weight
    return score, known_weight


@st.cache_data(show_spinner=False)
def _semantic_projection(inventory):
    parents, parent_assignments = _source_parent_assignments(inventory)
    records = []
    for source in inventory["sources"]:
        records.append(
            {
                "id": _value(source, "source_id"),
                "type": "DOCUMENT",
                "title": _value(source, "title"),
                "source_id": _value(source, "source_id"),
                "url": _value(source, "source_url_or_doi"),
                "text": " ".join(
                    _value(source, key, default="")
                    for key in ("title", "definition_verbatim", "source_note", "abstract")
                ),
                "parent": next(
                    iter(sorted(parent_assignments.get(source.get("source_id", ""), set()))),
                    "UNMAPPED / REVIEW_REQUIRED",
                ),
            }
        )
    for measure in _measure_records(inventory):
        source = _source_record(inventory, measure.get("source_id", ""))
        records.append(
            {
                "id": measure["_measure_key"],
                "type": measure["_measure_type"],
                "title": measure["_measure_label"],
                "source_id": _value(source, "source_id"),
                "url": _value(source, "source_url_or_doi"),
                "text": " ".join(
                    [
                        measure["_measure_label"],
                        measure["_definition"],
                        _value(measure, "substance"),
                    ]
                ),
                "parent": next(
                    iter(sorted(parent_assignments.get(source.get("source_id", ""), set()))),
                    "UNMAPPED / REVIEW_REQUIRED",
                ),
            }
        )
    for claim in _claims(inventory):
        records.append(
            {
                "id": claim["id"],
                "type": "CLAIM",
                "title": claim["label"],
                "source_id": claim.get("source_id", "UNKNOWN"),
                "url": _value(_source_record(inventory, claim.get("source_id", "")), "source_url_or_doi"),
                "text": f"{claim['label']} {claim.get('description', '')}",
                "parent": "CLAIM",
            }
        )
    return records


@st.cache_data(show_spinner=False)
def _tfidf_pca(records):
    token_rows = [_tokens(record["text"]) for record in records]
    vocabulary = sorted(set().union(*token_rows)) if token_rows else []
    if not records or not vocabulary:
        return np.zeros((len(records), 2))
    token_index = {token: index for index, token in enumerate(vocabulary)}
    matrix_values = np.zeros((len(records), len(vocabulary)), dtype=float)
    document_frequency = Counter(token for row in token_rows for token in row)
    for row_index, tokens in enumerate(token_rows):
        if not tokens:
            continue
        for token in tokens:
            matrix_values[row_index, token_index[token]] = 1.0
    inverse_frequency = np.array(
        [
            math.log((1 + len(records)) / (1 + document_frequency[token])) + 1
            for token in vocabulary
        ]
    )
    matrix_values *= inverse_frequency
    norms = np.linalg.norm(matrix_values, axis=1, keepdims=True)
    matrix_values = np.divide(
        matrix_values,
        norms,
        out=np.zeros_like(matrix_values),
        where=norms != 0,
    )
    centered = matrix_values - matrix_values.mean(axis=0, keepdims=True)
    if centered.shape[0] < 2:
        return np.zeros((len(records), 2))
    left, singular_values, right = np.linalg.svd(centered, full_matrices=False)
    dimensions = min(2, len(singular_values))
    coordinates = np.zeros((len(records), 2))
    coordinates[:, :dimensions] = left[:, :dimensions] * singular_values[:dimensions]
    for axis in range(dimensions):
        anchor = int(np.argmax(np.abs(right[axis])))
        if right[axis, anchor] < 0:
            coordinates[:, axis] *= -1
    return coordinates


@st.cache_data(show_spinner=False)
def _spring_layout_coordinates(node_ids, edges):
    layout_graph = nx.Graph()
    layout_graph.add_nodes_from(node_ids)
    layout_graph.add_edges_from(edges)
    if not node_ids:
        return {}
    positions = nx.spring_layout(
        layout_graph,
        seed=2026,
        iterations=24,
        k=1 / math.sqrt(max(len(node_ids), 1)),
        weight=None,
    )
    return {
        node_id: (float(position[0]), float(position[1]))
        for node_id, position in positions.items()
    }


def _fixed_method_content():
    _scope_panel()


def render_readme(inventory):
    documents, _ = _document_rows(inventory)
    measures = _measure_records(inventory)
    claims = _claims(inventory)
    products = _entity_rows(inventory, "data_products")
    observations = _entity_rows(inventory, "observations")
    families = {
        row["source_family"]
        for row in documents
    }

    st.markdown("# Gambia Evidence Gap Explorer")
    st.markdown("### Exploratory Evidence Atlas")
    st.caption(
        "Maximal visibility mode · all relevant seed and candidate rows remain explorable "
        "regardless of review, access, age, or alignment state."
    )
    columns = st.columns(5)
    for column, label, value in zip(
        columns,
        ("Documents", "Source families", "Data products", "Measures", "Claims"),
        (
            len(documents),
            len(families),
            len(products),
            len(measures),
            len(claims),
        ),
    ):
        column.metric(label, value)
    st.markdown(
        "**Four views:** README / Overview · View A Topic Inventory · View B Claim & Measure Audit · "
        "View C Data Production Flow."
    )
    st.info(
        "The atlas maximizes visibility, not certainty. Candidate status, restricted access, "
        "unknown metadata, and weak or absent alignments never hide a record."
    )
    st.markdown("### Fixed Method & Scope")
    for label, value in FIXED_SCOPE:
        st.markdown(f"**{label}:** {value}")
    st.markdown("### Fixed Layer A parents")
    parents, _, _ = _canonical_parent_maps(inventory["parents"])
    st.markdown(" · ".join(parents) if parents else "Not configured in seed concept boxes.")

    st.markdown("### Exploratory claim–measure relevance (read-only)")
    st.dataframe(
        [
            {"component": name, "fixed weight": weight}
            for name, weight in RELEVANCE_COMPONENTS.items()
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Formula: R(c,m) = weighted mean over known components; C(c,m) = sum of weights "
        "for known components. R and C are RULE_DERIVED navigation aids only. They never "
        "create or modify a stored alignment."
    )
    st.markdown("### Configured measurement formula (separate, read-only)")
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
    else:
        st.info("config/measures.yaml: Not configured.")
    st.caption("Configured mismatch weights are not applied to inventory counts or exploratory R.")

    st.markdown("### Loaded CSV inventory · raw inputs retained")
    st.dataframe(inventory["csv_inventory"], hide_index=True, width="stretch")
    if inventory["candidate_loaded"]:
        st.success(
            f"Candidate batch loaded: {len(inventory['candidate_files'])} CSV files. "
            "Seed CSVs remain read-only."
        )
    else:
        st.warning("candidate batch not loaded")
    st.caption(
        f"Seed source rows: {len(inventory['raw']['sources'][0])} · candidate source rows: "
        f"{len(inventory['raw']['sources'][1])} · unique displayed documents after exact "
        f"source-ID/URL deduplication: {len(documents)} · observation rows retained: {len(observations)}."
    )
    st.markdown("### Provenance states")
    provenance_columns = st.columns(len(PROVENANCE_COLORS))
    for column, (state, color) in zip(provenance_columns, PROVENANCE_COLORS.items()):
        column.markdown(
            f"<div style='border-left:4px solid {color};padding:.35rem .55rem;"
            f"background:#111820'><b>{state}</b></div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "Search frame is bounded and not exhaustive. Observation time and publication time "
        "remain separate. No national value is expanded into a subnational record."
    )
    if inventory["duplicate_sources"]:
        with st.expander(f"Exact source duplicates reported ({len(inventory['duplicate_sources'])})"):
            st.dataframe(
                inventory["duplicate_sources"],
                hide_index=True,
                width="stretch",
            )
    if inventory["unparsed_rows"]:
        with st.expander(f"CSV rows with extra/unparsed fields ({len(inventory['unparsed_rows'])})"):
            st.dataframe(
                inventory["unparsed_rows"],
                hide_index=True,
                width="stretch",
            )
    st.caption(
        "All source and candidate review labels are displayed as recorded; this exploratory "
        "release does not approve, reject, or promote evidence."
    )


def render_view_a(inventory):
    documents, parent_axis = _document_rows(inventory)
    st.markdown("# View A · Topic Inventory")
    st.markdown(
        "Full topic universe and linked data layers. Review status, access, population "
        "scope, and alignment never gate visibility."
    )
    _fixed_method_content()

    filter_keys = (
        "v1_filter_search",
        "v1_filter_parent",
        "v1_filter_time",
        "v1_filter_publication",
        "v1_filter_substance",
        "v1_filter_age",
        "v1_filter_geography",
        "v1_filter_source_type",
        "v1_filter_access",
        "v1_filter_review",
        "v1_filter_box",
    )
    if st.button("Show all / reset filters", key="v1_reset_filters"):
        for key in filter_keys:
            st.session_state[key] = "" if key.endswith("search") else []
        st.rerun()

    parents, parent_assignments = _source_parent_assignments(inventory)
    mapping_boxes = defaultdict(set)
    for row in _entity_rows(inventory, "mapping"):
        if row.get("source_id") and row.get("operational_box_id"):
            mapping_boxes[row["source_id"]].add(row["operational_box_id"])
    filter_values = {
        "parent": parent_axis,
        "time": TIME_BINS,
        "publication": sorted(
            {
                _value(row, "publication_time", "publication_year")
                for row in documents
                if not _is_unknown(_value(row, "publication_time", "publication_year"))
            }
        ),
        "substance": sorted({_value(row, "substance") for row in documents}),
        "age": sorted({_value(row, "original_age", "original_age_group") for row in documents}),
        "geography": sorted(
            {_value(row, "geography_level", "geographic_level") for row in documents}
        ),
        "source_type": sorted({_value(row, "source_type", "record_entity_type") for row in documents}),
        "access": sorted({_value(row, "access_rule", "access_status") for row in documents}),
        "review": sorted({_value(row, "review_status") for row in documents}),
        "box": sorted(
            {
                box
                for source_boxes in mapping_boxes.values()
                for box in source_boxes
            }
        ),
    }
    with st.expander("Inventory filters · defaults include every record", expanded=True):
        search = st.text_input("Search sources and metadata", key="v1_filter_search").casefold()
        filter_columns = st.columns(3)
        selected = {}
        for column, (name, label, state_key) in zip(
            filter_columns * 3,
            (
                ("parent", "Layer A parent", "v1_filter_parent"),
                ("time", "Observation-time bin", "v1_filter_time"),
                ("publication", "Publication time", "v1_filter_publication"),
                ("substance", "Substance", "v1_filter_substance"),
                ("age", "Age / population", "v1_filter_age"),
                ("geography", "Geography", "v1_filter_geography"),
                ("source_type", "Source type", "v1_filter_source_type"),
                ("access", "Access status", "v1_filter_access"),
                ("review", "Review status", "v1_filter_review"),
            ),
        ):
            selected[name] = column.multiselect(
                label,
                filter_values[name],
                key=state_key,
                help="Leave empty to include all values.",
            )
        selected["box"] = st.multiselect(
            "Layer B operational box",
            filter_values["box"],
            key="v1_filter_box",
            help="Leave empty to include all operational boxes.",
        )

    filtered_documents = []
    for row in documents:
        source_id = row["source_id"]
        values = {
            "parent": set(row["_parents"]),
            "time": {row["_time_bin"]},
            "publication": {_value(row, "publication_time", "publication_year")},
            "substance": {_value(row, "substance")},
            "age": {_value(row, "original_age", "original_age_group")},
            "geography": {_value(row, "geography_level", "geographic_level")},
            "source_type": {_value(row, "source_type", "record_entity_type")},
            "access": {_value(row, "access_rule", "access_status")},
            "review": {_value(row, "review_status")},
            "box": mapping_boxes.get(source_id, set()),
        }
        if any(selection and not (selection & values[name]) for name, selection in selected.items()):
            continue
        searchable = " ".join(
            str(value or "")
            for value in row.values()
            if not isinstance(value, (list, dict, set))
        ).casefold()
        if search and search not in searchable:
            continue
        filtered_documents.append(row)

    st.caption(
        f"Visible after explicit filters: {len(filtered_documents)} / {len(documents)} documents. "
        "No filter mutates the loaded inventory; reset returns to all records."
    )
    count_mode = st.selectbox(
        "Heat unit · entity types are never summed together",
        ("Documents", "Data products", "Indicators", "Variables", "Observations"),
        key="v1_heat_unit",
    )
    source_ids = {
        row["source_id"]
        for row in filtered_documents
    }
    all_document_source_ids = {row["source_id"] for row in documents}
    filters_active = bool(search) or any(bool(values) for values in selected.values())
    entity_configs = {
        "Documents": ("sources", "source_id", ("title",)),
        "Data products": ("data_products", "data_product_id", ("data_product_name", "title")),
        "Indicators": ("indicators", "indicator_id", ("indicator_name", "indicator_code")),
        "Variables": ("variables", "variable_id", ("variable_name",)),
        "Observations": ("observations", "observation_id", ("variable_id",)),
    }
    entity, id_field, name_fields = entity_configs[count_mode]
    heat_records = []
    if count_mode == "Documents":
        heat_records = [
            {
                **row,
                "_count_id": row["source_id"],
                "_parents": row["_parents"],
                "_time_bin": row["_time_bin"],
            }
            for row in filtered_documents
        ]
    else:
        seen_entities = set()
        for row_index, row in enumerate(_entity_rows(inventory, entity)):
            raw_source_id = _value(row, "source_id", default="")
            source_id = inventory["source_aliases"].get(raw_source_id, raw_source_id)
            if source_id in all_document_source_ids and source_id not in source_ids:
                continue
            item_id = _value(row, id_field, default="") or f"ROW_{row_index + 1}"
            entity_key = (source_id, item_id)
            if entity_key in seen_entities:
                continue
            seen_entities.add(entity_key)
            source = _source_record(inventory, source_id)
            observation_time = _value(
                row,
                "observed_time",
                "observation_period",
                "observation_year",
                default=_value(source, "observed_time", "observation_period", "observation_year", default=""),
            )
            item_time_bin = _time_bin({"observed_time": observation_time})
            item_parents = sorted(
                parent_assignments.get(source_id, set()),
                key=parents.index,
            ) or ["UNMAPPED / REVIEW_REQUIRED"]
            if source_id not in all_document_source_ids and filters_active:
                orphan_values = {
                    "parent": set(item_parents),
                    "time": {item_time_bin},
                    "publication": {
                        _value(row, "publication_time", "publication_year", default="")
                    },
                    "substance": {_value(row, "substance", default="")},
                    "age": {_value(row, "original_age", "original_age_group", default="")},
                    "geography": {
                        _value(row, "geography_level", "geographic_level", default="")
                    },
                    "source_type": {
                        _value(row, "source_type", "record_entity_type", default="")
                    },
                    "access": {_value(row, "access_rule", "access_status", default="")},
                    "review": {_value(row, "review_status", default="")},
                    "box": {_value(row, "operational_box_id", default="")},
                }
                if any(
                    selection and not (selection & orphan_values[name])
                    for name, selection in selected.items()
                ):
                    continue
                orphan_search_text = " ".join(
                    str(value or "") for value in row.values() if value is not None
                ).casefold()
                if search and search not in orphan_search_text:
                    continue
            record = {
                **source,
                **row,
                "source_id": source_id,
                "_count_id": item_id,
                "_parents": item_parents,
                "_time_bin": item_time_bin,
                "_item_name": _value(row, *name_fields),
            }
            heat_records.append(record)

    heat_counts = Counter(
        (parent, row["_time_bin"])
        for row in heat_records
        for parent in row["_parents"]
        if parent in parent_axis
    )
    z = [[heat_counts[(parent, period)] for period in TIME_BINS] for parent in parent_axis]
    products_by_source = defaultdict(set)
    for product_index, product in enumerate(_entity_rows(inventory, "data_products")):
        raw_source_id = _value(product, "source_id", default="")
        source_id = inventory["source_aliases"].get(raw_source_id, raw_source_id)
        products_by_source[source_id].add(
            _value(product, "data_product_id", default=f"ROW_{product_index + 1}")
        )
    hover = []
    for parent in parent_axis:
        hover_row = []
        for period in TIME_BINS:
            cell_rows = [
                row
                for row in heat_records
                if parent in row["_parents"] and row["_time_bin"] == period
            ]
            cell_source_ids = {row.get("source_id", "") for row in cell_rows}
            family_ids = {
                row.get("source_family_id", row.get("source_id"))
                for row in documents
                if row["source_id"] in cell_source_ids
            }
            product_count = sum(
                len(products_by_source.get(source_id, set()))
                for source_id in cell_source_ids
            )
            hover_row.append(
                f"{parent}<br>{period}<br>{count_mode}: {heat_counts[(parent, period)]}"
                f"<br>Distinct source families: {len(family_ids)}"
                f"<br>Data products: {product_count}"
            )
        hover.append(hover_row)
    maximum = max((max(line) for line in z), default=0)
    display_time_bins = [
        "2010-2014",
        "2015-2019",
        "2020-2022",
        "2023-2026",
        "Unknown observation time",
    ]
    display_parent_axis = [_compact_parent_label(parent) for parent in parent_axis]
    fig = matrix(
        display_time_bins,
        display_parent_axis,
        z,
        f"{count_mode} by Layer A parent × observation time · RULE_DERIVED counts",
        [[0.0, "#17222C"], [0.45, "#4B918C"], [1.0, "#B58B48"]],
        text=[[str(value) for value in line] for line in z],
        hovertext=hover,
        zmax=max(maximum, 1),
    )
    fig.update_layout(
        height=max(550, 44 * len(parent_axis) + 150),
        margin={"l": 220, "r": 30, "t": 70, "b": 90},
    )
    fig.update_xaxes(tickangle=-15, automargin=True)
    fig.update_traces(colorbar={"title": count_mode})
    st.plotly_chart(fig, width="stretch", theme=None, key="v1_topic_heatmap")
    st.caption(
        f"{count_mode}: {len({row['_count_id'] for row in heat_records})} unique entities shown. "
        f"Documents: {len(documents)} · source families: "
        f"{len({row['source_family'] for row in documents})} · data-product rows: "
        f"{len(_entity_rows(inventory, 'data_products'))}. "
        "Multi-topic records count once globally; parent totals may be non-additive. "
        "Publication time is never substituted for observation time. The final time bin is "
        "OBSERVATION_PERIOD_UNKNOWN."
    )

    with st.expander("Temporal density · known observation years only", expanded=False):
        st.markdown(
            "**What this visual means:** bars are RULE_DERIVED counts of documents with an "
            "explicit observation year. Each topic has its own subplot; no smoothing or "
            "interpolation occurs across nominal topic rows."
        )
        selected_years = []
        for row in filtered_documents:
            period = _year_range(_value(row, "observed_time", "observation_year", default=""))
            if period:
                selected_years.append((row, period))
        trend_fig = make_subplots(
            rows=len(parent_axis),
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.012,
            subplot_titles=parent_axis,
        )
        for row_index, parent in enumerate(parent_axis, start=1):
            year_counts = Counter()
            for document, year_range in selected_years:
                if parent not in document["_parents"]:
                    continue
                for year in range(max(2010, year_range[0]), min(2026, year_range[1]) + 1):
                    year_counts[year] += 1
            years = list(range(2010, 2027))
            counts_by_year = [year_counts[year] for year in years]
            trend_fig.add_trace(
                go.Bar(
                    x=years,
                    y=counts_by_year,
                    marker_color="#4B918C",
                    opacity=0.75,
                    name=parent,
                    showlegend=False,
                    hovertemplate=f"{parent}<br>%{{x}}<br>Documents: %{{y}}<extra></extra>",
                ),
                row=row_index,
                col=1,
            )
        trend_fig.update_layout(
            paper_bgcolor="#0B1016",
            plot_bgcolor="#0A1119",
            font={"color": "#E8EEF2"},
            height=max(420, len(parent_axis) * 90),
            margin={"l": 20, "r": 20, "t": 55, "b": 30},
            title="Observed-year document density · unknown-year documents excluded from curves",
        )
        trend_fig.update_xaxes(showgrid=True, gridcolor="#26333D", range=[2010, 2026])
        trend_fig.update_yaxes(showgrid=True, gridcolor="#26333D", rangemode="tozero")
        st.plotly_chart(trend_fig, width="stretch", theme=None, key="v1_temporal_density")
        st.caption(
            f"Known observation-year documents plotted: {len(selected_years)} · unknown "
            f"observation-time documents remain in the heatmap's final bin: "
            f"{sum(row['_time_bin'] == TIME_BINS[-1] for row in filtered_documents)}."
        )

    with st.expander("Semantic evidence landscape · TF-IDF + PCA", expanded=False):
        st.markdown(
            "**What this visual means:** document, measure, and claim text is transformed "
            "with word-level TF-IDF and projected by deterministic PCA. Contours estimate "
            "density only in this declared text-projection space. Positions are RULE_DERIVED, "
            "not geography, time, or a directly interpretable measurement."
        )
        semantic_records = _semantic_projection(inventory)
        coordinates = _tfidf_pca(semantic_records)
        parent_palette = [
            "#4B918C", "#B58B48", "#A34D42", "#4D78A8", "#9B70B3",
            "#6A9B6F", "#C47D51", "#5A9CA5", "#9C8A56", "#7D7DAD",
        ]
        parent_colors = {
            parent: parent_palette[index % len(parent_palette)]
            for index, parent in enumerate(parents)
        }
        point_colors = [
            "#E8EEF2"
            if record["type"] == "CLAIM"
            else parent_colors.get(record["parent"], "#454B50")
            for record in semantic_records
        ]
        semantic_fig = go.Figure()
        if semantic_records:
            semantic_fig.add_trace(
                go.Histogram2dContour(
                    x=coordinates[:, 0],
                    y=coordinates[:, 1],
                    ncontours=8,
                    colorscale=[[0, "#1B2A31"], [1, "#B58B48"]],
                    opacity=0.35,
                    showscale=False,
                    hoverinfo="skip",
                    contours={"coloring": "fill", "showlines": True},
                    name="TF-IDF point density",
                )
            )
            semantic_fig.add_trace(
                go.Scatter(
                    x=coordinates[:, 0],
                    y=coordinates[:, 1],
                    mode="markers",
                    marker={
                        "size": [
                            12 if record["type"] == "DOCUMENT" else 9
                            for record in semantic_records
                        ],
                        "color": point_colors,
                        "line": {"color": "#E8EEF2", "width": 0.5},
                        "opacity": 0.88,
                    },
                    customdata=[
                        [
                            record["type"],
                            record["id"],
                            record["title"],
                            record["source_id"],
                            record["url"],
                            record["parent"],
                        ]
                        for record in semantic_records
                    ],
                    text=[record["title"] for record in semantic_records],
                    hovertemplate=(
                        "%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]}"
                        "<br>Source: %{customdata[3]}<br>Parent: %{customdata[5]}"
                        "<br>%{customdata[4]}<extra>RULE_DERIVED TF-IDF/PCA</extra>"
                    ),
                    name="Evidence universe",
                )
            )
        semantic_fig.update_layout(
            paper_bgcolor="#0B1016",
            plot_bgcolor="#0A1119",
            font={"color": "#E8EEF2"},
            height=690,
            title="Text landscape · document / measure / claim points with density contours",
            xaxis_title="Semantic dimension 1 · PCA",
            yaxis_title="Semantic dimension 2 · PCA",
            margin={"l": 40, "r": 20, "t": 60, "b": 45},
        )
        st.plotly_chart(
            semantic_fig,
            width="stretch",
            theme=None,
            key="v1_semantic_landscape",
        )
        st.caption(
            f"Points: {len(semantic_records)} · documents {sum(r['type'] == 'DOCUMENT' for r in semantic_records)} · "
            f"measures {sum(r['type'] != 'DOCUMENT' and r['type'] != 'CLAIM' for r in semantic_records)} · "
            f"claims {sum(r['type'] == 'CLAIM' for r in semantic_records)}. "
            "No external embedding service or new dependency is used."
        )

    st.markdown("### Layer B boxes and operational detail")
    box_rows = [
        row
        for row in _entity_rows(inventory, "concept_boxes")
        if row.get("box_type") not in {"layer_a_parent", ""}
    ]
    if box_rows:
        st.dataframe(box_rows, hide_index=True, width="stretch")
    else:
        st.info("No operational boxes were loaded.")

    st.markdown("### Documentary provenance · full visible universe")
    detail_rows = []
    for row in filtered_documents:
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
                "source type": _value(row, "source_type", "record_entity_type"),
                "access": _value(row, "access_rule", "access_status"),
                "review status": _value(row, "review_status"),
                "source family": row["source_family"],
                "data products": sum(
                    1
                    for product in _entity_rows(inventory, "data_products")
                    if product.get("source_id") == row["source_id"]
                ),
            }
        )
    st.dataframe(
        detail_rows,
        hide_index=True,
        width="stretch",
        column_config={
            "URL/DOI": st.column_config.LinkColumn(
                "URL/DOI", display_text="Open source"
            )
        },
    )

    all_layer_names = {
        "Data products": "data_products",
        "Indicators": "indicators",
        "Variables": "variables",
        "Observations": "observations",
        "Gap claims": "gap_claims",
        "Alignments": "alignments",
        "Barriers": "barriers",
        "Search runs": "search_runs",
        "Search candidates": "search_candidates",
        "Mappings": "mapping",
    }
    counts = [
        {
            "entity layer": label,
            "seed rows": len(inventory["raw"][entity][0]),
            "candidate rows": len(inventory["raw"][entity][1]),
            "total rows": sum(len(rows) for rows in inventory["raw"][entity]),
        }
        for label, entity in all_layer_names.items()
    ]
    st.markdown("### Linked evidence layers · separate entity levels")
    st.dataframe(counts, hide_index=True, width="stretch")
    layer_choice = st.selectbox(
        "Inspect raw linked layer",
        tuple(all_layer_names),
        key="v1_raw_layer_choice",
    )
    raw_layer = all_layer_names[layer_choice]
    st.dataframe(
        _entity_rows(inventory, raw_layer),
        hide_index=True,
        width="stretch",
    )
    if inventory["duplicate_sources"]:
        with st.expander(f"Exact source duplicates retained in audit trail ({len(inventory['duplicate_sources'])})"):
            st.dataframe(
                inventory["duplicate_sources"],
                hide_index=True,
                width="stretch",
            )
    if inventory["unparsed_rows"]:
        with st.expander(f"Raw rows with extra CSV fields ({len(inventory['unparsed_rows'])})"):
            st.dataframe(
                inventory["unparsed_rows"],
                hide_index=True,
                width="stretch",
            )


def render_view_b(inventory):
    st.markdown("# View B · Claim & Measure Audit")
    st.markdown(
        "Complete exploratory claim × measure matrix. Relevance is a calculated navigation "
        "layer; stored assessment classes remain a separate, provenance-backed layer."
    )
    _fixed_method_content()
    all_claims = _claims(inventory)
    all_measures = _measure_records(inventory)
    alignment_rows, alignment_lookup = _alignment_lookup(inventory)
    parents, parent_assignments = _source_parent_assignments(inventory)

    st.markdown("### Matrix controls")
    control_columns = st.columns(3)
    claim_search = control_columns[0].text_input(
        "Search claims", key="v1_claim_search"
    ).casefold()
    measure_search = control_columns[1].text_input(
        "Search measures / sources", key="v1_measure_search"
    ).casefold()
    display_layer = control_columns[2].selectbox(
        "Cell fill",
        ("Exploratory relevance R", "Stored alignment class"),
        key="v1_matrix_layer",
    )
    filter_columns = st.columns(3)
    selected_parents = filter_columns[0].multiselect(
        "Filter Layer A parents",
        [*parents, "UNMAPPED / REVIEW_REQUIRED"],
        key="v1_matrix_parent_filter",
    )
    selected_measure_types = filter_columns[1].multiselect(
        "Measure entity type",
        ("INDICATOR", "VARIABLE", "OBSERVATION"),
        key="v1_matrix_type_filter",
    )
    selected_claim_status = filter_columns[2].multiselect(
        "Claim provenance",
        sorted({claim["status"] for claim in all_claims}),
        key="v1_matrix_claim_status",
    )

    claims = [
        claim
        for claim in all_claims
        if (not claim_search or claim_search in f"{claim['label']} {claim.get('description', '')}".casefold())
        and (not selected_claim_status or claim["status"] in selected_claim_status)
    ]
    measures = []
    for measure in all_measures:
        source = _source_record(inventory, measure.get("source_id", ""))
        measure_parents = parent_assignments.get(measure.get("source_id", "")) or {
            "UNMAPPED / REVIEW_REQUIRED"
        }
        searchable = " ".join(
            [
                measure["_measure_label"],
                measure["_definition"],
                _value(source, "source_id"),
                _value(source, "title"),
                _value(measure, "substance"),
            ]
        ).casefold()
        if measure_search and measure_search not in searchable:
            continue
        if selected_parents and not (set(selected_parents) & measure_parents):
            continue
        if selected_measure_types and measure["_measure_type"] not in selected_measure_types:
            continue
        measures.append(measure)

    st.caption(
        f"Visible matrix: {len(claims)} claims × {len(measures)} measures = "
        f"{len(claims) * len(measures)} cells. Empty filters include the full universe."
    )
    if not claims or not measures:
        st.info("No rows match the active filters; clear searches or selections to show all.")
        return

    states = []
    scores = []
    coverages = []
    hover = []
    state_counts = Counter()
    component_rows = []
    for claim in claims:
        state_row = []
        score_row = []
        coverage_row = []
        hover_row = []
        for measure in measures:
            measure_ids = {
                measure.get("_measure_id", ""),
                measure.get("_measure_key", ""),
                measure.get("variable_id", ""),
                measure.get("indicator_id", ""),
                measure.get("indicator_code", ""),
                measure.get("variable_name", ""),
            }
            measure_ids.discard("")
            stored = []
            for claim_id in claim["match_ids"]:
                for observed_id in measure_ids:
                    stored.extend(alignment_lookup.get((claim_id, observed_id), []))
            stored = list({id(row): row for row in stored}.values())
            stored_classes = sorted(
                {
                    _value(row, "relationship_class")
                    for row in stored
                    if _value(row, "relationship_class")
                    in {*ALIGNMENT_CLASSES, "NOT_APPLICABLE"}
                }
            )
            if not stored_classes:
                state = "NOT_ASSESSED"
            elif len(stored_classes) == 1:
                state = stored_classes[0]
            else:
                state = "MULTIPLE_STORED"
            state_row.append(state)
            state_counts.update(stored_classes if stored_classes else [state])
            source = _source_record(inventory, measure.get("source_id", ""))
            components = _relevance_components(
                claim,
                measure,
                source,
                parent_assignments,
            )
            score, coverage = _relevance_score(components)
            score_row.append(score)
            coverage_row.append(coverage)
            component_rows.append(
                {
                    "claim": claim["id"],
                    "measure": measure["_measure_key"],
                    "source_id": _value(source, "source_id"),
                    "R": score,
                    "coverage C": coverage,
                    **{
                        name: "UNKNOWN" if value is None else f"{value:.3f}"
                        for name, value in components.items()
                    },
                    "stored class": " / ".join(stored_classes) or "NOT_ASSESSED",
                }
            )
            component_text = "<br>".join(
                f"{name}: {'UNKNOWN' if value is None else f'{value:.2f}'}"
                for name, value in components.items()
            )
            reason_text = "; ".join(
                sorted(
                    {
                        _value(row, "relationship_reason")
                        for row in stored
                    }
                )
            ) or "No stored alignment row"
            evidence_text = "; ".join(
                sorted(
                    {
                        _value(row, "evidence_reference")
                        for row in stored
                    }
                )
            ) or "UNKNOWN"
            loss_text = "; ".join(
                sorted({_value(row, "measurement_loss") for row in stored})
            ) or "UNKNOWN"
            limitation_text = "; ".join(
                sorted(
                    {_value(row, "identification_limitation") for row in stored}
                )
            ) or "UNKNOWN"
            stored_statuses = "; ".join(
                sorted({_value(row, "review_status") for row in stored})
            ) or _value(measure, "review_status")
            hover_row.append(
                "<br>".join(
                    [
                        f"Claim: {claim['label']}",
                        f"Claim provenance: {claim['status']}",
                        f"Measure: {measure['_measure_label']}",
                        f"Definition: {measure['_definition']}",
                        f"Source: {_value(source, 'title')} ({_value(source, 'source_id')})",
                        f"URL/DOI: {_value(source, 'source_url_or_doi')}",
                        f"Observation time: {_value(measure, 'observed_time', 'observation_period', 'observation_year')}",
                        f"Publication time: {_value(measure, 'publication_time', 'publication_year')}",
                        f"Age: {_value(measure, 'original_age', 'original_age_group')}",
                        f"Geography: {_value(measure, 'geography_level', 'geographic_level')}",
                        f"Unit: {_value(measure, 'unit')}",
                        f"Denominator: {_value(measure, 'denominator')}",
                        f"R: {'UNKNOWN' if score is None else f'{score:.3f}'} · coverage C: {coverage:.3f}",
                        component_text,
                        f"Stored class: {' / '.join(stored_classes) or 'NOT_ASSESSED (display-only)'}",
                        f"Reason(s): {reason_text}",
                        f"Evidence reference(s): {evidence_text}",
                        f"Measurement loss: {loss_text}",
                        f"Identification limitation: {limitation_text}",
                        f"Review status: {stored_statuses}",
                        "R is RULE_DERIVED exploratory relevance, never a stored or human-approved alignment.",
                    ]
                )
            )
        states.append(state_row)
        scores.append(score_row)
        coverages.append(coverage_row)
        hover.append(hover_row)

    labels_x = [measure["_measure_key"] for measure in measures]
    labels_y = [claim["id"] for claim in claims]
    if display_layer == "Exploratory relevance R":
        relevance_values = [
            [-1 if score is None else score for score in row]
            for row in scores
        ]
        fig = matrix(
            labels_x,
            labels_y,
            relevance_values,
            "Exploratory relevance R · RULE_DERIVED, not evidence fit",
            [
                [0.0, "#454B50"],
                [0.249, "#454B50"],
                [0.25, "#26333D"],
                [0.55, "#4B918C"],
                [0.8, "#B58B48"],
                [1.0, "#A34D42"],
            ],
            hovertext=hover,
            zmax=1,
        )
        fig.update_traces(
            zmin=-1,
            zmax=1,
            showscale=True,
            colorbar={
                "title": "R score<br>UNKNOWN at -1",
                "tickvals": [-1, 0, 0.5, 1],
                "ticktext": ["UNKNOWN", "0", "0.5", "1"],
            },
        )
    else:
        state_names = [
            *ALIGNMENT_CLASSES,
            "NOT_APPLICABLE",
            "NOT_ASSESSED",
            "MULTIPLE_STORED",
        ]
        state_index = {state: index for index, state in enumerate(state_names)}
        state_values = [
            [state_index.get(state, state_index["NOT_ASSESSED"]) for state in row]
            for row in states
        ]
        fig = matrix(
            labels_x,
            labels_y,
            state_values,
            "Stored alignment classes · NOT_ASSESSED is display-only",
            categorical_scale(state_names, DISPLAY_COLORS),
            text=states,
            hovertext=hover,
            zmax=len(state_names) - 1,
        )
    fig.update_layout(
        height=max(620, min(1250, 38 * len(claims) + 250)),
        margin={"l": 150, "r": 35, "t": 65, "b": 230},
    )
    fig.update_xaxes(tickangle=-60, automargin=True, tickfont={"size": 9})
    fig.update_yaxes(automargin=True, tickfont={"size": 10})
    st.plotly_chart(
        fig,
        width="stretch",
        theme=None,
        key="v1_claim_measure_matrix",
    )
    st.caption(
        "Exploratory relevance ≠ direct evidence fit. A high R does not create, promote, or "
        "substitute for a stored alignment. UNKNOWN components reduce coverage rather than "
        "excluding a cell."
    )

    total_cells = len(claims) * len(measures)
    stored_cell_count = sum(
        state not in {"NOT_ASSESSED", "MULTIPLE_STORED"}
        for row in states
        for state in row
    ) + sum(state == "MULTIPLE_STORED" for row in states for state in row)
    state_cell_counts = Counter(state for row in states for state in row)
    st.markdown("### Matrix and stored-state counts")
    metrics = st.columns(5)
    for column, label, value in zip(
        metrics,
        ("Claims", "Measures", "All cells", "Cells with stored class", "NOT_ASSESSED"),
        (
            len(claims),
            len(measures),
            total_cells,
            stored_cell_count,
            state_cell_counts["NOT_ASSESSED"],
        ),
    ):
        column.metric(label, value)
    st.dataframe(
        [
            {
                "state": state,
                "display cells": state_cell_counts[state],
                "definition": (
                    "Display-only neutral state; no stored alignment row"
                    if state == "NOT_ASSESSED"
                    else "Multiple distinct stored classes matched; inspect cell provenance"
                    if state == "MULTIPLE_STORED"
                    else "Exact stored class; not altered by exploratory R"
                ),
            }
            for state in [
                *ALIGNMENT_CLASSES,
                "NOT_APPLICABLE",
                "NOT_ASSESSED",
                "MULTIPLE_STORED",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.markdown("### Every cell · relevance components and provenance")
    st.dataframe(
        component_rows,
        hide_index=True,
        width="stretch",
    )

    st.markdown("### Complete claim inventory")
    st.dataframe(
        [
            {
                "claim_id": claim["id"],
                "claim": claim["label"],
                "definition": claim.get("description", "UNKNOWN"),
                "provenance": claim["status"],
                "source_id": claim.get("source_id", "UNKNOWN"),
            }
            for claim in claims
        ],
        hide_index=True,
        width="stretch",
    )

    st.markdown("### Grouped measure lineage · Layer A → source → product")
    st.dataframe(
        [
            {
                "Layer A parent": "; ".join(
                    sorted(
                        parent_assignments.get(measure.get("source_id", ""), set())
                    )
                )
                or "UNMAPPED / REVIEW_REQUIRED",
                "source_id": _value(_source_record(inventory, measure.get("source_id", "")), "source_id"),
                "source": _value(_source_record(inventory, measure.get("source_id", "")), "title"),
                "data_product_id": measure["_product_id"],
                "data product": measure["_product_name"],
                "measure type": measure["_measure_type"],
                "measure_id": measure["_measure_id"],
                "measure": measure["_measure_label"],
                "definition": measure["_definition"],
                "observations": measure["_observation_count"],
                "observation detail": measure["_observation_details"],
                "review status": _value(measure, "review_status"),
            }
            for measure in measures
        ],
        hide_index=True,
        width="stretch",
    )

    measured_source_ids = {row.get("source_id") for row in measures}
    contextual = [
        row
        for row in inventory["sources"]
        if row.get("source_id") not in measured_source_ids
    ]
    st.markdown("### Contextual documents · no measure linked")
    st.caption(
        "Documents remain visible as context and are not fabricated into observed-variable columns."
    )
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
        width="stretch",
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
        "Production relationships are drawn from explicit lineage and role fields. Unknown "
        "roles do not hide products or suppress independently documented edges."
    )
    _fixed_method_content()
    rows = _product_records(inventory)
    st.caption(f"Data product/document rows: {len(rows)}")
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        column_config={
            "source_link": st.column_config.LinkColumn(
                "source link", display_text="Open source"
            )
        },
    )
    st.markdown("### Evidence production network")
    st.markdown(
        "**What this visual means:** layout is a deterministic force-directed graph "
        "(seed 2026), not geographic. Arrows are explicit source/product/measure foreign-key "
        "lineage or source-recorded production roles; each edge tooltip includes its evidence "
        "reference. Unknown roles are shown as disconnected badges, never as inferred edges."
    )
    graph_controls = st.columns(2)
    edge_mode = graph_controls[0].selectbox(
        "Relationship layer",
        ("Documented only", "Include MODEL_SUGGESTED relationships"),
        key="v1_flow_edge_mode",
    )
    show_unknown = graph_controls[1].checkbox(
        "Show UNKNOWN role slots",
        value=True,
        key="v1_flow_unknown_roles",
    )

    graph = nx.DiGraph()
    node_details = {}
    source_by_id = {row.get("source_id", ""): row for row in inventory["sources"]}
    source_products = defaultdict(list)
    product_nodes = {}
    source_nodes = {}
    edge_records = []
    role_types = {
        "funder": "funded_by",
        "collector": "collected_by",
        "producer": "produced_by",
        "indicator_authority": "indicator_defined_by",
        "custodian": "held_by/custodied_by",
        "reported_to": "reported_to",
        "access_authority": "accessible_through",
    }

    def add_node(node_id, kind, label, details, color):
        graph.add_node(node_id, kind=kind)
        node_details[node_id] = {
            "kind": kind,
            "label": label,
            "details": details,
            "color": color,
        }

    def add_edge(from_id, to_id, relation, reference, provenance="OBSERVED"):
        if not reference or _is_unknown(reference):
            return
        edge = {
            "from": from_id,
            "to": to_id,
            "relation": relation,
            "reference": reference,
            "provenance": provenance,
        }
        edge_records.append(edge)
        graph.add_edge(from_id, to_id, relation=relation, provenance=provenance)

    for source in inventory["sources"]:
        source_id = _value(source, "source_id")
        node_id = f"source:{source_id}"
        source_nodes[source_id] = node_id
        add_node(
            node_id,
            "Source document",
            source_id,
            f"{_value(source, 'title')}<br>{_value(source, 'source_url_or_doi')}",
            "#4B918C",
        )

    actual_products = _entity_rows(inventory, "data_products")
    for product in actual_products:
        source_id = _value(product, "source_id", default="")
        canonical_source_id = inventory["source_aliases"].get(source_id, source_id)
        product_id = _value(product, "data_product_id", default="")
        if not product_id:
            continue
        node_id = f"product:{canonical_source_id}:{product_id}"
        product_nodes[(canonical_source_id, product_id)] = node_id
        source_products[canonical_source_id].append(node_id)
        source = source_by_id.get(canonical_source_id, {})
        add_node(
            node_id,
            "Data product",
            product_id,
            f"{_value(product, 'data_product_name', 'title')}<br>Source: {canonical_source_id}",
            "#B58B48",
        )
        source_node = source_nodes.get(canonical_source_id)
        if source_node:
            add_edge(
                source_node,
                node_id,
                "source_has_data_product",
                _value(source, "source_url_or_doi"),
            )

    for entity, kind, id_fields, name_fields, color in (
        ("indicators", "Indicator", ("indicator_id", "indicator_code"), ("indicator_name", "indicator_code"), "#7594B8"),
        ("variables", "Variable", ("variable_id",), ("variable_name",), "#9B70B3"),
    ):
        for index, row in enumerate(_entity_rows(inventory, entity)):
            source_id = _value(row, "source_id", default="")
            source_id = inventory["source_aliases"].get(source_id, source_id)
            item_id = _value(row, *id_fields, default="") or f"ROW_{index + 1}"
            node_id = f"{kind.casefold()}:{source_id}:{item_id}"
            label = _value(row, *id_fields, default=item_id)
            add_node(
                node_id,
                kind,
                label,
                f"{_value(row, *name_fields)}<br>Source: {source_id}<br>"
                f"Definition: {_value(row, 'variable_definition', 'indicator_definition', 'definition_verbatim')}",
                color,
            )
            matching_product_id = _value(row, "data_product_id", default="")
            matching_product = product_nodes.get((source_id, matching_product_id))
            if not matching_product and len(source_products.get(source_id, [])) == 1:
                matching_product = source_products[source_id][0]
            reference = _value(
                row,
                "source_url_or_doi",
                default=_value(source_by_id.get(source_id, {}), "source_url_or_doi"),
            )
            parent_node = matching_product or source_nodes.get(source_id)
            if parent_node:
                add_edge(
                    parent_node,
                    node_id,
                    "data_product_has_measure" if matching_product else "source_documents_measure",
                    reference,
                )

    variable_nodes = {}
    for node_id, details in node_details.items():
        if details["kind"] == "Variable":
            variable_nodes[node_id.split(":", 1)[1]] = node_id
    for index, observation in enumerate(_entity_rows(inventory, "observations")):
        source_id = _value(observation, "source_id", default="")
        source_id = inventory["source_aliases"].get(source_id, source_id)
        observation_id = _value(observation, "observation_id", default=f"ROW_{index + 1}")
        variable_id = _value(observation, "variable_id", default="")
        node_id = f"observation:{source_id}:{observation_id}"
        add_node(
            node_id,
            "Observation",
            observation_id,
            f"Variable: {variable_id or 'UNKNOWN'}<br>"
            f"Value: {_value(observation, 'value')}<br>"
            f"Time: {_value(observation, 'observed_time', 'observation_period')}<br>"
            f"Unit: {_value(observation, 'unit')}<br>"
            f"Geography: {_value(observation, 'geography_level', 'geographic_level')}",
            "#D17A5B",
        )
        parent_node = variable_nodes.get(f"{source_id}:{variable_id}") if variable_id else None
        if not parent_node:
            parent_node = source_nodes.get(source_id)
        if parent_node:
            source = source_by_id.get(source_id, {})
            add_edge(
                parent_node,
                node_id,
                "variable_has_observation" if variable_id else "source_has_observation",
                _value(observation, "source_url_or_doi", default=_value(source, "source_url_or_doi")),
            )

    unknown_nodes = []
    for row in rows:
        source_id = inventory["source_aliases"].get(row["source_id"], row["source_id"])
        product_id = row["data_product_id"]
        product_node = product_nodes.get((source_id, product_id))
        target_node = product_node or source_nodes.get(source_id)
        if not target_node:
            continue
        for role, relation in role_types.items():
            actor_name = row.get(role, "UNKNOWN")
            if _is_unknown(actor_name):
                if show_unknown:
                    unknown_id = f"unknown:{target_node}:{role}"
                    if unknown_id not in node_details:
                        add_node(
                            unknown_id,
                            "UNKNOWN role slot",
                            f"UNKNOWN · {role}",
                            f"Role is not documented for {product_id}; no edge is drawn.",
                            "#454B50",
                        )
                        unknown_nodes.append(unknown_id)
                continue
            actor_id = f"actor:{role}:{actor_name}"
            if actor_id not in node_details:
                add_node(
                    actor_id,
                    f"Actor · {role}",
                    actor_name,
                    f"Role: {role}<br>Explicitly recorded in the source/data-production row.",
                    "#D2A95F",
                )
            source = source_by_id.get(source_id, {})
            evidence_reference = row.get("evidence_reference", "UNKNOWN")
            if _is_unknown(evidence_reference):
                evidence_reference = _value(source, "source_url_or_doi", default="")
            add_edge(
                actor_id,
                target_node,
                relation,
                evidence_reference,
            )

    documented_count = sum(edge["provenance"] == "OBSERVED" for edge in edge_records)
    suggested_count = sum(edge["provenance"] == "MODEL_SUGGESTED" for edge in edge_records)
    if edge_mode == "Documented only":
        visible_edges = [edge for edge in edge_records if edge["provenance"] == "OBSERVED"]
    else:
        visible_edges = edge_records
        st.info(
            f"No MODEL_SUGGESTED production-role edges are stored in the loaded candidate data "
            f"({suggested_count}); no role edges are inferred. Showing all {documented_count} documented edges."
        )
    st.caption(
        f"Nodes: {graph.number_of_nodes()} · documented edges: {documented_count} · "
        f"model-suggested edges in input: {suggested_count} · unknown role slots: {len(unknown_nodes)}."
    )
    if graph.number_of_nodes():
        positions = _spring_layout_coordinates(
            tuple(graph.nodes),
            tuple(graph.edges),
        )
        figure = go.Figure()
        edge_palette = {
            "source_has_data_product": "#4B918C",
            "data_product_has_measure": "#B58B48",
            "source_documents_measure": "#7594B8",
            "variable_has_observation": "#D17A5B",
            "source_has_observation": "#D17A5B",
            "funded_by": "#D2A95F",
            "collected_by": "#9B70B3",
            "produced_by": "#6A9B6F",
            "indicator_defined_by": "#4D78A8",
            "held_by/custodied_by": "#A34D42",
            "reported_to": "#5A9CA5",
            "accessible_through": "#9C8A56",
        }
        for relation in sorted({edge["relation"] for edge in visible_edges}):
            relation_edges = [edge for edge in visible_edges if edge["relation"] == relation]
            for edge in relation_edges:
                x0, y0 = positions[edge["from"]]
                x1, y1 = positions[edge["to"]]
                figure.add_trace(
                    go.Scatter(
                        x=[x0, x1],
                        y=[y0, y1],
                        mode="lines",
                        line={"color": edge_palette.get(relation, "#68717A"), "width": 1.4},
                        text=[
                            f"{relation}<br>{edge['provenance']}<br>Evidence: {edge['reference']}"
                        ] * 2,
                        hovertemplate="%{text}<extra></extra>",
                        showlegend=False,
                        name=relation,
                    )
                )
                figure.add_annotation(
                    x=x1,
                    y=y1,
                    ax=x0,
                    ay=y0,
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=0.8,
                    arrowwidth=1,
                    arrowcolor=edge_palette.get(relation, "#68717A"),
                    opacity=0.65,
                )
        node_types = sorted({details["kind"] for details in node_details.values()})
        for node_type in node_types:
            node_ids = [
                node_id
                for node_id, details in node_details.items()
                if details["kind"] == node_type
            ]
            figure.add_trace(
                go.Scatter(
                    x=[positions[node_id][0] for node_id in node_ids],
                    y=[positions[node_id][1] for node_id in node_ids],
                    mode="markers+text",
                    text=[node_details[node_id]["label"] for node_id in node_ids],
                    textposition="top center",
                    textfont={"size": 8},
                    marker={
                        "size": 12 if node_type != "UNKNOWN role slot" else 8,
                        "color": node_details[node_ids[0]]["color"],
                        "line": {"color": "#E8EEF2", "width": 0.6},
                    },
                    customdata=[
                        [
                            node_type,
                            node_details[node_id]["label"],
                            node_details[node_id]["details"],
                        ]
                        for node_id in node_ids
                    ],
                    hovertemplate=(
                        "%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]}"
                        "<extra>Graph node</extra>"
                    ),
                    name=node_type,
                )
            )
        figure.update_layout(
            paper_bgcolor="#0B1016",
            plot_bgcolor="#0A1119",
            font={"color": "#E8EEF2"},
            height=950,
            title="Evidence lineage and production roles · layout coordinates are not geography",
            margin={"l": 10, "r": 10, "t": 55, "b": 10},
            legend={"orientation": "h", "y": -0.02},
            xaxis={"visible": False, "showgrid": False, "zeroline": False},
            yaxis={"visible": False, "showgrid": False, "zeroline": False},
            hovermode="closest",
        )
        st.plotly_chart(
            figure,
            width="stretch",
            theme=None,
            key="v1_production_network",
        )
    else:
        st.info("No source, product, or lineage nodes were loaded.")

    st.markdown("### Edge provenance")
    st.dataframe(
        [
            {
                "from": node_details[edge["from"]]["label"],
                "to": node_details[edge["to"]]["label"],
                "relationship type": edge["relation"],
                "provenance": edge["provenance"],
                "evidence reference": edge["reference"],
            }
            for edge in visible_edges
        ],
        hide_index=True,
        width="stretch",
    )
