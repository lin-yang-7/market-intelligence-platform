from fastapi.testclient import TestClient
from services.rule_service.app.dependencies import get_rule_service
from services.rule_service.app.main import app
from services.rule_service.app.repositories import InMemoryRuleRepository
from services.rule_service.app.services import RuleService


def test_rule_create_list_evaluate_update_and_delete() -> None:
    service = RuleService(InMemoryRuleRepository())
    app.dependency_overrides[get_rule_service] = lambda: service
    client = TestClient(app)
    try:
        create_response = client.post(
            "/v1/rule/create",
            json={
                "name": "Strong long inflow",
                "scope": "signal",
                "target": "BTCUSDT",
                "conditions": {"type": "longInflow", "score": ">=90"},
                "action": "notify",
                "userId": "usr_demo",
            },
            headers={"X-Request-ID": "rule-create"},
        )
        rule_id = create_response.json()["data"]["ruleId"]
        list_response = client.get("/v1/rule/list", params={"userId": "usr_demo"})
        evaluate_response = client.post(
            "/v1/rule/evaluate",
            json={
                "scope": "signal",
                "target": "BTCUSDT",
                "userId": "usr_demo",
                "payload": {"type": "longInflow", "score": 94},
            },
        )
        update_response = client.post(
            "/v1/rule/update",
            json={"ruleId": rule_id, "enabled": False},
        )
        delete_response = client.delete(f"/v1/rule/{rule_id}")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert create_response.json()["requestId"] == "rule-create"
    assert list_response.json()["data"][0]["ruleId"] == rule_id
    assert evaluate_response.json()["data"][0]["ruleId"] == rule_id
    assert evaluate_response.json()["data"][0]["reason"] == "all conditions matched"
    assert update_response.json()["data"]["status"] == "disabled"
    assert delete_response.json()["data"] == {"ruleId": rule_id, "status": "deleted"}


def test_rule_invalid_condition_returns_error() -> None:
    service = RuleService(InMemoryRuleRepository())
    app.dependency_overrides[get_rule_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/v1/rule/create",
            json={
                "name": "Bad",
                "scope": "signal",
                "conditions": {"score": "=>90"},
                "action": "notify",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["code"] == 7104


def test_rule_evaluate_skips_non_matching_payload() -> None:
    service = RuleService(InMemoryRuleRepository())
    app.dependency_overrides[get_rule_service] = lambda: service
    client = TestClient(app)
    try:
        client.post(
            "/v1/rule/create",
            json={
                "name": "Momentum",
                "scope": "signal",
                "conditions": {"type": "momentum", "score": ">=80"},
                "action": "tag",
            },
        )
        response = client.post(
            "/v1/rule/evaluate",
            json={
                "scope": "signal",
                "payload": {"type": "longInflow", "score": 90},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"] == []
