from __future__ import annotations
from dataclasses import dataclass,asdict
from threading import RLock
from fnmatch import fnmatch
from time import time
import uuid

PRIORITY={"critical":0,"control":1,"normal":2,"background":3}

@dataclass(frozen=True)
class Event:
    kind:str
    source:str
    payload:dict
    timestamp:float
    event_id:str
    priority:int=2
    target:str|None=None
    correlation_id:str|None=None
    provenance:str="direct"
    confidence:float=1.0
    novelty:float=0.0

class NervousSystem:
    """Backbone: routing, ordering, sleep gating, isolation, tracing and health."""
    def __init__(self,history_limit=2000,mailbox_limit=512):
        self.history=[]; self.history_limit=history_limit
        self.mailboxes={}; self.handlers={}; self.subscriptions=[]
        self.mailbox_limit=mailbox_limit; self.phase="awake"
        self.components={}; self.lock=RLock()
        self.metrics={"published":0,"delivered":0,"dropped":0,"gated":0,"errors":0}

    def register_component(self,name,kind="cell",version="0.1.0",sleep_capable=True):
        with self.lock:
            self.components[name]={"name":name,"kind":kind,"version":version,
                                   "sleep_capable":sleep_capable,"state":"starting",
                                   "last_heartbeat":time()}
        return name

    def heartbeat(self,name,state="running",detail=None):
        with self.lock:
            if name not in self.components:
                self.register_component(name)
            c=self.components[name]; c["state"]=state
            c["last_heartbeat"]=time()
            if detail is not None: c["detail"]=detail

    def subscribe(self,pattern,handler,name=None,phases=None):
        name=name or getattr(handler,"__name__","handler")
        sub={"pattern":pattern,"handler":handler,"name":name,
             "phases":set(phases) if phases else None}
        with self.lock:
            self.subscriptions.append(sub); self.mailboxes.setdefault(name,[])
            self.handlers[name]=handler
            self.components.setdefault(name,{"name":name,"kind":"handler",
                "version":"0.1.0","sleep_capable":True,"state":"running",
                "last_heartbeat":time()})
        return name

    def unsubscribe(self,name):
        with self.lock:
            self.subscriptions=[s for s in self.subscriptions if s["name"]!=name]
            self.handlers.pop(name,None); self.mailboxes.pop(name,None)

    def set_phase(self,phase):
        with self.lock: self.phase=str(phase)

    def publish(self,kind,payload=None,*,source="unknown",priority="normal",
                target=None,correlation_id=None,provenance="direct",
                confidence=1.0,novelty=0.0):
        event=Event(kind,source,dict(payload or {}),time(),uuid.uuid4().hex,
                    PRIORITY.get(priority,2),target,correlation_id,provenance,
                    max(0,min(1,float(confidence))),max(0,min(1,float(novelty))))
        with self.lock:
            if len(self.history)>=self.history_limit: self.history.pop(0)
            self.history.append(event); self.metrics["published"]+=1
            for sub in self.subscriptions:
                if target and sub["name"]!=target: continue
                if sub["phases"] and self.phase not in sub["phases"]:
                    self.metrics["gated"]+=1; continue
                if fnmatch(kind,sub["pattern"]):
                    box=self.mailboxes[sub["name"]]
                    if len(box)>=self.mailbox_limit:
                        self.metrics["dropped"]+=1
                    else: box.append(event)
        return event

    def _take(self,box,limit):
        out=[]
        for _ in range(min(limit,len(box))):
            idx=min(range(len(box)),key=lambda i:(box[i].priority,box[i].timestamp))
            out.append(box.pop(idx))
        return out

    def poll(self,name,limit=32):
        with self.lock:
            box=self.mailboxes.get(name)
            return self._take(box,limit) if box is not None else []

    def dispatch(self,limit=64):
        delivered=0
        while delivered<limit:
            with self.lock:
                choices=[(n,min(b,key=lambda e:(e.priority,e.timestamp))) for n,b in self.mailboxes.items() if b]
                if not choices: break
            name,_=min(choices,key=lambda x:(x[1].priority,x[1].timestamp))
            event=self.poll(name,1); handler=self.handlers.get(name)
            if not event or not handler: continue
            try:
                handler(event[0]); delivered+=1
            except Exception: self.metrics["errors"]+=1
        self.metrics["delivered"]+=delivered
        return delivered

    def latest(self,pattern=None,limit=20):
        with self.lock: items=list(self.history)
        if pattern: items=[e for e in items if fnmatch(e.kind,pattern)]
        return [asdict(e) for e in items[-limit:]]

    def trace(self,correlation_id):
        with self.lock:
            return [asdict(e) for e in self.history if e.correlation_id==correlation_id]

    def snapshot(self):
        with self.lock:
            return {"phase":self.phase,"metrics":dict(self.metrics),
                    "components":dict(self.components),
                    "subscriptions":[s["name"]+":"+s["pattern"] for s in self.subscriptions],
                    "mailboxes":{k:len(v) for k,v in self.mailboxes.items()},
                    "history_depth":len(self.history)}
