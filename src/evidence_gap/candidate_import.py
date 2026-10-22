"""Strict CSV bundle import into review queue; never directly approves data."""
import csv
import json
import re
from datetime import date
from pathlib import Path
from .provenance import stable_id,now_iso

REQUIRED_COLUMNS={"source_id","source_title","source_url_or_doi","retrieved_at","bundle_json"}

def _norm_title(value):
    return re.sub(r"\W+","",(value or "").casefold())

def _canonical_url(value):
    return (value or "").strip().rstrip("/").casefold()

def _parse_date(value):
    try: return date.fromisoformat(value)
    except (TypeError,ValueError): raise ValueError("retrieved_at must be an ISO date (YYYY-MM-DD)")

def read_candidate_csv(path_or_file):
    if hasattr(path_or_file,"read"):
        rows=list(csv.DictReader(path_or_file))
    else:
        with Path(path_or_file).open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if not rows: return []
    missing=REQUIRED_COLUMNS-set(rows[0])
    if missing: raise ValueError("Missing CSV columns: "+", ".join(sorted(missing)))
    result=[]
    for line,row in enumerate(rows,start=2):
        title=(row.get("source_title") or "").strip()
        identity=(row.get("source_url_or_doi") or "").strip()
        source_id=(row.get("source_id") or "").strip()
        if not title or not identity or not source_id: raise ValueError(f"CSV row {line}: source_id, source_title and source_url_or_doi are required")
        retrieved=_parse_date((row.get("retrieved_at") or "").strip())
        try: bundle=json.loads(row["bundle_json"])
        except json.JSONDecodeError as exc: raise ValueError(f"CSV row {line}: bundle_json is not valid JSON: {exc}") from exc
        sources=bundle.get("sources") or []
        if len(sources)!=1: raise ValueError(f"CSV row {line}: bundle_json must include exactly one source record")
        source=sources[0]
        source.update({"id":source_id,"title":title,"review_status":"PENDING_HUMAN_REVIEW"})
        if identity.lower().startswith("10."):
            source["doi"]=identity
        else:
            source["url"]=identity
        source["retrieved_at"]=retrieved.isoformat()
        source["synthetic"]=(row.get("synthetic") or "false").casefold() in ("1","true","yes")
        synthetic=source["synthetic"]
        product_ids={record.get("id") for record in bundle.get("data_products",[])}
        indicator_ids={record.get("id") for record in bundle.get("indicators",[])}
        variable_by_id={record.get("id"):record for record in bundle.get("variables",[])}
        if any(record.get("source_id")!=source_id for record in bundle.get("data_products",[])):
            raise ValueError(f"CSV row {line}: each data product must reference source_id {source_id}")
        if any(record.get("data_product_id") not in product_ids for record in bundle.get("indicators",[]) if record.get("data_product_id")):
            raise ValueError(f"CSV row {line}: every indicator data_product_id must link to a bundled data product")
        if any(record.get("indicator_id") not in indicator_ids for record in bundle.get("variables",[])):
            raise ValueError(f"CSV row {line}: every variable indicator_id must link to a bundled indicator")
        for table in ("observations","alignments","gap_claims","barriers","research_claims","macro_series"):
            for record in bundle.get(table,[]):
                if record.get("source_id") not in (None,source_id):
                    raise ValueError(f"CSV row {line}: {table} source_id must match bundle source {source_id}")
                record["source_id"]=source_id
        # Preserve mandatory raw provenance for each imported observation.
        for obs in bundle.get("observations",[]):
            variable=variable_by_id.get(obs.get("variable_id"),{})
            if obs.get("variable_id") not in variable_by_id:
                raise ValueError(f"CSV row {line}: observation variable_id must link to a bundled variable")
            for field in ("source_id","original_variable_name","original_age_band","original_definition","unit","denominator"):
                if field not in obs: obs[field]=None
            obs["source_id"]=source_id
            obs["original_variable_name"]=obs.get("original_variable_name") or variable.get("original_name")
            obs["original_age_band"]=obs.get("original_age_band") or variable.get("age_band")
            obs["original_definition"]=obs.get("original_definition") or variable.get("definition")
            obs["unit"]=obs.get("unit") or variable.get("unit")
            obs["denominator"]=obs.get("denominator") or next((i.get("denominator") for i in bundle.get("indicators",[]) if i.get("id")==variable.get("indicator_id")),None)
            if not obs.get("original_variable_name") or not obs.get("original_definition"):
                raise ValueError(f"CSV row {line}: each observation needs original_variable_name and original_definition")
            if obs.get("unit") is None and not obs.get("denominator"):
                raise ValueError(f"CSV row {line}: each observation needs a unit or denominator")
        links={
            "alignments":lambda r: r.get("source_id")==source_id and r.get("observed_indicator_id") in indicator_ids and r.get("target_indicator_id") in indicator_ids,
            "gap_claims":lambda r: r.get("source_id")==source_id,
            "barriers":lambda r: r.get("source_id") in (None,source_id),
        }
        for table,valid in links.items():
            if any(not valid(record) for record in bundle.get(table,[])):
                raise ValueError(f"CSV row {line}: invalid source/entity links in {table}")
        from .resistance import validate_barrier
        for barrier in bundle.get("barriers",[]):
            validate_barrier(barrier.get("barrier_type"))
        for series in bundle.get("macro_series",[]):
            required=("producer","collected_by","collection_method","frequency","aggregation_level","unit","definition")
            missing=[field for field in required if not series.get(field)]
            if missing:
                raise ValueError(f"CSV row {line}: macro_series missing required metadata: {', '.join(missing)}")
        for table,items in bundle.items():
            if isinstance(items,list) and table!="sources":
                for record in items:
                    if isinstance(record,dict):
                        record["review_status"]="PENDING_HUMAN_REVIEW"
                        record["synthetic"]=synthetic
        result.append({"id":f"candidate_{source_id}","source_id":source_id,"title":title,"identity":identity,
                       "retrieved_at":retrieved.isoformat(),"synthetic":synthetic,
                       "bundle":bundle})
    return result

