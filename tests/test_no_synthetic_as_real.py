from evidence_gap.schemas import Source
def test_synthetic_flag_is_explicit(): assert Source(id="s",title="synthetic",synthetic=True).synthetic is True
