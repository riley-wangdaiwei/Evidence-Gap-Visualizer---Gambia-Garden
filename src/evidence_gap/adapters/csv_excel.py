import pandas as pd
from .base import Adapter
from ..schemas import RawCandidate
from ..provenance import stable_id
class TabularAdapter(Adapter):
    def read(self,path):
        frame=pd.read_excel(path) if str(path).lower().endswith((".xlsx",".xls")) else pd.read_csv(path)
        out=[]
        for i,row in frame.iterrows():
            d={k:(None if pd.isna(v) else v) for k,v in row.items()}; title=str(d.get("title") or d.get("source_title") or "").strip()
            if title: out.append(RawCandidate(id=stable_id("candidate",title,d.get("doi") or d.get("url") or i),title=title,url=d.get("url"),doi=d.get("doi"),source_type=d.get("source_type") or "report",metadata=d))
        return out
