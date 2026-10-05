from __future__ import annotations
from dataclasses import dataclass,asdict
import time
from .nervous import NervousSystem

@dataclass
class Signal:
    name:str
    value:float=0.0
    confidence:float=0.5
    novelty:float=0.0
    timestamp:float=0.0

    def emit(self,value,confidence=0.5,novelty=0.0):
        self.value=max(-1.0,min(1.0,float(value)))
        self.confidence=max(0.0,min(1.0,float(confidence)))
        self.novelty=max(0.0,min(1.0,float(novelty)))
        self.timestamp=time.time()
        return self

class AdaptiveSignal:
    def __init__(self,name,rate=0.08):
        self.name=name; self.rate=rate
        self.baseline=0.0; self.error=0.0; self.exposure=0

    def update(self,value):
        value=float(value); self.error=value-self.baseline
        self.baseline+=self.rate*self.error; self.exposure+=1
        return Signal(self.name,value,1.0,min(1.0,abs(self.error)),time.time())

class SignalBus:
    """Signal layer on top of the G.A.I. nervous system."""
    def __init__(self,nervous=None):
        self.nervous=nervous or NervousSystem()
        self._signals={}; self._adaptive={}

    def publish(self,name,value,confidence=0.5,adaptive=False,source="signal"):
        if adaptive:
            learner=self._adaptive.setdefault(name,AdaptiveSignal(name))
            signal=learner.update(value)
        else:
            signal=Signal(name,value,confidence,0.0,time.time())
        self._signals[name]=signal
        self.nervous.publish("signal."+name,asdict(signal),source=source,
                             confidence=signal.confidence,novelty=signal.novelty)
        return signal

    def get(self,name,default=0.0):
        return self._signals.get(name,Signal(name,default)).value

    def snapshot(self):
        return {k:asdict(v) for k,v in self._signals.items()}

    def learning_snapshot(self):
        return {k:{"baseline":v.baseline,"error":v.error,"exposure":v.exposure}
                for k,v in self._adaptive.items()}

    def subscribe(self,pattern,handler,name=None,phases=None):
        return self.nervous.subscribe(pattern,handler,name=name,phases=phases)

    def emit(self,kind,payload=None,**kwargs):
        return self.nervous.publish(kind,payload,**kwargs)

    def poll(self,name,limit=32):
        return self.nervous.poll(name,limit)

    def dispatch(self,limit=64):
        return self.nervous.dispatch(limit)

    def latest(self,pattern=None,limit=20):
        return self.nervous.latest(pattern,limit)

    def nervous_snapshot(self):
        return self.nervous.snapshot()
