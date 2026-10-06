from __future__ import annotations

from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from threading import RLock
from time import time
from typing import Protocol
import json
import uuid
import heapq

PRIORITY = {"critical": 0, "control": 1, "normal": 2, "background": 3}
PHASES = {"awake", "pre_sleep", "dream", "wake"}


class EventTransport(Protocol):
    def send(self, event: "Event") -> None: ...


@dataclass(frozen=True)
class Event:
    """Immutable message flowing through G.A.I.'s internal nervous system."""
    kind: str
    source: str
    payload: dict
    timestamp: float
    event_id: str
    priority: int = 2
    target: str | None = None
    correlation_id: str | None = None
    provenance: str = "direct"
    confidence: float = 1.0
    novelty: float = 0.0
    channel: str = "event"
    reply_to: str | None = None
    ttl: float | None = None
    sequence: int = 0

    def as_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**dict(data))


class NervousSystem:
    """Backbone for routing, ordering, gating, supervision, tracing and transport."""

    def __init__(self, history_limit=2000, mailbox_limit=512, dead_letter_limit=256):
        self.history: list[Event] = []
        self.history_limit = int(history_limit)
        self.mailboxes: dict[str, list[Event]] = {}
        self.subscriptions: dict[str, dict] = {}
        self._exact_routes = {}
        self._wildcard_routes = set()
        self.mailbox_limit = int(mailbox_limit)
        self.phase = "awake"
        self.components: dict[str, dict] = {}
        self.dead_letters: list[dict] = []
        self.dead_letter_limit = int(dead_letter_limit)
        self.lock = RLock()
        self.sequence = 0
        # Ready-event heap: dispatch no longer scans every mailbox on every event.
        self._ready_heap = []
        self.transport: EventTransport | None = None
        self.metrics = {
            "published": 0,
            "matched": 0,
            "delivered": 0,
            "dropped": 0,
            "evicted": 0,
            "expired": 0,
            "gated": 0,
            "errors": 0,
            "transport_errors": 0,
        }

    def register_component(self, name, kind="cell", version="0.1.0",
                           sleep_capable=True, critical=False):
        with self.lock:
            existing = self.components.get(name, {})
            self.components[name] = {
                "name": name,
                "kind": kind,
                "version": version,
                "sleep_capable": bool(sleep_capable),
                "critical": bool(critical),
                "state": existing.get("state", "starting"),
                "last_heartbeat": existing.get("last_heartbeat", time()),
                "heartbeat_count": existing.get("heartbeat_count", 0),
                "event_count": existing.get("event_count", 0),
                "error_count": existing.get("error_count", 0),
            }
        return name

    def heartbeat(self, name, state="running", detail=None):
        now = time()
        with self.lock:
            if name not in self.components:
                self.register_component(name)
            c = self.components[name]
            c["state"] = state
            c["last_heartbeat"] = now
            c["heartbeat_count"] = c.get("heartbeat_count", 0) + 1
            if detail is not None:
                c["detail"] = detail

    def component_health(self, stale_after=15.0):
        now = time()
        with self.lock:
            result = {}
            for name, c in self.components.items():
                age = max(0.0, now - c.get("last_heartbeat", now))
                state = c.get("state", "unknown")
                stale = age > stale_after and state not in {"planned", "stopped", "sleeping"}
                result[name] = {
                    **c,
                    "heartbeat_age": round(age, 3),
                    "stale": stale,
                }
            return result

    def health(self, stale_after=15.0):
        components = self.component_health(stale_after)
        critical_stale = [
            n for n, c in components.items() if c.get("critical") and c["stale"]
        ]
        degraded = [
            n for n, c in components.items()
            if c.get("state") in {"degraded", "error"}
        ]
        return {
            "ok": not critical_stale and not degraded,
            "phase": self.phase,
            "critical_stale": critical_stale,
            "degraded": degraded,
            "components": components,
            "mailboxes": self.mailbox_depths(),
        }

    def subscribe(self, pattern, handler, name=None, phases=None, component=None):
        name = name or getattr(handler, "__name__", "handler")
        token = f"{name}:{uuid.uuid4().hex[:10]}"
        sub = {
            "token": token,
            "name": name,
            "component": component or name.split(".", 1)[0],
            "pattern": pattern,
            "handler": handler,
            "phases": set(phases) if phases else None,
        }
        with self.lock:
            self.subscriptions[token] = sub
            self.mailboxes.setdefault(token, [])
            if any(ch in str(pattern) for ch in "*?["):
                self._wildcard_routes.add(token)
            else:
                self._exact_routes.setdefault(str(pattern), set()).add(token)
            if any(ch in str(pattern) for ch in "*?["):
                self._wildcard_routes.add(token)
            else:
                self._exact_routes.setdefault(str(pattern), set()).add(token)
            component_name = sub["component"]
            self.components.setdefault(component_name, {
                "name": component_name,
                "kind": "handler",
                "version": "0.1.0",
                "sleep_capable": True,
                "critical": False,
                "state": "running",
                "last_heartbeat": time(),
                "heartbeat_count": 0,
                "event_count": 0,
                "error_count": 0,
            })
        return token

    def unsubscribe(self, token_or_name):
        with self.lock:
            tokens = [
                token for token, sub in self.subscriptions.items()
                if token == token_or_name or sub["name"] == token_or_name
                or sub["component"] == token_or_name
            ]
            for token in tokens:
                sub = self.subscriptions.pop(token, None)
                self.mailboxes.pop(token, None)
                self._wildcard_routes.discard(token)
                if sub is not None:
                    route = self._exact_routes.get(str(sub["pattern"]))
                    if route is not None:
                        route.discard(token)
                        if not route:
                            self._exact_routes.pop(str(sub["pattern"]), None)
        return len(tokens)

    def set_phase(self, phase):
        phase = str(phase)
        if phase not in PHASES:
            raise ValueError(f"unknown nervous-system phase: {phase}")
        with self.lock:
            self.phase = phase

    def attach_transport(self, transport: EventTransport | None):
        with self.lock:
            self.transport = transport

    def _normalise_priority(self, priority):
        if isinstance(priority, str):
            return PRIORITY.get(priority, PRIORITY["normal"])
        return max(0, min(3, int(priority)))

    def _build_event(self, kind, payload, *, source, priority, target,
                     correlation_id, provenance, confidence, novelty,
                     channel, reply_to, ttl):
        with self.lock:
            self.sequence += 1
            sequence = self.sequence
        return Event(
            kind=str(kind),
            source=str(source),
            payload=dict(payload or {}),
            timestamp=time(),
            event_id=uuid.uuid4().hex,
            priority=self._normalise_priority(priority),
            target=str(target) if target else None,
            correlation_id=correlation_id,
            provenance=str(provenance),
            confidence=max(0.0, min(1.0, float(confidence))),
            novelty=max(0.0, min(1.0, float(novelty))),
            channel=str(channel),
            reply_to=reply_to,
            ttl=None if ttl is None else max(0.0, float(ttl)),
            sequence=sequence,
        )

    def _enqueue(self, token, event):
        box = self.mailboxes[token]
        if len(box) < self.mailbox_limit:
            box.append(event)
            heapq.heappush(self._ready_heap, (event.priority, event.timestamp, event.sequence, token))
            return True
        worst = max(range(len(box)), key=lambda i: (box[i].priority, box[i].timestamp))
        if event.priority < box[worst].priority:
            box.pop(worst)
            box.append(event)
            heapq.heappush(self._ready_heap, (event.priority, event.timestamp, event.sequence, token))
            self.metrics["evicted"] += 1
            return True
        self.metrics["dropped"] += 1
        return False

    def _route(self, event, forward=True):
        now = time()
        with self.lock:
            self.history.append(event)
            if len(self.history) > self.history_limit:
                del self.history[:len(self.history) - self.history_limit]
            self.metrics["published"] += 1

            candidates = set(self._exact_routes.get(event.kind, ()))
            candidates.update(self._wildcard_routes)
            for token in candidates:
                sub = self.subscriptions.get(token)
                if sub is None:
                    continue
                if event.target and event.target not in {sub["name"], sub["component"]}:
                    continue
                if token in self._wildcard_routes and not fnmatch(event.kind, sub["pattern"]):
                    continue
                self.metrics["matched"] += 1
                if sub["phases"] and self.phase not in sub["phases"]:
                    self.metrics["gated"] += 1
                    continue
                if event.ttl is not None and now - event.timestamp > event.ttl:
                    self.metrics["expired"] += 1
                    continue
                self._enqueue(token, event)

        transport = self.transport
        if forward and transport:
            try:
                transport.send(event)
            except Exception:
                with self.lock:
                    self.metrics["transport_errors"] += 1
        return event

    def publish(self, kind, payload=None, *, source="unknown",
                priority="normal", target=None, correlation_id=None,
                provenance="direct", confidence=1.0, novelty=0.0,
                channel="event", reply_to=None, ttl=None):
        event = self._build_event(
            kind, payload, source=source, priority=priority, target=target,
            correlation_id=correlation_id, provenance=provenance,
            confidence=confidence, novelty=novelty, channel=channel,
            reply_to=reply_to, ttl=ttl,
        )
        return self._route(event)

    def inject(self, event):
        if not isinstance(event, Event):
            event = Event.from_dict(event)
        return self._route(event, forward=False)

    def request(self, kind, payload=None, *, source, target, priority="control",
                correlation_id=None, provenance="request", **kwargs):
        correlation_id = correlation_id or uuid.uuid4().hex
        return self.publish(
            kind, payload, source=source, target=target, priority=priority,
            correlation_id=correlation_id, channel="request",
            provenance=provenance, **kwargs,
        )

    def reply(self, request_event, kind, payload=None, *, source,
              priority="control", provenance="reply", **kwargs):
        if not isinstance(request_event, Event):
            request_event = Event.from_dict(request_event)
        return self.publish(
            kind, payload, source=source, target=request_event.source,
            priority=priority, correlation_id=request_event.correlation_id,
            channel="reply", reply_to=request_event.event_id,
            provenance=provenance, **kwargs,
        )

    def replies(self, correlation_id, limit=32):
        with self.lock:
            items = [
                e for e in self.history
                if e.correlation_id == correlation_id and e.channel == "reply"
            ]
        return [e.as_dict() for e in items[-limit:]]

    def _take(self, token, limit):
        box = self.mailboxes.get(token)
        if box is None:
            return []
        out = []
        now = time()
        for _ in range(min(int(limit), len(box))):
            idx = min(range(len(box)), key=lambda i: (box[i].priority, box[i].timestamp))
            event = box.pop(idx)
            if event.ttl is not None and now - event.timestamp > event.ttl:
                self.metrics["expired"] += 1
                continue
            out.append(event)
        return out

    def poll(self, token_or_name, limit=32):
        with self.lock:
            tokens = [
                token for token, sub in self.subscriptions.items()
                if token == token_or_name or sub["name"] == token_or_name
                or sub["component"] == token_or_name
            ]
            if not tokens:
                return []
            out = []
            remaining = max(0, int(limit))
            for token in tokens:
                if remaining <= 0:
                    break
                before = len(out)
                out.extend(self._take(token, remaining))
                remaining -= len(out) - before
            out.sort(key=lambda e: (e.priority, e.timestamp))
            return out

    def dispatch(self, limit=64):
        delivered = 0
        while delivered < int(limit):
            with self.lock:
                event_batch = []
                token = None
                # Heap entries can become stale after polling/eviction; discard them lazily.
                while self._ready_heap:
                    _, _, _, candidate = heapq.heappop(self._ready_heap)
                    box = self.mailboxes.get(candidate)
                    if box:
                        token = candidate
                        event_batch = self._take(token, 1)
                        break
                if not event_batch:
                    break
                sub = self.subscriptions.get(token)
                handler = sub.get("handler") if sub else None
                component = sub.get("component", token) if sub else token
            if handler is None:
                continue
            event = event_batch[0]
            try:
                handler(event)
                with self.lock:
                    self.metrics["delivered"] += 1
                    c = self.components.get(component)
                    if c:
                        c["event_count"] = c.get("event_count", 0) + 1
                        c["state"] = "running"
                        c["last_heartbeat"] = time()
                delivered += 1
            except Exception as exc:
                with self.lock:
                    self.metrics["errors"] += 1
                    c = self.components.get(component)
                    if c:
                        c["error_count"] = c.get("error_count", 0) + 1
                        c["state"] = "degraded"
                        c["last_error"] = str(exc)
                        c["last_error_event"] = event.event_id
                    self.dead_letters.append({
                        "event": event.as_dict(),
                        "component": component,
                        "error": repr(exc),
                        "timestamp": time(),
                    })
                    if len(self.dead_letters) > self.dead_letter_limit:
                        del self.dead_letters[:len(self.dead_letters) - self.dead_letter_limit]
        return delivered

    def latest(self, pattern=None, limit=20):
        with self.lock:
            items = list(self.history)
        if pattern:
            items = [e for e in items if fnmatch(e.kind, pattern)]
        return [e.as_dict() for e in items[-int(limit):]]

    def trace(self, correlation_id):
        with self.lock:
            return [e.as_dict() for e in self.history if e.correlation_id == correlation_id]

    def mailbox_depths(self):
        with self.lock:
            return {
                sub["name"]: len(self.mailboxes.get(token, []))
                for token, sub in self.subscriptions.items()
            }

    def snapshot(self):
        health = self.health()
        with self.lock:
            subscriptions = [
                {
                    "token": token,
                    "name": sub["name"],
                    "component": sub["component"],
                    "pattern": sub["pattern"],
                    "phases": sorted(sub["phases"]) if sub["phases"] else None,
                }
                for token, sub in self.subscriptions.items()
            ]
            return {
                "phase": self.phase,
                "metrics": dict(self.metrics),
                "components": self.component_health(),
                "subscriptions": subscriptions,
                "mailboxes": self.mailbox_depths(),
                "history_depth": len(self.history),
                "latest_events": self.latest(limit=24),
                "dead_letters": list(self.dead_letters[-16:]),
                "health": health,
            }
