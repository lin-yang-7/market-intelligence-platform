from mip_common.audit import AuditEvent, InMemoryAuditLog


def test_audit_log_records_and_lists_events() -> None:
    log = InMemoryAuditLog()
    log.record(AuditEvent(actor="usr_1", action="login", resource="user", result="success"))
    log.record(AuditEvent(actor="usr_2", action="login", resource="user", result="success"))

    assert len(log.list_events()) == 2
    assert log.list_events(actor="usr_1")[0].actor == "usr_1"
