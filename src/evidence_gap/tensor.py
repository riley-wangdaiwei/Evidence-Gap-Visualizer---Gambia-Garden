"""One sparse, review-aware tensor shared by both matrix projections."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml

from .schemas import GapState

APPROVED = ("HUMAN_REVIEWED", "SOURCE_VERIFIED")


@dataclass
class EvidenceTensor:
    records: list[dict]
    proxy_records: list[dict] | None = None

    def project_gap(self):
        return [
            {**r, "state": r.get("gap_state",GapState.NOT_SEARCHED_OR_UNKNOWN.value)}
            for r in self.records
        ]

    def project_proxy(self):
        if self.proxy_records is not None:
            return self.proxy_records
        return [{**r, "relation_class": r.get("relation_class") or "UNKNOWN_REQUIRES_REVIEW"}
                for r in self.records if r.get("observed_name") or r.get("observed")]


def _taxonomy(path="config/taxonomy.yaml"):
    p = Path(path)
    if not p.exists():
        return {"targets": [], "populations": ["youth"], "geographies": [{"name": "national", "level": "country"}]}
    value = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "targets": value.get("targets", []),
        "populations": value.get("population_groups", ["youth"]),
        "geographies": value.get("geographies", [{"name": "national", "level": "country"}]),
    }


def _dict(row):
    return dict(row) if row is not None else {}


def from_database(db, taxonomy_path="config/taxonomy.yaml"):
    """Create all configured target × population × geography cells.

    Only approved canonical records contribute evidence. Search state applies
    only to a search explicitly scoped to the same target/population/geography.
    National observations are never copied into subnational cells.
    """
    taxonomy = _taxonomy(taxonomy_path)
    targets = taxonomy["targets"]
    populations = list(taxonomy["populations"])
    geographies = list(taxonomy["geographies"])
    if not targets:
        targets = [dict(r) for r in db.execute(
            "SELECT id, name, definition FROM indicators WHERE is_target=1 ORDER BY name"
        )]
    targets = [({"id": t, "name": t} if isinstance(t, str) else t) for t in targets]
    target_ids={t.get("id") or t.get("name") for t in targets}
    for row in db.execute("SELECT id,name,definition FROM indicators WHERE is_target=1 AND review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED') AND synthetic=0 ORDER BY name"):
        if row["id"] not in target_ids:
            targets.append(dict(row)); target_ids.add(row["id"])
    approved_marks = ",".join("?" for _ in APPROVED)
    for row in db.execute(f"SELECT DISTINCT population FROM observations WHERE review_status IN ({approved_marks}) AND synthetic=0 AND population IS NOT NULL AND population<>''", APPROVED):
        if row[0] not in populations:
            populations.append(row[0])
    legal_levels = set(yaml.safe_load(Path(taxonomy_path).read_text(encoding="utf-8")).get("geographic_levels", [])) if Path(taxonomy_path).exists() else set()
    for row in db.execute(f"SELECT DISTINCT geography, geography_level FROM observations WHERE review_status IN ({approved_marks}) AND synthetic=0", APPROVED):
        configured=[g for g in geographies if isinstance(g,dict)]
        known=any(g.get("name")==row["geography"] or row["geography"] in g.get("aliases",[]) for g in configured)
        if row["geography_level"] in legal_levels and row["geography"] and not known:
            geographies.append({"name": row["geography"], "level": row["geography_level"]})

    cells = {}
    for target in targets:
        for population in populations:
            for geography in geographies:
                geo = {"name": geography, "level": "country"} if isinstance(geography, str) else geography
                target_id = target.get("id") or target.get("name")
                key = (target_id, population, geo["name"])
                cells[key] = {
                    "target": target.get("name", target.get("id")),
                    "target_id": target.get("id", target.get("name")),
                    "target_name": target.get("name", target.get("id")),
                    "population": population,
                    "geography": geo["name"], "geography_level": geo.get("level"),
                    "gap_state": GapState.NOT_SEARCHED_OR_UNKNOWN.value,
                    "flags": [], "source_ids": [], "source_titles": [],
                    "direct_evidence_count": 0, "independent_source_count": 0,
                    "observed": None, "observed_name": None,
                    "relation_class": None, "rationale": None,
                    "observation_period": None, "observation_year": None, "publication_year": None,
                    "age_band": None, "original_definition": None,
                    "review_status": None, "barriers": [], "gap_claims": [],
                }

    query = f"""SELECT o.*, v.original_name, v.age_band, v.definition AS variable_definition,
        v.review_status AS variable_review_status, i.id AS indicator_id, i.name AS indicator_name,
        i.definition AS indicator_definition, i.review_status AS indicator_review_status,
        p.review_status AS product_review_status,
        p.population AS product_population, p.source_id AS product_source_id, s.title AS source_title,
        s.synthetic, s.review_status AS source_review_status, s.publication_year AS source_publication_year, s.access_status, s.underlying_data_id,
        a.target_indicator_id, a.relation_class, a.rationale, a.review_status AS alignment_review_status,
        ti.name AS target_name, als.review_status AS alignment_source_status, als.synthetic AS alignment_source_synthetic
      FROM observations o JOIN variables v ON v.id=o.variable_id
      JOIN indicators i ON i.id=v.indicator_id
      JOIN data_products p ON p.id=i.data_product_id
      JOIN sources s ON s.id=p.source_id
      LEFT JOIN alignments a ON a.observed_indicator_id=i.id
      LEFT JOIN indicators ti ON ti.id=a.target_indicator_id
      LEFT JOIN sources als ON als.id=a.source_id
      WHERE o.review_status IN ({approved_marks}) AND v.review_status IN ({approved_marks})
        AND i.review_status IN ({approved_marks}) AND p.review_status IN ({approved_marks})
        AND s.review_status IN ({approved_marks})
        AND (als.review_status IN ({approved_marks}) OR als.id IS NULL)
        AND COALESCE(o.synthetic,0)=0 AND COALESCE(v.synthetic,0)=0
        AND COALESCE(i.synthetic,0)=0 AND COALESCE(s.synthetic,0)=0"""
    approved = APPROVED * 6
    for row in db.execute(query, approved):
        r = _dict(row)
        for (target_id, population, geography), cell in cells.items():
            target_match = target_id == r.get("target_indicator_id") or cell["target"] == r.get("target_name")
            if not target_match:
                continue
            # Respect the observation's recorded geographic level and value.
            # Only exact area name + level matches contribute to a cell.
            configured_geo=next((g for g in geographies if (g.get("name") if isinstance(g,dict) else g)==geography),{})
            aliases=configured_geo.get("aliases",[]) if isinstance(configured_geo,dict) else []
            geo_match=r.get("geography")==geography or r.get("geography") in aliases
            if not geo_match or r.get("geography_level") != cell["geography_level"]:
                continue
            if r.get("population") not in (None, "", population) and r.get("population") != population:
                continue
            if r.get("alignment_review_status") not in APPROVED or r.get("alignment_source_status") not in APPROVED or r.get("relation_class") != "DIRECT_MATCH":
                if r.get("alignment_review_status") in APPROVED and r.get("alignment_source_status") in APPROVED and r.get("relation_class") not in (None,"DIRECT_MATCH"):
                    cell["flags"].append("INDIRECT_OR_NOT_COMPARABLE_EVIDENCE")
                continue
            cell["direct_evidence_count"] += 1
            cell["source_ids"].append(r.get("product_source_id"))
            cell["source_titles"].append(r.get("source_title"))
            cell["observed"] = r.get("indicator_name")
            cell["observed_name"] = r.get("original_name") or r.get("indicator_name")
            cell["relation_class"] = r.get("relation_class")
            cell["rationale"] = r.get("rationale")
            cell["observation_period"] = cell["observation_period"] or r.get("period")
            cell["observation_year"] = cell["observation_year"] or r.get("observation_year")
            cell["publication_year"] = cell["publication_year"] or r.get("source_publication_year") or r.get("publication_year")
            cell["age_band"] = cell["age_band"] or r.get("age_band")
            cell["original_definition"] = cell["original_definition"] or r.get("variable_definition") or r.get("indicator_definition")
            cell["review_status"] = r.get("alignment_review_status")
            if r.get("temporal_status") == "OUTDATED_OR_TEMPORALLY_MISMATCHED":
                cell["flags"].append("OUTDATED_OR_TEMPORALLY_MISMATCHED")
            if (r.get("access_status") or "").casefold() == "restricted":
                cell["flags"].append("RESTRICTED_ACCESS")

    # National evidence can inform a warning at another level, but its value
    # and source counts never populate that subnational cell.
    for (target_id,population,geography),cell in cells.items():
        if cell["geography_level"]=="country" or cell["direct_evidence_count"]:
            continue
        national=next((other for (tid,pop,geo),other in cells.items()
                       if tid==target_id and pop==population and other["geography_level"]=="country"
                       and other["direct_evidence_count"]>0),None)
        if national:
            cell["flags"].append("INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION")
    for (target_id, population, geography), cell in cells.items():
        cell["barriers"] = [dict(b) for b in db.execute(
            f"SELECT id,barrier_type,description,evidence,source_id,verification_status,review_status FROM barriers WHERE target_id=? AND synthetic=0 AND review_status IN ({approved_marks})",
            (target_id, *APPROVED),
        )]
        for barrier in cell["barriers"]:
            if barrier["barrier_type"]=="ACCESS_RESTRICTED": cell["flags"].append("RESTRICTED_ACCESS")
            if barrier["barrier_type"] in ("MISSING_DISAGGREGATION","GEOGRAPHY_MISMATCH"):
                cell["flags"].append("INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION")
        direct_sources = set(cell["source_ids"])
        lineage = {}
        if direct_sources:
            marks = ",".join("?" for _ in direct_sources)
            for source in db.execute(f"SELECT id, COALESCE(NULLIF(underlying_data_id,''),id) AS lineage FROM sources WHERE id IN ({marks})", tuple(direct_sources)):
                lineage[source["id"]] = source["lineage"]
        cell["independent_source_count"] = len({lineage.get(s, s) for s in direct_sources})
        if "RESTRICTED_ACCESS" in cell["flags"]:
            cell["gap_state"] = GapState.RESTRICTED_ACCESS.value
        elif "OUTDATED_OR_TEMPORALLY_MISMATCHED" in cell["flags"]:
            cell["gap_state"] = GapState.OUTDATED_OR_TEMPORALLY_MISMATCHED.value
        elif cell["independent_source_count"] > 1:
            cell["gap_state"] = GapState.MULTIPLE_INDEPENDENT_DIRECT_SOURCES.value
        elif cell["direct_evidence_count"]:
            cell["gap_state"] = GapState.DIRECT_EVIDENCE_FOUND.value
        elif "INDIRECT_OR_NOT_COMPARABLE_EVIDENCE" in cell["flags"]:
            cell["gap_state"] = GapState.INDIRECT_OR_NOT_COMPARABLE_EVIDENCE.value
        elif "INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION" in cell["flags"]:
            cell["gap_state"] = GapState.INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION.value
        scoped_searches = db.execute(
            f"SELECT status FROM search_runs WHERE target_id=? AND population=? AND geography=? AND review_status IN ({approved_marks})",
            (target_id, population, geography, *APPROVED),
        ).fetchall()
        if not cell["direct_evidence_count"] and cell["gap_state"]==GapState.NOT_SEARCHED_OR_UNKNOWN.value and any(s["status"] == "complete" for s in scoped_searches):
            cell["gap_state"] = GapState.SEARCHED_NO_DIRECT_EVIDENCE_FOUND.value
        elif not cell["direct_evidence_count"] and cell["gap_state"]==GapState.NOT_SEARCHED_OR_UNKNOWN.value and scoped_searches:
            cell["gap_state"] = GapState.SEARCH_INCOMPLETE.value
        for claim in db.execute(
            f"SELECT claim, review_status, source_id FROM gap_claims WHERE target_id=? AND population=? AND geography=? AND synthetic=0 AND review_status IN ({approved_marks})",
            (target_id, population, geography, *APPROVED),
        ):
            cell["gap_claims"].append(dict(claim))
        cell["flags"] = sorted(set(cell["flags"]))

    # View B is a configured-target × approved-observed-variable matrix.
    # Missing relationships are explicit UNKNOWN display cells, never stored
    # or inferred alignments.
    target_names={t.get("id") or t.get("name"):t.get("name") or t.get("id") for t in targets}
    observed_rows=db.execute(f"""SELECT v.id AS variable_id,v.original_name,v.definition AS variable_definition,v.age_band,v.unit AS variable_unit,
        i.id AS observed_indicator_id,i.name AS observed_indicator_name,i.definition AS observed_definition,
        p.id AS data_product_id,p.population,p.geography_level,p.observation_period,
        s.id AS source_id,s.title AS source_title,s.underlying_data_id
        FROM variables v JOIN indicators i ON i.id=v.indicator_id
        JOIN data_products p ON p.id=i.data_product_id JOIN sources s ON s.id=p.source_id
        WHERE v.review_status IN ({approved_marks}) AND i.review_status IN ({approved_marks})
        AND p.review_status IN ({approved_marks}) AND s.review_status IN ({approved_marks})
        AND COALESCE(v.synthetic,0)=0 AND COALESCE(i.synthetic,0)=0
        AND COALESCE(p.synthetic,0)=0 AND COALESCE(s.synthetic,0)=0 ORDER BY i.name,v.original_name""",APPROVED*4).fetchall()
    alignment_rows=db.execute(f"""SELECT a.*,ti.name AS target_name,oi.name AS observed_indicator_name,
        s.title AS source_title,s.underlying_data_id
        FROM alignments a JOIN indicators ti ON ti.id=a.target_indicator_id
        JOIN indicators oi ON oi.id=a.observed_indicator_id
        JOIN sources s ON s.id=a.source_id
        WHERE a.review_status IN ({approved_marks}) AND ti.review_status IN ({approved_marks})
        AND oi.review_status IN ({approved_marks}) AND s.review_status IN ({approved_marks})
        AND COALESCE(a.synthetic,0)=0 AND COALESCE(ti.synthetic,0)=0
        AND COALESCE(oi.synthetic,0)=0 AND COALESCE(s.synthetic,0)=0
        """,APPROVED*4).fetchall()
    alignment_map={}
    for row in alignment_rows:
        item=dict(row); alignment_map.setdefault((item["target_indicator_id"],item["observed_indicator_id"]),[]).append(item)
    proxy_records=[]
    for target_id,target_name in target_names.items():
        for observed in observed_rows:
            obs=dict(observed)
            matches=alignment_map.get((target_id,obs["observed_indicator_id"]),[])
            if matches:
                source_groups={m.get("source_id") or obs["source_id"]:m.get("underlying_data_id") or obs.get("underlying_data_id") or m.get("source_id") or obs["source_id"] for m in matches}
                for relation in matches:
                    proxy_records.append({**obs,**relation,"target_name":target_name,
                        "observed_name":obs["original_name"],"observed_label":f"{obs['original_name']} · {obs['source_title']}","source_id":relation.get("source_id") or obs["source_id"],
                        "source_title":relation.get("source_title") or obs["source_title"],
                        "independent_source_count":len(set(source_groups.values()))})
            else:
                proxy_records.append({**obs,"target_indicator_id":target_id,"target_name":target_name,
                    "observed_name":obs["original_name"],"observed_label":f"{obs['original_name']} · {obs['source_title']}","relation_class":"UNKNOWN_REQUIRES_REVIEW",
                    "rationale":"No reviewed alignment record.","measurement_loss":None,
                    "review_status":None,"derivation_status":None,"independent_source_count":0})
    for cell in cells.values():
        cell["alignments"] = [a for a in proxy_records if a.get("target_indicator_id")==cell["target_id"]]
    return EvidenceTensor(list(cells.values()), proxy_records)
