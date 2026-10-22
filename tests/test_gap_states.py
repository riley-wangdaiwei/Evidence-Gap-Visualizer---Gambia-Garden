from evidence_gap.gap_claims import state_for
def test_not_searched_distinct_from_searched_no_hit():
    assert state_for().value=="NOT_SEARCHED_OR_UNKNOWN"
    assert state_for("complete").value=="SEARCHED_NO_DIRECT_EVIDENCE_FOUND"
