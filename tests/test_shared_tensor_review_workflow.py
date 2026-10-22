import csv
import io
import json
import yaml

from evidence_gap.database import connect,approve_bundle
from evidence_gap.candidate_import import read_candidate_csv,enqueue_candidates
from evidence_gap.tensor import from_database
from app.components.dark_atlas import add_friction_markers
import plotly.graph_objects as go

def _taxonomy(path):
    path.write_text(yaml.safe_dump({
        "population_groups":["population-under-test"],
        "geographies":[{"name":"national","level":"country","aliases":["Test Republic"]},{"name":"test-region","level":"region"}],
        "geographic_levels":["country","region"],
        "targets":[{"id":"target-under-test","name":"Configured topic"}],
    }),encoding="utf-8")
    return path

def _approved_records(db):
    db.execute("INSERT INTO sources(id,title,access_status,synthetic,review_status,publication_year,underlying_data_id) VALUES('source-a','Test source','open',0,'HUMAN_REVIEWED',2022,'dataset-a')")
    db.execute("INSERT INTO data_products(id,source_id,name,product_type,geography_level,population,synthetic,review_status) VALUES('product-a','source-a','Test product','dataset','country','population-under-test',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO indicators(id,data_product_id,name,definition,unit,denominator,synthetic,review_status) VALUES('target-under-test',NULL,'Configured topic','Target definition',NULL,NULL,0,'HUMAN_REVIEWED')")
    db.execute("UPDATE indicators SET is_target=1 WHERE id='target-under-test'")
    db.execute("INSERT INTO indicators(id,data_product_id,name,definition,unit,synthetic,review_status) VALUES('observed-a','product-a','Observed field','Observed definition','count',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO variables(id,indicator_id,original_name,definition,unit,age_band,synthetic,review_status) VALUES('variable-a','observed-a','raw_measure','Original definition','count','original age band',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO observations(id,variable_id,value,unit,geography,geography_level,period,synthetic,review_status,population,observation_year,publication_year,source_id,original_variable_name,original_age_band,original_definition,denominator) VALUES('observation-a','variable-a','3','count','Test Republic','country','2019',0,'HUMAN_REVIEWED','population-under-test',2019,2022,'source-a','raw_measure','original age band','Original definition','respondents')")
    db.execute("INSERT INTO alignments(id,target_indicator_id,observed_indicator_id,relation_class,rationale,review_status,source_id) VALUES('alignment-a','target-under-test','observed-a','DIRECT_MATCH','Recorded comparison','HUMAN_REVIEWED','source-a')")
    db.commit()

def test_views_project_same_approved_batch_and_country_does_not_fill_region(tmp_path):
    db=connect(":memory:"); _approved_records(db); tensor=from_database(db,_taxonomy(tmp_path/"taxonomy.yaml"))
    national=next(r for r in tensor.project_gap() if r["geography"]=="national")
    region=next(r for r in tensor.project_gap() if r["geography"]=="test-region")
    proxy=tensor.project_proxy()[0]
    assert national["gap_state"]=="DIRECT_EVIDENCE_FOUND"
    assert national["source_ids"]==[proxy["source_id"]]
    assert national["observation_period"]=="2019" and national["publication_year"]==2022
    assert national["age_band"]=="original age band"
    assert region["direct_evidence_count"]==0
    assert region["source_ids"]==[]
    assert "INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION" in region["flags"]

def test_repeat_citation_is_one_independent_source_and_distinct_data_is_multiple(tmp_path):
    db=connect(":memory:"); _approved_records(db)
    db.execute("INSERT INTO sources(id,title,access_status,synthetic,review_status,underlying_data_id) VALUES('source-b','Second citation','open',0,'HUMAN_REVIEWED','dataset-a')")
    db.execute("INSERT INTO data_products(id,source_id,name,product_type,geography_level,population,synthetic,review_status) VALUES('product-b','source-b','Second product','dataset','country','population-under-test',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO indicators(id,data_product_id,name,definition,unit,synthetic,review_status) VALUES('observed-b','product-b','Second observation','Definition','count',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO variables(id,indicator_id,original_name,definition,unit,synthetic,review_status) VALUES('variable-b','observed-b','second_raw_field','Definition','count',0,'HUMAN_REVIEWED')")
    db.execute("INSERT INTO observations(id,variable_id,value,unit,geography,geography_level,period,synthetic,review_status,population) VALUES('observation-b','variable-b','5','count','Test Republic','country','2019',0,'HUMAN_REVIEWED','population-under-test')")
    db.execute("INSERT INTO alignments(id,target_indicator_id,observed_indicator_id,relation_class,rationale,review_status,source_id) VALUES('alignment-b','target-under-test','observed-b','DIRECT_MATCH','Reviewed comparison','HUMAN_REVIEWED','source-b')")
    db.commit(); taxonomy=_taxonomy(tmp_path/"taxonomy.yaml")
    same_data=next(r for r in from_database(db,taxonomy).project_gap() if r["geography"]=="national")
    assert same_data["direct_evidence_count"]==2 and same_data["independent_source_count"]==1
    assert same_data["gap_state"]=="DIRECT_EVIDENCE_FOUND"
    db.execute("UPDATE sources SET underlying_data_id='dataset-b' WHERE id='source-b'");db.commit()
    independent=next(r for r in from_database(db,taxonomy).project_gap() if r["geography"]=="national")
    assert independent["independent_source_count"]==2
    assert independent["gap_state"]=="MULTIPLE_INDEPENDENT_DIRECT_SOURCES"

