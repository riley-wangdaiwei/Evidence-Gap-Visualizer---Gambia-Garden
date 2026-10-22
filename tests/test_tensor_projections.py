from evidence_gap.tensor import EvidenceTensor
def test_both_projections_use_same_records():
    tensor=EvidenceTensor([{"target":"topic-under-test","observed":"measure-under-test","source_id":"s1","gap_state":"DIRECT_EVIDENCE_FOUND","relation_class":"DIRECT_MATCH"}])
    assert tensor.project_gap()[0]["source_id"]==tensor.project_proxy()[0]["source_id"]=="s1"
