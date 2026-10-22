import streamlit as st
import json
from pathlib import Path
from evidence_gap.task_builder import build_task,export_markdown
from evidence_gap.database import connect
def render():
    st.markdown("# Research tasks")
    with st.form("task"):
        title=st.text_input("TASK TITLE"); description=st.text_area("RATIONALE / NEXT ACTION"); submitted=st.form_submit_button("Create draft task")
    if submitted and title.strip():
        task=build_task(title,description)
        db=connect(); db.execute("INSERT OR REPLACE INTO research_tasks VALUES(?,?,?,?,?,?)",(task["id"],task["title"],task["description"],task["priority"],task["status"],task["created_at"])); db.commit()
        st.download_button("Download Markdown",export_markdown(task),file_name="research-task.md")
        st.download_button("Download JSON",json.dumps(task,indent=2),file_name="research-task.json")
    rows=[dict(r) for r in connect().execute("SELECT * FROM research_tasks ORDER BY created_at DESC")]
    st.dataframe(rows,width="stretch",hide_index=True)
