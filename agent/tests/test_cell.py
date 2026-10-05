from core.cell import Cell
from core.nervous import NervousSystem
from core.working_memory import WorkingMemoryCell

def test_cell_contract_and_phase_subscription():
    n=NervousSystem()
    c=WorkingMemoryCell(n).start()
    assert c.started
    n.publish("control.decision",{"action":"explore"},source="control")
    assert n.dispatch()==1
    assert c.recall(1)[0]["payload"]["action"]=="explore"
    assert n.snapshot()["components"]["working_memory"]["state"]=="running"

def test_cell_sleep_gates_delivery():
    n=NervousSystem()
    c=Cell("sleepy",n,sleep_phases={"awake"})
    seen=[]
    c.listen("x",lambda e:seen.append(e.kind))
    c.start()
    n.set_phase("dream")
    n.publish("x",source="test")
    assert n.dispatch()==0
    assert seen==[]