def test_configured_topics_are_not_page_hardcoded_and_empty_cells_remain_unknown(tmp_path):
    tensor=from_database(connect(":memory:"),_taxonomy(tmp_path/"topics.yaml"))
    assert [r["target_name"] for r in tensor.project_gap()]==["Configured topic","Configured topic"]
    assert {r["gap_state"] for r in tensor.project_gap()}=={"NOT_SEARCHED_OR_UNKNOWN"}

def test_observed_variables_without_reviewed_alignment_get_unknown_view_b_slots(tmp_path):
    db=connect(":memory:"); _approved_records(db)
    db.execute("DELETE FROM alignments"); db.commit()
    relation=from_database(db,_taxonomy(tmp_path/"taxonomy.yaml")).project_proxy()[0]
    assert relation["observed_name"]=="raw_measure"
    assert relation["relation_class"]=="UNKNOWN_REQUIRES_REVIEW"
    assert relation["review_status"] is None

def test_candidate_csv_is_pending_until_atomic_human_approval(tmp_path):
    bundle={
        "sources":[{"id":"source-c","title":"Source C","access_status":"open","underlying_data_id":"batch-c"}],
        "data_products":[{"id":"product-c","source_id":"source-c","name":"Product C","product_type":"dataset","geography_level":"country","population":"population-under-test"}],
        "indicators":[{"id":"target-under-test","data_product_id":None,"name":"Configured topic","definition":"Target definition","is_target":True},{"id":"indicator-c","data_product_id":"product-c","name":"Observed measure","definition":"Observed indicator","unit":"count"}],
        "variables":[{"id":"variable-c","indicator_id":"indicator-c","original_name":"raw_field","definition":"Original variable definition","unit":"count","age_band":"original age band"}],
        "observations":[{"id":"observation-c","variable_id":"variable-c","value":"4","unit":"count","geography":"Test Republic","geography_level":"country","period":"2019","population":"population-under-test","observation_year":2019,"publication_year":2022,"original_variable_name":"raw_field","original_age_band":"original age band","original_definition":"Original variable definition","denominator":"respondents"}],
        "alignments":[{"id":"alignment-c","target_indicator_id":"target-under-test","observed_indicator_id":"indicator-c","relation_class":"DIRECT_MATCH","rationale":"Reviewed test relation","review_status":"PENDING_HUMAN_REVIEW"}],
        "gap_claims":[{"id":"gap-c","source_id":"source-c","claim":"Documented missing subgroup","quote":"quoted passage","target_id":"target-under-test","population":"population-under-test","geography":"test-region"}],
        "barriers":[{"id":"barrier-c","barrier_type":"MISSING_DISAGGREGATION","description":"No regional breakdown","source_id":"source-c","target_id":"target-under-test","verification_status":"HUMAN_REVIEWED"}],
    }
    csv_text=io.StringIO(); writer=csv.DictWriter(csv_text,fieldnames=["source_id","source_title","source_url_or_doi","retrieved_at","bundle_json","synthetic"])
    writer.writeheader(); writer.writerow({"source_id":"source-c","source_title":"Source C","source_url_or_doi":"https://example.test/source-c","retrieved_at":"2026-10-22","bundle_json":json.dumps(bundle),"synthetic":"false"})
    candidates=read_candidate_csv(io.StringIO(csv_text.getvalue()))
    db=connect(":memory:"); assert enqueue_candidates(db,candidates)==["candidate_source-c"]
    assert db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]==0
    taxonomy=_taxonomy(tmp_path/"topics.yaml")
    before=from_database(db,taxonomy)
    assert before.project_proxy()==[]
    approved=approve_bundle(db,"candidate_source-c")
    assert approved["sources"][0]["review_status"]=="HUMAN_REVIEWED"
    source=db.execute("SELECT url,retrieved_at,review_status,synthetic FROM sources WHERE id='source-c'").fetchone()
    assert tuple(source)==("https://example.test/source-c","2026-10-22","HUMAN_REVIEWED",0)
    after=from_database(db,taxonomy)
    assert after.project_proxy()[0]["relation_class"]=="DIRECT_MATCH"
    assert next(r for r in after.project_gap() if r["geography"]=="national")["direct_evidence_count"]==1

def test_friction_markers_are_real_selectable_plotly_points():
    fig=go.Figure(); add_friction_markers(fig,[{"x":0,"y":0,"id":"barrier-test","type":"ACCESS_RESTRICTED","description":"Documented access restriction"}])
    assert len(fig.data)==1
    assert fig.data[0].customdata[0][0]=="barrier-test"
    assert fig.data[0].customdata[0][1]=="ACCESS_RESTRICTED"

