"""Catalog metadata only; no person-level responses are stored."""
def describe_variable(original_name, definition, age_band=None, unit=None):
    return {"original_name":original_name,"definition":definition,"age_band":age_band,"unit":unit,"person_level_data_stored":False}
