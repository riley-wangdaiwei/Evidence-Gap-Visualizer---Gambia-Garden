import json
from evidence_gap.database import connect
from evidence_gap.task_builder import build_task,export_markdown

def test_search_result_schema_keeps_candidate_out_of_formal_sources():
    db=connect(":memory:")
    db.execute("INSERT INTO search_runs(id,provider,query,started_at,status,result_count,details) VALUES('run','crossref','query','2026-10-22','complete',1,'test')")
    db.execute("INSERT INTO search_candidates(id,search_run_id,title,review_status) VALUES('candidate','run','Example','PENDING_HUMAN_REVIEW')")
    assert db.execute("SELECT count(*) FROM sources").fetchone()[0]==0
    assert db.execute("SELECT review_status FROM search_candidates").fetchone()[0]=="PENDING_HUMAN_REVIEW"

def test_task_exports_markdown_and_json_payload():
    task=build_task("Study gap","Review available measures")
    assert "# Study gap" in export_markdown(task)
    assert json.loads(json.dumps(task))["status"]=="draft"
