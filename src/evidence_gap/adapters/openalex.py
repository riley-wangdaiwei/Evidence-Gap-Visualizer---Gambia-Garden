from ..schemas import RawCandidate
from ..provenance import stable_id
def parse_openalex(item):
    title=item.get("title") or "Untitled"; doi=item.get("doi")
    return RawCandidate(id=stable_id("candidate",doi or item.get("id") or title),title=title,doi=doi,url=item.get("id"),source_type="paper",metadata={"publication_year":item.get("publication_year")})
