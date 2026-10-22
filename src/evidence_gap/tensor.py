from dataclasses import dataclass
@dataclass
class EvidenceTensor:
    records:list
    def project_gap(self):
        return [{"target":r.get("target_name") or r.get("target","unknown"),"population":r.get("population","unknown"),"state":r.get("gap_state","NOT_SEARCHED_OR_UNKNOWN"),"source_id":r.get("source_id"),"synthetic":r.get("synthetic",False)} for r in self.records]
    def project_proxy(self):
        return [{"target":r.get("target_name") or r.get("target","unknown"),"observed":r.get("observed_name") or r.get("observed","unknown"),"relation_class":r.get("relation_class","UNKNOWN_REQUIRES_REVIEW"),"review_status":r.get("review_status"),"source_id":r.get("source_id"),"synthetic":r.get("synthetic",False)} for r in self.records]
def from_database(db):
    rows=db.execute("SELECT a.*,s.synthetic,s.title AS source_title, oi.name AS observed_name, ti.name AS target_name FROM alignments a LEFT JOIN sources s ON s.id=a.source_id LEFT JOIN indicators oi ON oi.id=a.observed_indicator_id LEFT JOIN indicators ti ON ti.id=a.target_indicator_id").fetchall()
    return EvidenceTensor([dict(r) for r in rows])
