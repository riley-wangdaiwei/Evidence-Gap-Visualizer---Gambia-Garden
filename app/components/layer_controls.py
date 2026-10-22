import streamlit as st

def controls():
    st.markdown("#### LAYERS")
    layers={
        "heatmap":st.checkbox("Heatmap",True),
        "vectors":st.checkbox("Vectors / research bridges",False),
        "wind":st.checkbox("Wind / modeled field",False,disabled=True),
        "friction":st.checkbox("Friction / barriers",False),
        "sources":st.checkbox("Sources and labels",True),
    }
    st.caption("Wind is unavailable: no validated, geolocated directional network and coordinate layout are present. No field is synthesized.")
    return layers
