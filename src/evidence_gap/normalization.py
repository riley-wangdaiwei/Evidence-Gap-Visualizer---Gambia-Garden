from .schemas import Source
from .provenance import stable_id
def source_from_candidate(c):
    return Source(id=stable_id("source",c.doi or c.url or c.title),title=c.title,source_type=c.source_type,url=c.url,doi=c.doi,synthetic=c.synthetic)
