from evidence_gap.schemas import Observation,Variable

def test_country_observation_stays_country_level():
    observation=Observation(id="o",variable_id="v",value=10,geography="The Gambia",geography_level="country")
    assert observation.geography_level=="country"
    assert not hasattr(observation,"region")

def test_three_savings_measurements_remain_distinct():
    account_count=Variable(id="a",indicator_id="ia",original_name="account_count",definition="Count of accounts",unit="accounts",synthetic=True)
    account_holders=Variable(id="h",indicator_id="ih",original_name="account_holders",definition="Count of holders",unit="holders",synthetic=True)
    saved_12m=Variable(id="s",indicator_id="is",original_name="saved_12m",definition="Saved within prior 12 months",unit="binary response",synthetic=True)
    assert len({account_count.original_name,account_holders.original_name,saved_12m.original_name})==3
    assert len({account_count.unit,account_holders.unit,saved_12m.unit})==3
