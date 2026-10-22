def availability(edges, coordinates):
    if not edges: return False,"No documented directional relationships"
    if not coordinates or any(e.get("source") not in coordinates or e.get("target") not in coordinates for e in edges): return False,"Valid coordinates for all relationship endpoints are unavailable"
    return False,"Wind field is not enabled; discrete directed links remain available"
