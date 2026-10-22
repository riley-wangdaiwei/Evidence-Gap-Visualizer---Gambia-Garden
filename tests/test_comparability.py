from evidence_gap.comparability import classify
def test_unknown_metadata_stays_unknown(): assert classify({}).value=="UNKNOWN_REQUIRES_REVIEW"
