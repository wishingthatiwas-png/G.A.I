from __future__ import annotations
import json
from pathlib import Path

SEED = Path("/mnt/gai/memory/semantic_seed.json")

class SemanticNetwork:
    """Weak prior knowledge. Experience is allowed to strengthen or contradict it."""
    def __init__(self, path=SEED):
        self.path = Path(path)
        self.nodes = {}
        self.edges = []
        self.load()

    def load(self):
        if self.path.exists():
            obj=json.loads(self.path.read_text())
            self.nodes=obj.get("nodes",{})
            self.edges=obj.get("edges",[])
        else:
            self.nodes={}
            self.edges=[]

    def related(self, concept, limit=12):
        hits=[]
        for e in self.edges:
            if e["source"]==concept: hits.append(e)
            elif e["target"]==concept:
                hits.append({**e,"source":e["target"],"target":e["source"]})
        return sorted(hits,key=lambda e:e.get("weight",0),reverse=True)[:limit]

    def seed_labels(self):
        return list(self.nodes)
