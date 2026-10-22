import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import streamlit as st
from evidence_gap.database import connect
from evidence_gap.batch_loader import load_configured_batch
st.set_page_config(page_title="Gambia Evidence Gap Explorer",layout="wide")
st.markdown("""<style>
.stApp{background:#050505;color:#fff}
.block-container{padding-top:2rem;max-width:none;text-align:left}
h1,h2,h3{font-family:Georgia,serif;letter-spacing:-.03em;color:#fff}
p,li{font-family:Georgia,serif;color:#ddd;line-height:1.55}
.stCaption,.stCode{font-family:'Courier New',monospace;font-size:10px;color:#c8c8c8;letter-spacing:.04em}
button,input,textarea,select,label{font-family:Arial,Helvetica,sans-serif}
section[data-testid="stSidebar"]{background:#050505;border-right:1px solid #777}
.stButton>button{border-radius:0;background:transparent;color:#fff;border:none;border-bottom:1px solid #777;padding-left:0;padding-right:0}
.stButton>button:hover{background:#050505;color:#fff;border-bottom-color:#fff}
input,textarea{background:#111!important;color:#fff!important;border:0!important;border-bottom:1px solid #777!important;border-radius:0!important}
input:focus,textarea:focus{border-bottom:2px solid #fff!important;box-shadow:none!important}
[data-baseweb="select"]>div{background:#111!important;color:#fff!important;border:0!important;border-bottom:1px solid #777!important;border-radius:0!important}
[data-testid="stAlert"]{background:#080808!important;border:0!important;border-left:1px solid #888!important;border-radius:0!important;color:#fff!important}
[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"]{border-radius:0!important;box-shadow:none!important}
div[data-testid="stDataFrame"]{border-radius:0!important}
div[data-testid="stRadio"] label{color:#777}
div[data-testid="stRadio"] label:has(input:checked){color:#fff;font-weight:700}
div[data-testid="stRadio"] label>div:first-child{display:none}
</style>""",unsafe_allow_html=True)
batch=load_configured_batch(connect())
from pages import evidence_gap_map,proxy_alignment_map,source_registry,formula_settings,research_tasks
PAGES={"Overview":None,"Evidence gap map":evidence_gap_map,"Proxy alignment map":proxy_alignment_map,"Source registry":source_registry,"Formula settings":formula_settings,"Research tasks":research_tasks}
with st.sidebar:
    st.markdown("## GAMBIA / EVIDENCE ATLAS")
    page=st.radio("NAVIGATION",list(PAGES),label_visibility="collapsed")
if page in {"Source registry","Formula settings","Research tasks"}:
    st.markdown("<style>.stMainBlockContainer{max-width:900px!important;margin-left:0!important;margin-right:auto!important}</style>",unsafe_allow_html=True)
if page=="Overview":
    st.markdown("# Evidence, measured carefully.")
    st.markdown("A local instrument for examining what is measured, what is missing, and what research step may follow.")
    st.markdown("---")
    st.caption("MVP / LOCAL REGISTRY / NO LLM KEY REQUIRED")
    if batch["files"]:
        st.info(f"Configured batch: {batch['folder']} · {batch['files']} CSV file(s) · {batch['queued']} new candidate bundle(s), pending human review.")
    else:
        st.info(f"Configured batch folder is empty: {batch['folder']}. Evidence remains unknown until reviewed source records are supplied.")
    st.markdown("### Method")
    st.markdown("One canonical registry feeds both matrix views. Provenance and original measurement definitions remain attached. A national statistic stays national. Unknown is never zero.")
else: PAGES[page].render()
