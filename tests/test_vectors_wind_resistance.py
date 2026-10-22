import pytest
from evidence_gap.research_bridges import arrow_definition
from evidence_gap.wind_field import availability
from evidence_gap.resistance import validate_barrier
def test_arrow_directions():
    assert "→ target gap" in arrow_definition("gap")
    assert "→ target indicator" in arrow_definition("proxy")
def test_wind_disabled_without_evidence(): assert availability([],{})[0] is False
def test_barriers_are_typed():
    assert validate_barrier("ACCESS_RESTRICTED")=="ACCESS_RESTRICTED"
    with pytest.raises(ValueError): validate_barrier("ALARM")