def test_synthetic_records_never_enter_either_projection(tmp_path):
    db=connect(":memory:"); _approved_records(db)
    for table in ("sources","data_products","indicators","variables","observations","alignments"):
        db.execute(f"UPDATE {table} SET synthetic=1")
    db.commit(); tensor=from_database(db,_taxonomy(tmp_path/"taxonomy.yaml"))
    assert all(row["direct_evidence_count"]==0 for row in tensor.project_gap())
    assert tensor.project_proxy()==[]

def test_scoped_completed_search_changes_only_its_unknown_cell(tmp_path):
    db=connect(":memory:")
    db.execute("INSERT INTO search_runs(id,provider,query,started_at,status,result_count,target_id,population,geography,review_status) VALUES('run-a','crossref','explicit query','2026-10-22','complete',0,'target-under-test','population-under-test','national','HUMAN_REVIEWED')")
    tensor=from_database(db,_taxonomy(tmp_path/"taxonomy.yaml"))
    states={(r["geography"],r["gap_state"]) for r in tensor.project_gap()}
    assert ("national","SEARCHED_NO_DIRECT_EVIDENCE_FOUND") in states
    assert ("test-region","NOT_SEARCHED_OR_UNKNOWN") in states

def test_claim_audit_keeps_requirements_linked_to_claim_and_variable():
    db=connect(":memory:")
    db.execute("INSERT INTO research_claims(id,title,claim,identification_limits,review_status) VALUES('claim-a','Reviewable claim','A bounded research claim','Unmeasured confounding remains','HUMAN_REVIEWED')")
    db.execute("INSERT INTO indicators(id,name,definition,review_status) VALUES('indicator-a','Observed indicator','Definition','HUMAN_REVIEWED')")
    db.execute("INSERT INTO variables(id,indicator_id,original_name,definition,review_status) VALUES('variable-a','indicator-a','raw_field','Original definition','HUMAN_REVIEWED')")
    db.execute("INSERT INTO claim_requirements(id,claim_id,required_variable,variable_id,analysis_limited,review_status) VALUES('req-a','claim-a','Required field','variable-a','Prevents subgroup estimate','HUMAN_REVIEWED')")
    row=db.execute("SELECT c.identification_limits,r.required_variable,r.analysis_limited,v.original_name FROM research_claims c JOIN claim_requirements r ON r.claim_id=c.id JOIN variables v ON v.id=r.variable_id").fetchone()
    assert tuple(row)==("Unmeasured confounding remains","Required field","Prevents subgroup estimate","raw_field")

def test_exact_duplicates_suppress_but_shared_data_across_dois_gets_lineage_review():
    rows=[]
    for source_id,title,doi in (("s-a","Study A","10.1000/a"),("s-b","Study B","10.1000/b"),("s-c","Study C","10.1000/a")):
        bundle={"sources":[{"id":source_id,"title":title,"underlying_data_id":"same-dataset"}]}
        rows.append({"source_id":source_id,"source_title":title,"source_url_or_doi":doi,"retrieved_at":"2026-10-22","bundle_json":json.dumps(bundle)})
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=["source_id","source_title","source_url_or_doi","retrieved_at","bundle_json"]);writer.writeheader();writer.writerows(rows)
    candidates=read_candidate_csv(io.StringIO(stream.getvalue())); db=connect(":memory:")
    queued=enqueue_candidates(db,candidates)
    assert queued==["candidate_s-a","candidate_s-b"]
    flags=[r[0] for r in db.execute("SELECT lineage_review FROM review_candidates ORDER BY id")]
    assert all(flag.startswith("REVIEW_SHARED_UNDERLYING_DATA:") for flag in flags)

def test_macro_series_candidate_requires_auditable_method_and_aggregation():
    bundle={"sources":[{"id":"macro-source","title":"Metadata only"}],"macro_series":[{"id":"series-1","source_id":"macro-source","producer":"Agency","collected_by":"Agency","collection_method":"Published administrative series","frequency":"annual","aggregation_level":"country","unit":"index points","definition":"Source definition"}]}
    row={"source_id":"macro-source","source_title":"Metadata only","source_url_or_doi":"https://example.test/macro","retrieved_at":"2026-10-22","bundle_json":json.dumps(bundle)}
    data=io.StringIO();writer=csv.DictWriter(data,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    candidate=read_candidate_csv(io.StringIO(data.getvalue()))[0]
    assert candidate["bundle"]["macro_series"][0]["review_status"]=="PENDING_HUMAN_REVIEW"
    bundle["macro_series"][0]["collection_method"]=""
    row["bundle_json"]=json.dumps(bundle);data=io.StringIO();writer=csv.DictWriter(data,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    import pytest
    with pytest.raises(ValueError,match="collection_method"):
        read_candidate_csv(io.StringIO(data.getvalue()))
