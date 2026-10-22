from datetime import datetime, timezone
from hashlib import sha256
import json

def stable_id(kind, *parts):
    payload="|".join(str(p).strip().lower() for p in parts)
    return f"{kind}_{sha256(payload.encode()).hexdigest()[:16]}"
def snapshot(records): return sha256(json.dumps(records,sort_keys=True,default=str).encode()).hexdigest()
def now_iso(): return datetime.now(timezone.utc).isoformat()
