import streamlit as st
def render(record):
    st.markdown("#### RECORD DETAIL")
    for k,v in record.items(): st.markdown(f"**{k.replace('_',' ').upper()}**  \n{v if v is not None else 'UNKNOWN'}")
