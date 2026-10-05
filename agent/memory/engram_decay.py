from __future__ import annotations

def decay(memory, rate: float, floor: float = 0.001):
    """Apply bounded long-term weakening to rarely useful associations."""
    rate=max(0.0,min(1.0,float(rate)))
    removed=0
    for key,edge in list(memory.edges.items()):
        edge.weight*=1.0-rate
        edge.reinforcement*=1.0-rate*0.5
        if edge.weight < floor:
            del memory.edges[key]
            removed+=1
    memory._save()
    return removed
