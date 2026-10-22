from .schemas import GapState
def state_for(search_status="not_run", direct=0, indirect=0, restricted=False):
    if restricted: return GapState.RESTRICTED_ACCESS
    if search_status=="not_run": return GapState.NOT_SEARCHED_OR_UNKNOWN
    if search_status!="complete": return GapState.SEARCH_INCOMPLETE
    if direct>1: return GapState.MULTIPLE_INDEPENDENT_DIRECT_SOURCES
    if direct==1: return GapState.DIRECT_EVIDENCE_FOUND
    if indirect: return GapState.INDIRECT_OR_NOT_COMPARABLE_EVIDENCE
    return GapState.SEARCHED_NO_DIRECT_EVIDENCE_FOUND
