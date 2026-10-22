from evidence_gap.tensor import EvidenceTensor
def test_both_projections_use_same_records():
    tensor=EvidenceTensor([{"target":"savings","observed":"accounts","source_id":"s1"}])
    assert tensor.project_gap()[0]["source_id"]==tensor.project_proxy()[0]["source_id"]=="s1"
