from ..schemas import RawCandidate
from ..provenance import stable_id
def parse_crossref(item):
    title=(item.get("title") or ["Untitled"])[0]; doi=item.get("DOI")
    return RawCandidate(id=stable_id("candidate",doi or title),title=title,doi=doi,url=item.get("URL"),source_type="paper",metadata={"publisher":item.get("publisher")})
