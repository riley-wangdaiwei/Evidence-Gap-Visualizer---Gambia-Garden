import re
def deduplicate(candidates):
    seen=set(); result=[]
    for c in candidates:
        key=(c.doi or c.url or re.sub(r"\W+","",c.title.lower())).lower()
        if key not in seen: seen.add(key); result.append(c)
    return result
