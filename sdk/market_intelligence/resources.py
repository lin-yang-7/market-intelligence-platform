from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class Resource:
    def __init__(self, client) -> None:
        self.client = client


class MarketResource(Resource):
    def ticker(self, symbol: str, exchange: str | None = None) -> Any:
        return self.client.get("/v1/market/ticker", {"symbol": symbol, "exchange": exchange})

    def kline(self, symbol: str, interval: str = "1m", exchange: str | None = None) -> Any:
        return self.client.get(
            "/v1/market/kline",
            {"symbol": symbol, "interval": interval, "exchange": exchange},
        )

    def trades(self, symbol: str, exchange: str | None = None) -> Any:
        return self.client.get("/v1/market/trades", {"symbol": symbol, "exchange": exchange})


class FeatureResource(Resource):
    def list(self) -> Any:
        return self.client.get("/v1/feature/list")

    def meta(self, feature: str) -> Any:
        return self.client.get("/v1/feature/meta", {"feature": feature})

    def current(self, symbol: str, feature: str, exchange: str | None = None) -> Any:
        return self.client.get(
            "/v1/feature/current",
            {"symbol": symbol, "feature": feature, "exchange": exchange},
        )

    def batch(self, symbol: str, features: list[str], exchange: str | None = None) -> Any:
        return self.client.get(
            "/v1/feature/batch",
            {"symbol": symbol, "features": ",".join(features), "exchange": exchange},
        )

    def history(self, symbol: str, feature: str, limit: int = 100) -> Any:
        return self.client.get(
            "/v1/feature/history",
            {"symbol": symbol, "feature": feature, "limit": limit},
        )


class FeatureStoreResource(Resource):
    def catalog(self, category: str | None = None) -> Any:
        return self.client.get("/v1/feature-store/catalog", {"category": category})

    def register(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/feature-store/registry", payload)

    def meta(self, feature: str, version: str | None = None) -> Any:
        return self.client.get("/v1/feature-store/meta", {"feature": feature, "version": version})

    def write(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/feature-store/value", payload)

    def latest(self, symbol: str, feature: str, exchange: str | None = None) -> Any:
        return self.client.get(
            "/v1/feature-store/latest",
            {"symbol": symbol, "feature": feature, "exchange": exchange},
        )

    def history(self, symbol: str, feature: str, limit: int = 100) -> Any:
        return self.client.get(
            "/v1/feature-store/history",
            {"symbol": symbol, "feature": feature, "limit": limit},
        )

    def materialize(self, symbol: str, features: list[str], exchange: str | None = None) -> Any:
        return self.client.get(
            "/v1/feature-store/materialize",
            {"symbol": symbol, "features": ",".join(features), "exchange": exchange},
        )


class RankingResource(Resource):
    def overall(self, exchange: str | None = None, limit: int = 50) -> Any:
        return self.client.get("/v1/ranking/overall", {"exchange": exchange, "limit": limit})

    def long_inflow(self, exchange: str | None = None, limit: int = 50) -> Any:
        return self.client.get("/v1/ranking/longInflow", {"exchange": exchange, "limit": limit})

    def momentum(self, exchange: str | None = None, limit: int = 50) -> Any:
        return self.client.get("/v1/ranking/momentum", {"exchange": exchange, "limit": limit})

    def volume(self, exchange: str | None = None, limit: int = 50) -> Any:
        return self.client.get("/v1/ranking/volume", {"exchange": exchange, "limit": limit})


class ScreenerResource(Resource):
    def list(self) -> Any:
        return self.client.get("/v1/screener/list")

    def query(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/screener/query", payload)

    def long_inflow(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/screener/longInflow", payload)


class SignalResource(Resource):
    def current(self, symbol: str | None = None, signal_type: str | None = None) -> Any:
        return self.client.get("/v1/signal/current", {"symbol": symbol, "type": signal_type})

    def long_inflow(self, limit: int = 50) -> Any:
        return self.client.get("/v1/signal/longInflow", {"limit": limit})

    def detail(self, signal_id: str) -> Any:
        return self.client.get("/v1/signal/detail", {"signalId": signal_id})

    def history(self, symbol: str, signal_type: str | None = None, limit: int = 100) -> Any:
        return self.client.get(
            "/v1/signal/history",
            {"symbol": symbol, "type": signal_type, "limit": limit},
        )


class AlertResource(Resource):
    def create(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/alert/create", payload)

    def list(self) -> Any:
        return self.client.get("/v1/alert/list")

    def update(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/alert/update", payload)

    def history(self, symbol: str | None = None, limit: int = 100) -> Any:
        return self.client.get("/v1/alert/history", {"symbol": symbol, "limit": limit})


class HistoryResource(Resource):
    def snapshot(self, symbol: str, features: list[str] | None = None, limit: int = 100) -> Any:
        return self.client.get(
            "/v1/history/snapshot",
            {"symbol": symbol, "features": ",".join(features or []), "limit": limit},
        )

    def timeline(self, symbol: str, features: list[str] | None = None, limit: int = 100) -> Any:
        return self.client.get(
            "/v1/history/timeline",
            {"symbol": symbol, "features": ",".join(features or []), "limit": limit},
        )


class ScoreResource(Resource):
    def calculate(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/score/calculate", payload)

    def batch(self, items: list[Mapping[str, Any]]) -> Any:
        return self.client.post("/v1/score/batch", {"items": items})


class RuleResource(Resource):
    def create(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/rule/create", payload)

    def list(self, user_id: str | None = None, scope: str | None = None) -> Any:
        return self.client.get("/v1/rule/list", {"userId": user_id, "scope": scope})

    def update(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/rule/update", payload)

    def evaluate(self, payload: Mapping[str, Any]) -> Any:
        return self.client.post("/v1/rule/evaluate", payload)


class UserResource(Resource):
    def register(self, email: str, password: str, plan: str = "free") -> Any:
        return self.client.post(
            "/v1/user/register",
            {"email": email, "password": password, "plan": plan},
        )

    def login(self, email: str, password: str) -> Any:
        data = self.client.post("/v1/user/login", {"email": email, "password": password})
        access_token = data.get("accessToken")
        if access_token:
            self.client.set_access_token(access_token)
        return data

    def profile(self) -> Any:
        return self.client.get("/v1/user/profile")

    def logout(self) -> Any:
        data = self.client.post("/v1/user/logout", {})
        self.client.set_access_token("")
        return data

    def change_password(self, old_password: str, new_password: str) -> Any:
        return self.client.post(
            "/v1/user/password",
            {"oldPassword": old_password, "newPassword": new_password},
        )

    def plans(self) -> Any:
        return self.client.get("/v1/user/plans")

    def api_keys(self) -> Any:
        return self.client.get("/v1/user/api-keys")

    def create_api_key(self, name: str, scopes: list[str]) -> Any:
        return self.client.post("/v1/user/api-keys", {"name": name, "scopes": scopes})

    def usage(self) -> Any:
        return self.client.get("/v1/user/usage")
