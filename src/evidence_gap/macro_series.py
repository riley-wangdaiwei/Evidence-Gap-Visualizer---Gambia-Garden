REQUIRED_METADATA=("producer","collected_by","collection_method","frequency","aggregation_level","unit","definition")
def validate_series_metadata(record):
    missing=[k for k in REQUIRED_METADATA if not record.get(k)]
    return {"missing":missing,"complete":not missing}
