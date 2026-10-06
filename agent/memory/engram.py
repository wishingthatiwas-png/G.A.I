from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, math, time, uuid

MEMORY_DIR = Path('/mnt/gai/memory/engrams')

@dataclass
class Neuron:
    id: int
    label: str
    activation: float = 0.0

@dataclass
class Association:
    source: int
    target: int
    weight: float = 0.0
    reinforcement: float = 0.0
    last_fired: float = 0.0

@dataclass
class Engram:
    id: str
    timestamp: float
    stimuli: list[int]
    emotions: dict[str, float]
    context: dict
    salience: float
    reward: float
    associations: list[dict]

class AssociativeMemory:
    """Simple persistent engram system inspired by neuron firing/Hebbian association.

    IDs provide stable concepts. Repeated co-activation strengthens edges;
    emotionally salient/rewarding events strengthen them more strongly.
    This is an engineering model, not a claim of biological equivalence.
    """
    def __init__(self, association_gain=1.0):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.association_gain=float(association_gain)
        self.neurons: dict[str, Neuron] = {}
        self.edges: dict[tuple[int,int], Association] = {}
        self._persist_counter = 0
        self._load()

    def _load(self):
        p = MEMORY_DIR / 'network.json'
        if not p.exists(): return
        obj = json.loads(p.read_text())
        self.neurons = {n['label']: Neuron(**n) for n in obj.get('neurons', [])}
        self.edges = {(e['source'],e['target']): Association(**e) for e in obj.get('associations', [])}

    def _save(self):
        p = MEMORY_DIR / 'network.json'
        p.write_text(json.dumps({'neurons':[asdict(n) for n in self.neurons.values()], 'associations':[asdict(e) for e in self.edges.values()]}, indent=2))

    def neuron(self, label: str) -> int:
        if label not in self.neurons:
            self.neurons[label] = Neuron(id=len(self.neurons)+1, label=label)
        return self.neurons[label].id

    def fire(self, labels: list[str], emotions: dict[str,float] | None = None, context=None, reward=0.0, salience=None):
        emotions = emotions or {}
        ids = [self.neuron(x) for x in labels]
        emotional_intensity = min(1.0, sum(abs(v) for v in emotions.values()) / max(1, len(emotions)))
        if salience is None:
            salience = min(1.0, 0.35 + 0.45*emotional_intensity + 0.20*abs(reward))
        now = time.time()
        associations=[]
        # Hebbian-style co-firing: repeated stimulus/emotion co-activation strengthens edges.
        for i, a in enumerate(ids):
            for b in ids[i+1:]:
                key=(a,b)
                edge=self.edges.get(key, Association(a,b))
                delta=self.association_gain*(0.05 + 0.20*salience + 0.15*max(0.0,reward))
                edge.weight=min(1.0, edge.weight + delta)
                edge.reinforcement += delta
                edge.last_fired=now
                self.edges[key]=edge
                associations.append(asdict(edge))
        engram=Engram(uuid.uuid4().hex, now, ids, emotions, context or {}, salience, reward, associations)
        self._persist_counter += 1
        # Association weights learn immediately in RAM. Disk persistence is a
        # slower memory-consolidation process, so don't serialize the whole graph
        # or create a file on every biological tick.
        if self._persist_counter % 5 == 0:
            (MEMORY_DIR / f'{engram.id}.json').write_text(json.dumps(asdict(engram), indent=2))
            self._save()
        return engram

    def strongest(self, label: str, limit=8):
        nid=self.neuron(label)
        edges=[e for e in self.edges.values() if e.source==nid or e.target==nid]
        edges.sort(key=lambda e:e.weight, reverse=True)
        byid={n.id:n.label for n in self.neurons.values()}
        return [{'label':byid.get(e.target if e.source==nid else e.source), 'weight':e.weight} for e in edges[:limit]]
