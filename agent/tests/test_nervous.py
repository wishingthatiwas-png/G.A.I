from core.nervous import NervousSystem

def test_phase_gating():
    n=NervousSystem()
    awake=[]; dream=[]
    n.subscribe("sense.*",lambda e:awake.append(e.kind),name="awake_cell",phases={"awake"})
    n.subscribe("sense.*",lambda e:dream.append(e.kind),name="dream_cell",phases={"dream"})
    n.publish("sense.frame",source="camera")
    assert n.dispatch()==1
    assert awake==["sense.frame"] and dream==[]
    n.set_phase("dream")
    n.publish("sense.frame",source="camera")
    assert n.dispatch()==1
    assert dream==["sense.frame"]
    assert n.metrics["gated"]==2

def test_priority_is_global_across_mailboxes():
    n=NervousSystem()
    seen=[]
    n.subscribe("*",lambda e:seen.append(("a",e.kind)),name="a")
    n.subscribe("*",lambda e:seen.append(("b",e.kind)),name="b")
    n.publish("slow",source="a",priority="background")
    n.publish("urgent",source="b",priority="critical")
    n.publish("normal",source="c",priority="normal")
    assert n.dispatch()==6
    assert seen[0][1]=="urgent"

def test_targeted_delivery_and_trace():
    n=NervousSystem()
    seen=[]
    n.subscribe("control.*",lambda e:seen.append(e.kind),name="control")
    a=n.publish("control.decision",{"action":"explore"},source="kernel",
                target="control",correlation_id="t1",provenance="predicted")
    n.publish("control.reward",{"value":.4},source="reward",
              correlation_id="t1",provenance="learned")
    n.publish("other",source="x",correlation_id="t1")
    assert n.dispatch()==2
    assert seen==["control.decision","control.reward"]
    assert len(n.trace("t1"))==3
    assert a.correlation_id=="t1"

def test_handler_failure_is_isolated():
    n=NervousSystem()
    n.subscribe("*",lambda e:1/0,name="broken")
    n.publish("one",source="test")
    assert n.dispatch()==0
    assert n.metrics["errors"]==1

def test_component_health():
    n=NervousSystem()
    n.register_component("camera",kind="sensor")
    n.heartbeat("camera",state="running",detail={"fps":30})
    snap=n.snapshot()
    assert snap["components"]["camera"]["state"]=="running"
    assert snap["components"]["camera"]["detail"]["fps"]==30
