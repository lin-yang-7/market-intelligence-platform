from scripts.backup_retention_plan import POLICIES, backup_targets, render_plan


def test_backup_targets_include_business_and_history_tables() -> None:
    targets = backup_targets()

    assert "mysql:users" in targets
    assert "mysql:invoices" in targets
    assert "clickhouse:prediction_history" in targets
    assert "clickhouse:ranking_history" in targets


def test_retention_policies_are_monotonic() -> None:
    for policy in POLICIES:
        assert policy.hot_days < policy.cold_days < policy.delete_after_days


def test_render_plan_contains_safety_note() -> None:
    plan = render_plan()

    assert "This MVP plan is declarative and does not delete data." in plan
    assert "Destructive retention jobs must run with audited dry-run output first." in plan