def enqueue_candidates(db, rows):
    queued=[]
    for item in rows:
        identity=item["identity"]
        is_doi=identity.casefold().startswith("10.")
        sources=[dict(r) for r in db.execute("SELECT id,title,url,doi,underlying_data_id FROM sources")]
        queued_matches=[dict(r) for r in db.execute("SELECT id,url,doi,payload_json FROM review_candidates")]
        for candidate in queued_matches:
            try:
                queued_bundle=json.loads(candidate["payload_json"])
                queued_source=(queued_bundle.get("sources") or [{}])[0]
                candidate["title"]=queued_source.get("title","")
                candidate["underlying_data_id"]=queued_source.get("underlying_data_id")
            except (TypeError,ValueError,IndexError): candidate["title"]=""
        normalized_identity=identity.casefold() if is_doi else _canonical_url(identity)
        match=next((s for s in sources if ((s.get("doi") or "").casefold()==normalized_identity if is_doi else _canonical_url(s.get("url"))==normalized_identity) or _norm_title(s.get("title"))==_norm_title(item["title"])),None)
        match=match or next((c for c in queued_matches if ((c.get("doi") or "").casefold()==normalized_identity if is_doi else _canonical_url(c.get("url"))==normalized_identity) or _norm_title(c.get("title"))==_norm_title(item["title"])),None)
        if match:
            basis="doi" if is_doi and (match.get("doi") or "").casefold()==normalized_identity else "url" if not is_doi and _canonical_url(match.get("url"))==normalized_identity else "normalized_title"
            db.execute("INSERT OR IGNORE INTO dedup_suppressions(id,source_id,matched_id,match_basis,title,url,doi,created_at) VALUES(?,?,?,?,?,?,?,?)",
                       (stable_id("dedup",item["source_id"],match.get("id"),basis),item["source_id"],match.get("id"),basis,item["title"],None if is_doi else identity,identity if is_doi else None,now_iso()))
            continue
        # A shared underlying-data marker across distinct DOI is retained as
        # a lineage-review warning, never counted independently by assumption.
        underlying=item["bundle"]["sources"][0].get("underlying_data_id")
        lineage=None
        if underlying:
            existing=db.execute("SELECT id FROM sources WHERE underlying_data_id=? LIMIT 1",(underlying,)).fetchone()
            if existing: lineage=f"REVIEW_SHARED_UNDERLYING_DATA:{existing['id']}"
            else:
                queued_match=next((c for c in queued_matches if c.get("underlying_data_id")==underlying),None)
                if queued_match:
                    lineage=f"REVIEW_SHARED_UNDERLYING_DATA:{queued_match['id']}"
                    db.execute("UPDATE review_candidates SET lineage_review=? WHERE id=?",(f"REVIEW_SHARED_UNDERLYING_DATA:{item['id']}",queued_match["id"]))
        from .database import enqueue_bundle
        queued.append(enqueue_bundle(db,item["bundle"],source_id=item["source_id"],retrieved_at=item["retrieved_at"],
                                     url=None if is_doi else _canonical_url(identity),doi=identity if is_doi else None,
                                     synthetic=item["synthetic"],lineage_review=lineage))
    db.commit()
    return queued
