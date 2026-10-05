from __future__ import annotations
from time import time

class Cell:
    """Standard contract for a G.A.I. nervous-system subsystem."""
    def __init__(self,name,nervous,version="0.1.0",sleep_phases=None):
        self.name=name; self.nervous=nervous; self.version=version
        self.sleep_phases=set(sleep_phases or {"awake"})
        self.bindings=[]; self.started=False; self.state="stopped"

    def start(self):
        if self.started: return self
        self.nervous.register_component(self.name,kind="cell",
                                        version=self.version,sleep_capable=True)
        for pattern,handler in self.bindings:
            sub=self.nervous.subscribe(pattern,handler,name=self.name+"."+pattern,
                                       phases=self.sleep_phases)
            self.bindings[self.bindings.index((pattern,handler))]=(pattern,handler,sub)
        self.started=True; self.state="running"; self.heartbeat()
        return self

    def listen(self,pattern,handler=None,phases=None):
        if handler is None: handler=self.on_event
        allowed=set(phases) if phases else self.sleep_phases
        self.sleep_phases=allowed
        self.bindings.append((pattern,handler))
        if self.started:
            sub=self.nervous.subscribe(pattern,handler,name=self.name+"."+pattern,
                                       phases=allowed)
            self.bindings[-1]=(pattern,handler,sub)
        return handler

    def on_event(self,event):
        pass

    def heartbeat(self,detail=None):
        self.nervous.heartbeat(self.name,self.state,detail)

    def sleep(self):
        self.state="sleeping"; self.heartbeat()

    def wake(self):
        self.state="running"; self.heartbeat()

    def publish(self,kind,payload=None,**kwargs):
        return self.nervous.publish(kind,payload,source=self.name,**kwargs)

    def stop(self):
        for binding in self.bindings:
            if len(binding)==3:
                self.nervous.unsubscribe(binding[2])
        self.started=False; self.state="stopped"; self.heartbeat()
