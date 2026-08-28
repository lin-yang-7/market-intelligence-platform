from collections.abc import Iterable

from mip_common.responses import now_ms

from .schemas import (
    DataQualityReportBucket,
    DataQualityReportResponse,
    PipelineEvent,
    QualityIssue,
    QualityReport,
)

REQUIRED_FIELDS_BY_EVENT_TYPE = {
    "market.ticker": {"symbol", "price"},
    "market.kline": {"symbol", "open", "high", "low", "close", "volume"},
    "market.trade": {"symbol", "price", "quantity"},
    "market.funding": {"symbol", "fundingRate"},
    "market.open_interest": {"symbol", "openInterest"},
    "market.liquidation": {"symbol", "side", "price", "quantity", "value"},
    "feature.updated": {"symbol", "feature", "value"},
    "ranking.entered": {"symbol", "rankingType"},
    "ranking.exited": {"symbol", "rankingType"},
    "ranking.moved": {"symbol", "rankingType"},
    "ranking.strategy": {"event", "rankingType"},
    "signal.created": {"symbol", "type", "score", "confidence"},
}


class DataQualityChecker:
    def check(self, event: PipelineEvent) -> QualityReport:
        issues: list[QualityIssue] = []
        required = REQUIRED_FIELDS_BY_EVENT_TYPE.get(event.event_type, set())
        missing = sorted(field for field in required if field not in event.data)

        for field in missing:
            issues.append(
                QualityIssue(
                    code="missing_field",
                    severity="error",
                    message=f"Missing required field: {field}",
                )
            )

        self._check_price(event, issues)
        self._check_timestamp(event, issues)

        missing_rate = len(missing) / max(1, len(required))
        delay_ms = max(0, now_ms() - event.timestamp)
        accepted = not any(issue.severity == "error" for issue in issues)
        return QualityReport(
            accepted=accepted,
            issue_count=len(issues),
            issues=issues,
            missing_rate=round(missing_rate, 4),
            delay_ms=delay_ms,
        )

    def report(self, events: list[PipelineEvent]) -> DataQualityReportResponse:
        checked = [(event, self.check(event)) for event in events]
        buckets: list[DataQualityReportBucket] = []
        for event_type in sorted({event.event_type for event, _report in checked}):
            reports = [report for event, report in checked if event.event_type == event_type]
            buckets.append(
                DataQualityReportBucket(
                    eventType=event_type,
                    totalEvents=len(reports),
                    acceptedEvents=sum(1 for report in reports if report.accepted),
                    rejectedEvents=sum(1 for report in reports if not report.accepted),
                    warningEvents=sum(
                        1
                        for report in reports
                        if any(issue.severity == "warning" for issue in report.issues)
                    ),
                    errorEvents=sum(
                        1
                        for report in reports
                        if any(issue.severity == "error" for issue in report.issues)
                    ),
                    avgMissingRate=_avg_float(report.missing_rate for report in reports),
                    avgDelayMs=_avg_int(report.delay_ms for report in reports),
                    maxDelayMs=max((report.delay_ms for report in reports), default=0),
                )
            )

        reports = [report for _event, report in checked]
        return DataQualityReportResponse(
            totalEvents=len(reports),
            acceptedEvents=sum(1 for report in reports if report.accepted),
            rejectedEvents=sum(1 for report in reports if not report.accepted),
            warningEvents=sum(
                1
                for report in reports
                if any(issue.severity == "warning" for issue in report.issues)
            ),
            errorEvents=sum(
                1 for report in reports if any(issue.severity == "error" for issue in report.issues)
            ),
            avgMissingRate=_avg_float(report.missing_rate for report in reports),
            avgDelayMs=_avg_int(report.delay_ms for report in reports),
            maxDelayMs=max((report.delay_ms for report in reports), default=0),
            buckets=buckets,
        )

    def _check_price(self, event: PipelineEvent, issues: list[QualityIssue]) -> None:
        price = event.data.get("price")
        if price is not None and float(price) <= 0:
            issues.append(
                QualityIssue(
                    code="invalid_price",
                    severity="error",
                    message="Price must be greater than zero.",
                )
            )

    def _check_timestamp(self, event: PipelineEvent, issues: list[QualityIssue]) -> None:
        delay_ms = now_ms() - event.timestamp
        if delay_ms < -60_000:
            issues.append(
                QualityIssue(
                    code="future_timestamp",
                    severity="error",
                    message="Event timestamp is too far in the future.",
                )
            )
        elif delay_ms > 300_000:
            issues.append(
                QualityIssue(
                    code="data_delay",
                    severity="warning",
                    message="Event is delayed by more than five minutes.",
                )
            )


def _avg_float(values: Iterable[float]) -> float:
    items = list(values)
    return round(sum(items) / len(items), 4) if items else 0.0


def _avg_int(values: Iterable[int]) -> int:
    items = list(values)
    return round(sum(items) / len(items)) if items else 0
