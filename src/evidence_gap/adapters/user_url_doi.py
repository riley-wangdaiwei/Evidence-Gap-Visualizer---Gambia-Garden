from ..schemas import RawCandidate
from ..provenance import stable_id
def candidate(value):
    doi=value if value.lower().startswith("10.") else None
    return RawCandidate(id=stable_id("candidate",value),title=value,url=None if doi else value,doi=doi,source_type="user_supplied")
