from typing import Protocol

from .schemas import AlertHistoryItem, AlertRule


class AlertRepository(Protocol):
    async def save_rule(self, rule: AlertRule) -> None:
        ...

    async def get_rule(self, alert_id: str) -> AlertRule | None:
        ...

    async def list_rules(self, user_id: str | None = None) -> list[AlertRule]:
        ...

    async def delete_rule(self, alert_id: str) -> bool:
        ...

    async def save_history(self, history: AlertHistoryItem) -> None:
        ...

    async def list_history(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[AlertHistoryItem]:
        ...


class InMemoryAlertRepository:
    def __init__(self) -> None:
        self._rules: dict[str, AlertRule] = {}
        self._history: dict[str, AlertHistoryItem] = {}

    async def save_rule(self, rule: AlertRule) -> None:
        self._rules[rule.alertId] = rule

    async def get_rule(self, alert_id: str) -> AlertRule | None:
        return self._rules.get(alert_id)

    async def list_rules(self, user_id: str | None = None) -> list[AlertRule]:
        rules = list(self._rules.values())
        if user_id:
            rules = [rule for rule in rules if rule.userId == user_id]
        rules.sort(key=lambda rule: rule.createdAt, reverse=True)
        return rules

    async def delete_rule(self, alert_id: str) -> bool:
        return self._rules.pop(alert_id, None) is not None

    async def save_history(self, history: AlertHistoryItem) -> None:
        self._history[history.historyId] = history

    async def list_history(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[AlertHistoryItem]:
        history = list(self._history.values())
        if symbol:
            history = [item for item in history if item.symbol == symbol.upper()]
        history.sort(key=lambda item: item.triggerTime, reverse=True)
        return history[: max(1, min(limit, 1000))]

