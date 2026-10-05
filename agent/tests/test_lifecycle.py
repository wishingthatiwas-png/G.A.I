from core.lifecycle import Lifecycle,Phase

def test_charge_cycle_enters_dream_once():
    l=Lifecycle(target=1.0)
    assert l.update_power(.6,True).phase==Phase.PRE_SLEEP
    l.enter_dream()
    assert l.state.phase==Phase.DREAM
    assert l.update_power(.6,True).phase==Phase.DREAM
    assert l.state.dream_cycles==1

def test_full_charge_wakes_and_latches_until_unplug():
    l=Lifecycle(target=1.0)
    l.update_power(.6,True)
    l.enter_dream()
    assert l.update_power(1.0,True).phase==Phase.WAKE
    l.finish_wake()
    assert l.state.phase==Phase.AWAKE
    assert l.update_power(1.0,True).phase==Phase.AWAKE
    assert l.update_power(1.0,False).phase==Phase.AWAKE

def test_unplug_wakes_mid_dream():
    l=Lifecycle(target=1.0)
    l.update_power(.6,True)
    l.enter_dream()
    assert l.update_power(.7,False).phase==Phase.WAKE
