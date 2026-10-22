from .schemas import RelationClass
def classify(metadata):
    keys=("definition","population","geography","time_period","unit","denominator","method","aggregation_level")
    if any(metadata.get(k) is None for k in keys): return RelationClass.UNKNOWN_REQUIRES_REVIEW
    if all(metadata[k][0]==metadata[k][1] for k in keys): return RelationClass.DIRECT_MATCH
    if metadata.get("harmonization_rule"): return RelationClass.HARMONIZABLE
    if metadata.get("conceptually_related"): return RelationClass.PROXY
    return RelationClass.INCOMPATIBLE
