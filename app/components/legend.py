import streamlit as st

def render(view):
    if view=="gap":
        st.markdown("**Legend** · teal = direct evidence · darker teal = multiple independent direct sources · amber = indirect evidence / documented issue · rust = searched with no direct hit / temporal mismatch · charcoal hatch `///` = not searched or unknown.")
        direction="evidence or comparator → target gap"
        level="Observation levels are shown only at their recorded national, LGA/border-area, household, person, or institutional scope. National records never fill LGA cells."
    else:
        st.markdown("**Legend** · teal = lower documented mismatch · amber = proxy / related · rust = incompatible or higher documented mismatch · charcoal = unknown and requires review.")
        direction="observed indicator or variable → target indicator"
        level="Relations remain attached to source and observed variable; geographic scope is not inferred from alignment."
    st.caption(f"Vectors: {direction}; thickness = number of deduplicated independent supporting sources. Length has no evidence or importance meaning. Links are RULE_DERIVED or HUMAN_REVIEWED; no LLM links exist. Wind would mean a modeled research-connection field, but is disabled until supported relations and coordinates exist. Friction marks typed evidence/access barriers; click/select the affected cell for supporting evidence and verification state. Unknown is distinct from no direct evidence. {level}")
