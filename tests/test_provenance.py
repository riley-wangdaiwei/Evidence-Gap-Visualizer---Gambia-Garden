from evidence_gap.provenance import stable_id
def test_stable_id(): assert stable_id("source","doi") == stable_id("source","doi")
