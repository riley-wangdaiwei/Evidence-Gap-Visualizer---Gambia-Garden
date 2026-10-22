from evidence_gap.schemas import RawCandidate
from evidence_gap.deduplication import deduplicate
def test_duplicate_doi_not_independent():
    a=RawCandidate(id="a",title="A",doi="10/x"); b=RawCandidate(id="b",title="B",doi="10/x")
    assert len(deduplicate([a,b]))==1
