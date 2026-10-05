from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, random

STATE=Path("/mnt/gai/memory/evolution.json")

@dataclass
class Gene:
    name:str; value:float; minimum:float; maximum:float; mutation:float; generation:int=0

class EvolutionEngine:
    """Dream-only evolutionary selection. Candidates are tested on replay data."""
    def __init__(self):
        defaults={
            "novelty_weight":(0.70,.05,1.50,.08),"prediction_lr":(.15,.01,.50,.03),
            "association_gain":(.20,.02,.80,.04),"reward_gain":(.55,.05,1.50,.06),
            "memory_decay":(.02,.001,.20,.01)}
        self.genes={k:Gene(k,*v) for k,v in defaults.items()}
        self.fitness=0.0; self.generation=0; self.load()

    def load(self):
        if STATE.exists():
            o=json.loads(STATE.read_text())
            self.genes={k:Gene(**v) for k,v in o.get("genes",{}).items()}
            self.fitness=o.get("fitness",0.0); self.generation=o.get("generation",0)

    def save(self):
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps({"generation":self.generation,"fitness":self.fitness,
            "genes":{k:asdict(v) for k,v in self.genes.items()}},indent=2))

    def phenotype(self):
        return {k:g.value for k,g in self.genes.items()}

    def mutate(self, genes):
        child={k:Gene(g.name,g.value,g.minimum,g.maximum,g.mutation,g.generation+1) for k,g in genes.items()}
        for g in child.values():
            if random.random()<0.75:
                delta=random.gauss(0,g.mutation)
                g.value=max(g.minimum,min(g.maximum,g.value+delta))
        return child

    def fitness_for(self, genes, events):
        if not events: return 0.0
        lr=genes["prediction_lr"].value
        reward_gain=genes["reward_gain"].value
        error_sum=0.0; reward_sum=0.0
        for e in events:
            reward=float(e.get("reward",0)); err=abs(float(e.get("prediction_error",0)))
            # Lower replay error + useful reward = better phenotype.
            error_sum += err*(1.0+lr)
            reward_sum += reward*reward_gain
        return reward_sum/len(events) - error_sum/len(events)

    def dream_select(self, events, population=8):
        """Generate candidates, replay-score them, keep the fittest."""
        events=list(events or [])
        if not events:
            return {"generation":self.generation,"fitness":self.fitness,
                    "population":0,"genes":self.phenotype(),"candidate_scores":[]}
        candidates=[self.genes]
        for _ in range(max(1,population-1)):
            candidates.append(self.mutate(self.genes))
        scored=[(self.fitness_for(c,events),c) for c in candidates]
        scored.sort(key=lambda x:x[0],reverse=True)
        best_score,best=scored[0]
        self.genes=best
        self.fitness=best_score
        self.generation+=1
        for g in self.genes.values(): g.generation=self.generation
        self.save()
        return {"generation":self.generation,"fitness":self.fitness,
                "population":len(scored),"genes":self.phenotype(),
                "candidate_scores":[round(x[0],6) for x in scored]}

    def dream_mutation(self,reward,prediction_error):
        # Compatibility shim: single-event evolutionary selection.
        return self.dream_select([{"reward":reward,"prediction_error":prediction_error}],population=4)
