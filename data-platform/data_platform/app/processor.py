from typing import Any

from .quality import DataQualityChecker
from .router import ClickHouseRoutePlanner
from .schemas import (
    DataQualityReportResponse,
    PipelineEvent,
    ProcessedEvent,
    QualityReport,
    RoutePlan,
)


class PipelineProcessor:
    def __init__(
        self,
        quality_checker: DataQualityChecker | None = None,
        route_planner: ClickHouseRoutePlanner | None = None,
    ) -> None:
        self.quality_checker = quality_checker or DataQualityChecker()
        self.route_planner = route_planner or ClickHouseRoutePlanner()

    def validate(self, event: PipelineEvent) -> QualityReport:
        return self.quality_checker.check(event)

    def quality_report(self, events: list[PipelineEvent]) -> DataQualityReportResponse:
        return self.quality_checker.report(events)

    def route(self, event: PipelineEvent) -> RoutePlan:
        return self.route_planner.plan(event)

    def process(self, event: PipelineEvent) -> ProcessedEvent:
        quality = self.validate(event)
        route = (
            self.route(event)
            if quality.accepted
            else self.route_planner.dead_letter(event, quality.issues[0].code)
        )
        return ProcessedEvent(
            event=event,
            quality=quality,
            route=route,
            normalized_data=self._normalize(event.data),
        )

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if "symbol" in normalized:
            normalized["symbol"] = str(normalized["symbol"]).upper()
        if "exchange" in normalized:
            normalized["exchange"] = str(normalized["exchange"]).lower()
        return normalized


pipeline_processor = PipelineProcessor()
