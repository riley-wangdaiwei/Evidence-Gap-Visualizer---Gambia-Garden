import streamlit as st
from evidence_gap.database import connect
def render():
    st.markdown("# Source registry")
    db=connect(); rows=[dict(r) for r in db.execute("SELECT * FROM sources ORDER BY title")]
    st.caption("APPROVED / FORMAL SOURCE RECORDS")
    st.dataframe(rows,width="stretch",hide_index=True)
    st.markdown("#### SEARCH CANDIDATES · PENDING HUMAN REVIEW")
    candidates=[dict(r) for r in db.execute("SELECT id,search_run_id,title,url,doi,source_type,metadata_json,review_status FROM search_candidates ORDER BY rowid DESC")]
    st.dataframe(candidates,width="stretch",hide_index=True)
    st.caption("Provenance appears as stable record ID, DOI/URL, and search-run ID. Identical DOI/URL/title candidates are collapsed before queuing; suppressed-duplicate counts and source-lineage review controls are not shown.")
    with st.form("manual_source"):
        st.markdown("#### ADD SOURCE CANDIDATE")
        title=st.text_input("TITLE"); url=st.text_input("URL OR DOI"); producer=st.text_input("PRODUCER / REPORTING AGENCY")
        submitted=st.form_submit_button("Save candidate")
    if submitted and title.strip():
        from evidence_gap.schemas import Source
        from evidence_gap.provenance import stable_id
        doi=url if url.startswith("10.") else None; link=None if doi else (url or None)
        source=Source(id=stable_id("source",doi or link or title),title=title,doi=doi,url=link,producer=producer or None)
        from evidence_gap.database import insert_model
        insert_model(db,"sources",source); db.commit(); st.success("Candidate saved; review its metadata before analysis.")
