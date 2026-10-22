import csv
import io
import json
from datetime import date
import streamlit as st
import yaml
from pathlib import Path
from evidence_gap.database import connect,enqueue_bundle,approve_bundle
from evidence_gap.candidate_import import read_candidate_csv,enqueue_candidates,_norm_title
from evidence_gap.provenance import stable_id

def render():
    st.markdown("# Source registry")
    db=connect()
    project=yaml.safe_load(Path("config/project.yaml").read_text(encoding="utf-8"))
    project_id=project.get("project_id")
    st.markdown("#### IMPORT SOURCE-LINKED CSV BUNDLE")
    st.caption("Upload CSV rows with source_id, source_title, source_url_or_doi, retrieved_at, bundle_json, and optional synthetic. Imported records remain candidates until a reviewer approves the linked bundle.")
    template=io.StringIO(); writer=csv.writer(template); writer.writerow(["source_id","source_title","source_url_or_doi","retrieved_at","bundle_json","synthetic"])
    st.download_button("Download CSV header",template.getvalue(),file_name="evidence-bundle-template.csv",mime="text/csv")
    uploaded=st.file_uploader("CSV bundle",type=["csv"])
    if uploaded and st.button("Validate and queue CSV candidates"):
        try:
            rows=read_candidate_csv(io.StringIO(uploaded.getvalue().decode("utf-8-sig")))
            ids=enqueue_candidates(db,rows)
            st.success(f"Queued {len(ids)} candidate bundle(s); all require human review.")
        except Exception as exc: st.error(f"CSV rejected: {exc}")
    with st.form("manual_source_candidate"):
        st.markdown("#### ADD MANUAL SOURCE CANDIDATE")
        title=st.text_input("TITLE"); url=st.text_input("SOURCE URL OR DOI"); producer=st.text_input("PRODUCER / REPORTING AGENCY"); retrieved=st.date_input("RETRIEVED DATE",value=date.today())
        submitted=st.form_submit_button("Save as candidate")
    if submitted and title.strip() and url.strip():
        is_doi=url.strip().lower().startswith("10.")
        sid=stable_id("source",url.strip().lower())
        source={"id":sid,"title":title.strip(),"source_type":"report","doi":url.strip() if is_doi else None,"url":None if is_doi else url.strip(),"producer":producer.strip() or None,"access_status":"unknown","retrieved_at":retrieved.isoformat(),"synthetic":False}
        existing=[dict(r) for r in db.execute("SELECT id,title,url,doi FROM sources")]
        pending_sources=[json.loads(r[0]).get("sources",[{}])[0] for r in db.execute("SELECT payload_json FROM review_candidates")]
        records=existing+pending_sources
        matched=next((r for r in records if ((r.get("doi") or "").casefold()==(source.get("doi") or "!").casefold() if is_doi else (r.get("url") or "").rstrip("/").casefold()==(source.get("url") or "!").rstrip("/").casefold()) or _norm_title(r.get("title"))==_norm_title(title.strip())),None)
        if matched:
            from evidence_gap.provenance import now_iso
            basis="doi" if is_doi and (matched.get("doi") or "").casefold()==(source.get("doi") or "!").casefold() else "url" if not is_doi and (matched.get("url") or "").rstrip("/").casefold()==(source.get("url") or "!").rstrip("/").casefold() else "normalized_title"
            db.execute("INSERT OR IGNORE INTO dedup_suppressions(id,source_id,matched_id,match_basis,title,url,doi,created_at) VALUES(?,?,?,?,?,?,?,?)",(stable_id("dedup",sid,matched.get("id"),basis),sid,matched.get("id"),basis,title.strip(),source["url"],source["doi"],now_iso()))
            db.commit(); st.warning("A matching DOI, URL, or title was found; the duplicate was suppressed and recorded for provenance.")
        else:
            enqueue_bundle(db,{"id":f"manual_{sid}","sources":[source]},source_id=sid,retrieved_at=retrieved.isoformat(),url=source["url"],doi=source["doi"])
            db.commit(); st.success("Saved to the human-review queue. It is not yet a formal source.")
    pending=[dict(r) for r in db.execute("SELECT id,entity_type,source_id,url,doi,retrieved_at,review_status,synthetic,lineage_review,payload_json FROM review_candidates WHERE review_status='PENDING_HUMAN_REVIEW' ORDER BY rowid DESC")]
    st.markdown("#### CANDIDATES — PENDING HUMAN REVIEW")
    st.dataframe([{k:v for k,v in r.items() if k!="payload_json"} for r in pending],width="stretch",hide_index=True)
    if pending:
        selected=st.selectbox("Candidate to inspect",[r["id"] for r in pending])
        candidate=next(r for r in pending if r["id"]==selected)
        st.json(json.loads(candidate["payload_json"]))
        if candidate.get("lineage_review"): st.warning(f"Lineage review required: {candidate['lineage_review']}")
        if st.button("Approve selected bundle as HUMAN_REVIEWED"):
            try:
                approve_bundle(db,selected)
                st.success("Bundle promoted atomically to canonical tables after human review.")
                st.rerun()
            except Exception as exc: st.error(f"Approval failed; no partial promotion: {exc}")
    st.markdown("#### METADATA SEARCH REVIEW")
    runs=[dict(r) for r in db.execute("SELECT id,provider,query,started_at,status,result_count,target_id,population,geography,review_status FROM search_runs WHERE project_id=? ORDER BY started_at DESC",(project_id,))]
    st.dataframe(runs,width="stretch",hide_index=True)
    pending_runs=[r for r in runs if r["review_status"]=="PENDING_HUMAN_REVIEW"]
    if pending_runs:
        run_id=st.selectbox("Search run to verify",[r["id"] for r in pending_runs])
        if st.button("Mark search scope reviewed"):
            db.execute("UPDATE search_runs SET review_status='HUMAN_REVIEWED' WHERE id=?",(run_id,)); db.commit(); st.rerun()
    search_candidates=[dict(r) for r in db.execute("SELECT c.id,c.search_run_id,c.title,c.url,c.doi,c.source_type,c.metadata_json,c.review_status,r.started_at FROM search_candidates c JOIN search_runs r ON r.id=c.search_run_id WHERE c.review_status='PENDING_HUMAN_REVIEW' AND r.project_id=? ORDER BY r.started_at DESC",(project_id,))]
    if search_candidates:
        st.dataframe([{k:v for k,v in r.items() if k!="metadata_json"} for r in search_candidates],width="stretch",hide_index=True)
        chosen=st.selectbox("Metadata candidate to promote",[r["id"] for r in search_candidates])
        item=next(r for r in search_candidates if r["id"]==chosen)
        st.json(json.loads(item["metadata_json"] or "{}"))
        if st.button("Promote metadata candidate after review"):
            from evidence_gap.database import insert_model
            from evidence_gap.schemas import Source
            retrieved=(item.get("started_at") or date.today().isoformat())[:10]
            existing=[dict(r) for r in db.execute("SELECT id,title,url,doi FROM sources")]
            matched=next((r for r in existing if ((item.get("doi") or "").casefold()==(r.get("doi") or "!").casefold() if item.get("doi") else (item.get("url") or "").rstrip("/").casefold()==(r.get("url") or "!").rstrip("/").casefold()) or _norm_title(r.get("title"))==_norm_title(item.get("title"))),None)
            if matched:
                from evidence_gap.provenance import now_iso
                basis="doi" if item.get("doi") and (item["doi"].casefold()==(matched.get("doi") or "").casefold()) else "url" if item.get("url") else "normalized_title"
                db.execute("INSERT OR IGNORE INTO dedup_suppressions(id,source_id,matched_id,match_basis,title,url,doi,created_at) VALUES(?,?,?,?,?,?,?,?)",(stable_id("dedup",item["id"],matched["id"],basis),item["id"],matched["id"],basis,item.get("title"),item.get("url"),item.get("doi"),now_iso()))
                db.execute("UPDATE search_candidates SET review_status='DUPLICATE_SUPPRESSED' WHERE id=?",(chosen,)); db.commit(); st.warning("Duplicate suppressed and recorded."); st.rerun()
            src=Source(id=item["id"],title=item["title"],source_type=item.get("source_type") or "report",url=item.get("url"),doi=item.get("doi"),synthetic=False)
            record=src.model_dump(mode="json"); record.update({"review_status":"HUMAN_REVIEWED","retrieved_at":retrieved})
            insert_model(db,"sources",record)
            db.execute("UPDATE search_candidates SET review_status='HUMAN_REVIEWED' WHERE id=?",(chosen,)); db.commit(); st.rerun()
    macro=[dict(r) for r in db.execute("SELECT id,source_id,producer,collected_by,collection_method,frequency,aggregation_level,unit,definition,review_status FROM macro_series WHERE review_status IN ('HUMAN_REVIEWED','SOURCE_VERIFIED')")]
    st.markdown("#### APPROVED MACRO SERIES")
    st.dataframe(macro,width="stretch",hide_index=True)
    formal=[dict(r) for r in db.execute("SELECT id,title,doi,url,producer,access_status,retrieved_at,review_status,synthetic,underlying_data_id FROM sources WHERE COALESCE(synthetic,0)=0 ORDER BY title")]
    st.markdown("#### FORMAL SOURCES")
    st.dataframe(formal,width="stretch",hide_index=True)
    st.caption("Stable record ID, DOI/URL, retrieval date, synthetic flag, review status, search provenance and lineage review remain visible. Exact DOI/URL/title duplicates are suppressed; shared underlying-data lineage requires review and is not treated as an independent source.")
    st.markdown("#### DUPLICATE SUPPRESSIONS")
    st.dataframe([dict(r) for r in db.execute("SELECT source_id,matched_id,match_basis,title,url,doi,created_at FROM dedup_suppressions ORDER BY created_at DESC")],width="stretch",hide_index=True)
