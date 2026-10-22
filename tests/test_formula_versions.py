import pytest
from evidence_gap.formulas import FormulaConfig,weighted_score
from evidence_gap.formulas import record_formula_run
from evidence_gap.database import connect
import json
def test_weights_and_unknowns():
    cfg=FormulaConfig("m","1",{"a":50,"b":50})
    assert weighted_score(cfg,{"a":1,"b":0})==.5
    assert weighted_score(cfg,{"a":1,"b":None}) is None
    with pytest.raises(ValueError): weighted_score(FormulaConfig("m","1",{"a":20}),{"a":1})

def test_formula_run_persists_nullable_components_and_snapshot():
    db=connect(":memory:"); cfg=FormulaConfig("formula-test","v2",{"known":50,"unknown":50})
    run=record_formula_run(cfg,{"known":.8,"unknown":None},[{"id":"approved-source"}])
    db.execute("INSERT INTO formula_runs(id,formula_id,version,weights,components,data_snapshot,created_at) VALUES(?,?,?,?,?,?,?)",(run["id"],run["formula_id"],run["version"],json.dumps(run["weights"]),json.dumps(run["components"]),json.dumps(run["data_snapshot"]),run["created_at"]))
    saved=db.execute("SELECT formula_id,version,weights,components,data_snapshot,created_at FROM formula_runs").fetchone()
    assert saved["formula_id"]=="formula-test" and saved["version"]=="v2"
    assert json.loads(saved["components"])=={"known":.8,"unknown":None}
    assert saved["data_snapshot"] and saved["created_at"]
