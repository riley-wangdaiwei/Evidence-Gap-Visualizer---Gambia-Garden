import streamlit as st

from v1_views import (
    load_inventory,
    render_readme,
    render_view_a,
    render_view_b,
    render_view_c,
)

st.set_page_config(page_title="Gambia Evidence Gap Explorer", layout="wide")
st.markdown(
    """<style>
.stApp{background:#050505;color:#fff}
.block-container{padding-top:2rem;max-width:none;text-align:left}
h1,h2,h3{font-family:Georgia,serif;letter-spacing:-.03em;color:#fff}
p,li{font-family:Georgia,serif;color:#ddd;line-height:1.55}
.stCaption,.stCode{font-family:'Courier New',monospace;font-size:10px;color:#c8c8c8;letter-spacing:.04em}
button,input,textarea,select,label{font-family:Arial,Helvetica,sans-serif}
section[data-testid="stSidebar"]{display:none}
[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"]{border-radius:0!important;box-shadow:none!important}
div[data-testid="stDataFrame"]{border-radius:0!important}
button[role="tab"]{color:#c8c8c8}
button[role="tab"][aria-selected="true"]{color:#fff;border-bottom-color:#4B918C}
</style>""",
    unsafe_allow_html=True,
)

inventory = load_inventory()
tab_readme, tab_a, tab_b, tab_c = st.tabs(["README", "View A", "View B", "View C"])
with tab_readme:
    render_readme(inventory)
with tab_a:
    render_view_a(inventory)
with tab_b:
    render_view_b(inventory)
with tab_c:
    render_view_c(inventory)
