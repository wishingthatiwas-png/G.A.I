"""Experience -> salience -> sleep queue -> symbolic long-term memory pipeline."""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Experience:
    kind: str
    content: dict
    timestamp: float = 0.0
    novelty: float = 0.0
    emotional_intensity: float = 0.0
    reward: float = 0.0
    repetition: float = 0.0
    importance: float = 0.0
    memory_id: str = ""
    def __post_init__(self):
        if not self.timestamp: self.timestamp=time.time()
        if not self.memory_id:
            raw=json.dumps([self.kind,self.content,self.timestamp],sort_keys=True).encode()
            self.memory_id="mem-"+hashlib.sha256(raw).hexdigest()[:16]

class SalienceModel:
    def score(self,e: Experience)->float:
        # Emotional/novel/rewarding events survive better; repetition stabilises memory.
        base=(0.25*e.novelty + 0.30*e.emotional_intensity +
              0.15*min(1.0,abs(e.reward)) + 0.15*e.repetition + 0.15*e.importance)
        return max(0.0,min(1.0,base))

class MemoryPipeline:
    def __init__(self, root: str|Path='/mnt/gai/memory'):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.queue=self.root/'sleep_queue.jsonl'
        self.index=self.root/'experience_index.jsonl'
        self.salience=SalienceModel()
        # Awake recall must be O(1) with respect to lifetime memory. Keep a
        # bounded in-memory index; sleep/consolidation handles the full archive.
        self._index_cache=[]
        if self.index.exists():
            try:
                lines=self.index.read_text().splitlines()[-2000:]
                for line in lines:
                    try: self._index_cache.append(json.loads(line))
                    except Exception: pass
            except OSError: pass

    def ingest(self,e: Experience)->float:
        score=self.salience.score(e)
        e.importance=max(e.importance,score)
        with self.queue.open('a') as f: f.write(json.dumps(asdict(e),sort_keys=True)+'\n')
        entry={'memory_id':e.memory_id,'timestamp':e.timestamp,'salience':score,'kind':e.kind,'words':e.content.get('words',[])}
        with self.index.open('a') as f: f.write(json.dumps(entry)+'\n')
        self._index_cache.append(entry)
        if len(self._index_cache) > 2000: self._index_cache = self._index_cache[-2000:]
        return score

    def reinforce(self, memory_id: str, amount: float = 0.10):
        """Strengthen a queued experience when it is recalled/relevant."""
        if not self.queue.exists(): return False
        rows=[]; found=False
        for line in self.queue.read_text().splitlines():
            try: d=json.loads(line)
            except Exception: rows.append(line); continue
            if d.get("memory_id") == memory_id:
                d["repetition"]=min(1.0,float(d.get("repetition",0.0))+amount)
                d["importance"]=min(1.0,float(d.get("importance",0.0))+amount*.5)
                found=True
            rows.append(json.dumps(d,sort_keys=True))
        self.queue.write_text(('\n'.join(rows)+'\n') if rows else '')
        return found

    def decay(self, amount: float = 0.02):
        """Apply gentle forgetting to queued experiences before consolidation."""
        if not self.queue.exists(): return
        rows=[]
        for line in self.queue.read_text().splitlines():
            try: d=json.loads(line)
            except Exception: continue
            d["novelty"]=max(0.0,float(d.get("novelty",0.0))-amount)
            d["importance"]=max(0.0,float(d.get("importance",0.0))-amount*.5)
            rows.append(json.dumps(d,sort_keys=True))
        self.queue.write_text(('\n'.join(rows)+'\n') if rows else '')

    def select_for_sleep(self, threshold=.45, limit=500):
        if not self.queue.exists(): return []
        selected=[]
        for line in self.queue.read_text().splitlines():
            try: e=Experience(**json.loads(line))
            except Exception: continue
            if self.salience.score(e)>=threshold: selected.append(e)
            if len(selected)>=limit: break
        return selected

    @staticmethod
    def symbolic_encode(e: Experience)->dict:
        # Compact, model-independent representation: words + shapes/relations.
        c=e.content
        return {'memory_id':e.memory_id,'type':'symbolic_reconstruction','words':c.get('words',[]),
                'shapes':c.get('shapes',[]),'objects':c.get('objects',[]),'relations':c.get('relations',[]),
                'focus':c.get('focus'),'emotion':c.get('emotion',{}),'context':c.get('context',{}),
                'salience':e.importance,'source_timestamp':e.timestamp}


    def retrieve(self, query_words=None, limit=8):
        """Retrieve from the bounded awake index; never rescan lifetime memory."""
        query=set(w.lower() for w in (query_words or []))
        scored=[]
        for d in self._index_cache:
            words=set(str(w).lower() for w in d.get("words",[]))
            overlap=len(query & words) if query else 0
            score=float(d.get("salience",0.0)) + overlap*0.2
            scored.append((score,d))
        scored.sort(key=lambda x:x[0],reverse=True)
        return [d for _,d in scored[:limit]]


    def reconstruct(self, memory_id: str):
        """Load a stored symbolic memory for later generative reconstruction."""
        root=self.root / "long_term"
        candidates=[root / f"{memory_id}.json", Path("/mnt/gai/archive/long_term/memories") / f"{memory_id}.json"]
        for path in candidates:
            if path.exists():
                try:
                    d=json.loads(path.read_text())
                    return d.get("payload", d)
                except Exception:
                    return None
        return None

    def create_reconstruction_prompt(self, symbolic: dict)->str:
        """Turn symbolic memory into a deterministic visual-language prompt."""
        if not symbolic: return ""
        return json.dumps({
            "words": symbolic.get("words", []), "shapes": symbolic.get("shapes", []),
            "objects": symbolic.get("objects", []), "relations": symbolic.get("relations", []),
            "focus": symbolic.get("focus"), "context": symbolic.get("context", {}),
            "emotion": symbolic.get("emotion", {})
        }, sort_keys=True)

    def local_commit(self, memory_id: str, symbolic: dict):
        """Commit a consolidated memory to the always-present SSD memory organ."""
        target = self.root / "long_term" / f"{memory_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"payload": symbolic, "storage": "ssd", "committed_at": time.time()}
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2))
        tmp.replace(target)
        return str(target)

    def pressure(self, soft_limit=2000):
        """Estimate cognitive load from pending memory, not just raw count.

        Repetition compresses naturally; novel/high-salience experiences cost more.
        """
        if not self.queue.exists():
            return 0.0
        try:
            total = 0.0
            for line in self.queue.open():
                try:
                    e = Experience(**json.loads(line))
                    novelty = 0.35 + 0.65 * e.novelty
                    salience = 0.50 + 0.50 * self.salience.score(e)
                    repetition_relief = max(0.20, 1.0 - 0.60 * e.repetition)
                    total += novelty * salience * repetition_relief
                except Exception:
                    total += 0.25
        except OSError:
            return 0.0
        return max(0.0, min(1.0, total / max(1, int(soft_limit))))

    def consolidate(self, writer, threshold=.45, limit=500):
        selected=self.select_for_sleep(threshold,limit)
        committed=[]
        for e in selected:
            committed.append(writer(e.memory_id,self.symbolic_encode(e)))
        if selected:
            selected_ids={e.memory_id for e in selected}
            remaining=[]
            for line in self.queue.read_text().splitlines():
                try: mid=json.loads(line)['memory_id']
                except Exception: remaining.append(line); continue
                if mid not in selected_ids: remaining.append(line)
            self.queue.write_text(('\n'.join(remaining)+'\n') if remaining else '')
        return committed
