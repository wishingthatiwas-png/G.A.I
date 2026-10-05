import json
from time import sleep
from core.nervous import Event, NervousSystem


def test_phase_gating_counts_only_matching_subscriptions():
    n = NervousSystem()
    awake = []
    dream = []
    n.subscribe("sense.*", lambda e: awake.append(e.kind), name="awake", phases={"awake"})
    n.subscribe("control.*", lambda e: dream.append(e.kind), name="dream", phases={"dream"})
    n.set_phase("dream")
    n.publish("sense.frame", source="camera")
    assert n.dispatch() == 0
    assert awake == []
    assert dream == []
    assert n.metrics["gated"] == 1


def test_priority_is_global_across_mailboxes():
    n = NervousSystem()
    seen = []
    n.subscribe("*", lambda e: seen.append(("a", e.kind)), name="a")
    n.subscribe("*", lambda e: seen.append(("b", e.kind)), name="b")
    n.publish("slow", source="a", priority="background")
    n.publish("urgent", source="b", priority="critical")
    n.publish("normal", source="c", priority="normal")
    assert n.dispatch() == 6
    assert seen[0][1] == "urgent"


def test_targeted_delivery_and_trace():
    n = NervousSystem()
    seen = []
    n.subscribe("control.*", lambda e: seen.append(e.kind), name="control", component="control")
    a = n.publish("control.decision", {"action": "explore"}, source="kernel",
                  target="control", correlation_id="t1", provenance="predicted")
    n.publish("control.reward", {"value": .4}, source="reward",
              correlation_id="t1", provenance="learned")
    n.publish("other", source="x", correlation_id="t1")
    assert n.dispatch() == 2
    assert seen == ["control.decision", "control.reward"]
    assert len(n.trace("t1")) == 3
    assert a.correlation_id == "t1"


def test_handler_failure_is_isolated_and_recorded():
    n = NervousSystem()
    n.subscribe("*", lambda e: 1 / 0, name="broken", component="broken")
    n.publish("one", source="test")
    assert n.dispatch() == 0
    assert n.metrics["errors"] == 1
    assert n.components["broken"]["state"] == "degraded"
    assert len(n.dead_letters) == 1


def test_component_health():
    n = NervousSystem()
    n.register_component("camera", kind="sensor", critical=True)
    n.heartbeat("camera", state="running", detail={"fps": 30})
    snap = n.snapshot()
    assert snap["components"]["camera"]["state"] == "running"
    assert snap["components"]["camera"]["detail"]["fps"] == 30
    assert snap["health"]["ok"]


def test_backpressure_protects_high_priority():
    n = NervousSystem(mailbox_limit=2)
    n.subscribe("*", lambda e: None, name="sink")
    n.publish("bg1", priority="background")
    n.publish("bg2", priority="background")
    n.publish("urgent", priority="critical")
    assert n.metrics["evicted"] == 1
    assert n.metrics["dropped"] == 0
    assert [e.kind for e in n.poll("sink", 8)] == ["urgent", "bg1"]


def test_request_reply_round_trip():
    n = NervousSystem()
    replies = []
    n.subscribe("do.*", lambda e: replies.append(
        n.reply(e, "do.done", {"ok": True}, source="server")
    ), name="server-handler", component="server")
    n.subscribe("do.done", lambda e: replies.append(e),
                name="client-handler", component="client")
    req = n.request("do.work", {"x": 1}, source="client", target="server")
    assert req.channel == "request"
    assert n.dispatch() == 2
    assert replies[-1].channel == "reply"
    assert replies[-1].reply_to == req.event_id
    assert len(n.replies(req.correlation_id)) == 1


def test_serialization_and_injection():
    n = NervousSystem()
    seen = []
    n.subscribe("remote.*", lambda e: seen.append(e), name="sink")
    original = Event(
        "remote.sensor", "pi-1", {"value": 7}, 123.0, "abc",
        priority=1, correlation_id="c", channel="sensor"
    )
    restored = Event.from_dict(json.loads(original.to_json()))
    n.inject(restored)
    assert n.dispatch() == 1
    assert seen[0].event_id == "abc"


def test_sleeping_component_is_not_stale():
    n = NervousSystem()
    n.register_component("dreamer", critical=True)
    n.heartbeat("dreamer", state="sleeping")
    assert not n.component_health(stale_after=0)["dreamer"]["stale"]


def test_ttl_expiration():
    n = NervousSystem()
    n.subscribe("ephemeral", lambda e: None, name="sink")
    n.publish("ephemeral", ttl=0)
    sleep(0.001)
    assert n.dispatch() == 0
    assert n.metrics["expired"] == 1
