import hashlib
import operator
import re
from collections.abc import Callable
from typing import Any

from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError, now_ms
from services.notification_service.app.schemas import NotificationMessage, NotificationSendRequest
from services.notification_service.app.services import NotificationService
from services.signal_service.app.schemas import Signal

from .repositories import AlertRepository
from .schemas import (
    AlertCreateRequest,
    AlertCreateResponse,
    AlertHistoryItem,
    AlertRule,
    AlertUpdateRequest,
)

SUPPORTED_ALERT_TYPES = {"longInflow", "price", "feature", "ranking", "signal"}
SUPPORTED_CHANNELS = {"sse", "websocket"}
CONDITION_PATTERN = re.compile(r"^(>=|<=|>|<|==)\s*(-?\d+(?:\.\d+)?)$")
OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


class AlertService:
    def __init__(
        self,
        repository: AlertRepository,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.repository = repository
        self.notification_service = notification_service

    async def create_rule(self, request: AlertCreateRequest) -> AlertCreateResponse:
        self._validate_type(request.type)
        self._validate_channel(request.channel)
        self._validate_conditions(request.conditions)
        timestamp = now_ms()
        rule = AlertRule(
            alertId=self._id(
                "alert",
                request.userId,
                request.type,
                request.symbol or "*",
                timestamp,
            ),
            userId=request.userId,
            type=request.type,
            symbol=request.symbol.upper() if request.symbol else None,
            conditions=request.conditions,
            channel=request.channel,
            createdAt=timestamp,
            updatedAt=timestamp,
        )
        await self.repository.save_rule(rule)
        return AlertCreateResponse(alertId=rule.alertId, status=rule.status)

    async def create_long_inflow_rule(
        self,
        conditions: dict[str, Any],
        symbol: str | None = None,
        channel: str = "sse",
        user_id: str = "default",
    ) -> AlertCreateResponse:
        return await self.create_rule(
            AlertCreateRequest(
                type="longInflow",
                symbol=symbol,
                conditions=conditions,
                channel=channel,
                userId=user_id,
            )
        )

    async def create_signal_rule(
        self,
        signal_type: str,
        min_score: float,
        channel: str = "sse",
        user_id: str = "default",
    ) -> AlertCreateResponse:
        return await self.create_rule(
            AlertCreateRequest(
                type="signal",
                conditions={"signalType": signal_type, "score": f">={min_score}"},
                channel=channel,
                userId=user_id,
            )
        )

    async def list_rules(self, user_id: str | None = None) -> list[AlertRule]:
        return await self.repository.list_rules(user_id)

    async def update_rule(self, request: AlertUpdateRequest) -> AlertRule:
        rule = await self.repository.get_rule(request.alertId)
        if rule is None:
            raise ServiceError(7001, "Alert not found")
        conditions = request.conditions if request.conditions is not None else rule.conditions
        channel = request.channel if request.channel is not None else rule.channel
        self._validate_conditions(conditions)
        self._validate_channel(channel)
        updated = model_copy_with_update(
            rule,
            {
                "conditions": conditions,
                "channel": channel,
                "enabled": rule.enabled if request.enabled is None else request.enabled,
                "status": self._status(rule.status, request.enabled),
                "updatedAt": now_ms(),
            },
        )
        await self.repository.save_rule(updated)
        return updated

    async def delete_rule(self, alert_id: str) -> dict[str, str]:
        deleted = await self.repository.delete_rule(alert_id)
        if not deleted:
            raise ServiceError(7001, "Alert not found")
        return {"alertId": alert_id, "status": "deleted"}

    async def evaluate_signal(self, signal: Signal) -> list[AlertHistoryItem]:
        rules = await self.repository.list_rules()
        triggered: list[AlertHistoryItem] = []
        for rule in rules:
            if not rule.enabled:
                continue
            if rule.type not in {"longInflow", "signal"}:
                continue
            if rule.symbol and rule.symbol != signal.symbol:
                continue
            if rule.type == "longInflow" and signal.type != "longInflow":
                continue
            if not self._matches_conditions(rule.conditions, signal):
                continue
            history = self._history_item(rule, signal)
            delivery = await self._send_notification(rule, signal)
            if delivery is not None:
                history = model_copy_with_update(
                    history,
                    {
                        "result": delivery.status,
                        "reason": delivery.error or history.reason,
                    },
                )
            await self.repository.save_history(history)
            triggered.append(history)
        return triggered

    async def _send_notification(
        self,
        rule: AlertRule,
        signal: Signal,
    ):
        if self.notification_service is None:
            return None
        return await self.notification_service.send(
            NotificationSendRequest(
                channel=rule.channel,
                userId=rule.userId,
                dedupeKey=f"alert:{rule.alertId}:signal:{signal.signalId}",
                message=NotificationMessage(
                    title=f"{signal.symbol} {signal.type} signal",
                    body=signal.explanation,
                    severity="warning",
                    metadata={
                        "alertId": rule.alertId,
                        "signalId": signal.signalId,
                        "symbol": signal.symbol,
                        "score": signal.score,
                    },
                ),
            )
        )

    async def history(self, symbol: str | None = None, limit: int = 100) -> list[AlertHistoryItem]:
        return await self.repository.list_history(symbol, limit)

    def _matches_conditions(self, conditions: dict[str, Any], signal: Signal) -> bool:
        for key, expected in conditions.items():
            if key == "signalType" and expected != signal.type:
                return False
            if key in {"score", "confidence"}:
                actual = signal.score if key == "score" else signal.confidence
                if not self._compare(actual, str(expected)):
                    return False
        return True

    def _validate_type(self, alert_type: str) -> None:
        if alert_type not in SUPPORTED_ALERT_TYPES:
            raise ServiceError(7002, "Invalid condition")

    def _validate_channel(self, channel: str) -> None:
        if channel not in SUPPORTED_CHANNELS:
            raise ServiceError(7002, "Invalid condition")

    def _validate_conditions(self, conditions: dict[str, Any]) -> None:
        for key, value in conditions.items():
            if key in {"score", "confidence"}:
                self._parse_condition(str(value))

    def _compare(self, actual: float, condition: str) -> bool:
        op, expected = self._parse_condition(condition)
        return OPERATORS[op](actual, expected)

    def _parse_condition(self, condition: str) -> tuple[str, float]:
        match = CONDITION_PATTERN.match(condition.strip())
        if match is None:
            raise ServiceError(7002, "Invalid condition")
        return match.group(1), float(match.group(2))

    def _history_item(self, rule: AlertRule, signal: Signal) -> AlertHistoryItem:
        timestamp = now_ms()
        return AlertHistoryItem(
            historyId=self._id("hist", rule.alertId, signal.signalId or "", timestamp),
            alertId=rule.alertId,
            symbol=signal.symbol,
            type=rule.type,
            channel=rule.channel,
            triggerTime=timestamp,
            result="success",
            signalId=signal.signalId,
            reason=f"matched {rule.type} alert rule",
        )

    @staticmethod
    def _status(current: str, enabled: bool | None) -> str:
        if enabled is None:
            return current
        return "active" if enabled else "disabled"

    @staticmethod
    def _id(prefix: str, *parts: object) -> str:
        raw = ":".join(str(part) for part in parts).encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"{prefix}_{digest}"
