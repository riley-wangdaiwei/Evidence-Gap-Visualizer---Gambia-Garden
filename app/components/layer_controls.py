import streamlit as st
def controls():
    st.markdown("#### LAYERS")
    layers={"heatmap":st.checkbox("Heatmap",True),"vectors":st.checkbox("Vectors / research bridges",False,disabled=True),"wind":st.checkbox("Wind / modeled field",False,disabled=True),"friction":st.checkbox("Friction / barriers",False,disabled=True),"sources":st.checkbox("Sources and labels",True)}
    st.caption("Vectors and friction are not rendered in this matrix prototype. Wind is disabled because valid directional links and coordinates are absent.")
    return layers
