from evidence_gap.schemas import Source,Observation
def test_schema_preserves_scope_and_synthetic_flag():
    s=Source(id="s",title="Example",synthetic=True)
    o=Observation(id="o",variable_id="v",value=2,geography="The Gambia",geography_level="country")
    assert s.synthetic and o.geography_level=="country"
