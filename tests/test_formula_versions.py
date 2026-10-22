import pytest
from evidence_gap.formulas import FormulaConfig,weighted_score
def test_weights_and_unknowns():
    cfg=FormulaConfig("m","1",{"a":50,"b":50})
    assert weighted_score(cfg,{"a":1,"b":0})==.5
    assert weighted_score(cfg,{"a":1,"b":None}) is None
    with pytest.raises(ValueError): weighted_score(FormulaConfig("m","1",{"a":20}),{"a":1})
