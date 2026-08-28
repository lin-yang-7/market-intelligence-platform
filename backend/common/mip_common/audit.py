from dataclasses import dataclass, field

from .responses import now_ms


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    resource: str
    result: str
    timestamp: int = field(default_factory=now_ms)
    metadata: dict[str, str] = field(default_factory=dict)


class InMemoryAuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self, actor: str | None = None, limit: int = 100) -> list[AuditEvent]:
        events = self._events
        if actor:
            events = [event for event in events if event.actor == actor]
        events = sorted(events, key=lambda event: event.timestamp, reverse=True)
        return events[: max(1, min(limit, 1000))]


audit_log = InMemoryAuditLog()


def record_audit(
    actor: str,
    action: str,
    resource: str,
    result: str = "success",
    metadata: dict[str, str] | None = None,
) -> None:
    audit_log.record(
        AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            metadata=metadata or {},
        )
    )
