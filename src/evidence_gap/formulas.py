from dataclasses import dataclass
from .provenance import now_iso, snapshot, stable_id
@dataclass
class FormulaConfig:
    formula_id:str; version:str; weights:dict
    def validate(self): return bool(self.weights) and all(v>=0 for v in self.weights.values()) and abs(sum(self.weights.values())-100)<1e-8
def weighted_score(config, components):
    if not config.validate(): raise ValueError("Weights must be nonnegative and sum to 100%")
    if any(components.get(k) is None for k in config.weights): return None
    return sum(config.weights[k]*components[k] for k in config.weights)/100
def record_formula_run(config,components,records):
    created=now_iso()
    return {"id":stable_id("run",config.formula_id,config.version,created),"formula_id":config.formula_id,"version":config.version,"weights":config.weights,"components":components,"data_snapshot":snapshot(records),"created_at":created}
