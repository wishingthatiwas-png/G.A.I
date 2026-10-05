from __future__ import annotations

from .nervous import Event, NervousSystem


class Cell:
    """Standard lifecycle contract for every G.A.I. nervous-system subsystem."""

    def __init__(self, name, nervous: NervousSystem, version="0.1.0",
                 sleep_phases=None, critical=False):
        self.name = name
        self.nervous = nervous
        self.version = version
        self.sleep_phases = set(sleep_phases or {"awake"})
        self.critical = bool(critical)
        self.bindings = []
        self.started = False
        self.state = "stopped"

    def start(self):
        if self.started:
            return self
        self.nervous.register_component(
            self.name, kind="cell", version=self.version,
            sleep_capable=True, critical=self.critical,
        )
        new_bindings = []
        for binding in self.bindings:
            pattern, handler, *rest = binding
            phases = rest[0] if rest else self.sleep_phases
            token = self.nervous.subscribe(
                pattern, handler, name=f"{self.name}.{pattern}",
                component=self.name, phases=phases,
            )
            new_bindings.append((pattern, handler, phases, token))
        self.bindings = new_bindings
        self.started = True
        self.state = "running"
        self.heartbeat()
        return self

    def listen(self, pattern, handler=None, phases=None):
        handler = handler or self.on_event
        allowed = set(phases) if phases else set(self.sleep_phases)
        binding = (pattern, handler, allowed)
        self.bindings.append(binding)
        if self.started:
            token = self.nervous.subscribe(
                pattern, handler, name=f"{self.name}.{pattern}",
                component=self.name, phases=allowed,
            )
            self.bindings[-1] = (pattern, handler, allowed, token)
        return handler

    def on_event(self, event: Event):
        raise NotImplementedError(f"{self.name} has no event handler")

    def heartbeat(self, detail=None):
        self.nervous.heartbeat(self.name, self.state, detail)

    def sleep(self):
        if not self.started:
            return
        self.state = "sleeping"
        self.heartbeat()

    def wake(self):
        if not self.started:
            return
        self.state = "running"
        self.heartbeat()

    def publish(self, kind, payload=None, **kwargs):
        return self.nervous.publish(kind, payload, source=self.name, **kwargs)

    def request(self, kind, payload=None, target=None, **kwargs):
        return self.nervous.request(
            kind, payload, source=self.name, target=target, **kwargs
        )

    def reply(self, request_event, kind, payload=None, **kwargs):
        return self.nervous.reply(
            request_event, kind, payload, source=self.name, **kwargs
        )

    def stop(self):
        if not self.started:
            return
        for binding in self.bindings:
            if len(binding) == 4:
                self.nervous.unsubscribe(binding[3])
        self.started = False
        self.state = "stopped"
        self.heartbeat()
