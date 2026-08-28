import json
from pathlib import Path

REQUIRED_ENDPOINTS = {
    "/v1/data/validate",
    "/v1/data/quality/report",
    "/v1/data/stream/process",
    "/v1/data/batch/run",
    "/v1/data/warehouse/plan",
    "/v1/data/lake/write",
    "/v1/data/freshness/report",
    "/v1/data/governance/lineage",
    "/v1/data/route",
    "/v1/data/process",
    "/v1/data/store",
    "/v1/data/ingest",
    "/v1/data/ranking-monitor/events",
}

REQUIRED_FILES = {
    "data-platform/data_platform/app/jobs.py",
    "data-platform/data_platform/app/quality.py",
    "data-platform/data_platform/app/processor.py",
    "data-platform/data_platform/app/router.py",
    "data-platform/data_platform/app/storage.py",
    "backend/tests/test_data_platform_full_jobs.py",
    "backend/tests/test_data_platform_quality_report.py",
    "docs/generated/DATA-PLATFORM-FULL-MVP.md",
    "docs/generated/DATA-QUALITY-REPORT-API-MVP.md",
}

REQUIRED_CHECKLIST_MARKERS = {
    "Flink or stream processing jobs MVP",
    "Batch pipeline MVP",
    "Data warehouse layers MVP",
    "Data lake MVP",
    "Data quality report API MVP",
    "Data delay and event loss monitoring MVP",
    "Data lineage and governance MVP",
}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    openapi_path = root / "docs/generated/openapi/data-platform.openapi.json"
    if not openapi_path.is_file():
        errors.append("missing generated Data Platform OpenAPI schema")
    else:
        schema = json.loads(openapi_path.read_text(encoding="utf-8"))
        paths = set(schema.get("paths", {}))
        for endpoint in sorted(REQUIRED_ENDPOINTS - paths):
            errors.append(f"missing Data Platform OpenAPI endpoint: {endpoint}")

    checklist = (root / "docs/IMPLEMENTATION-GAP-CHECKLIST.md").read_text(encoding="utf-8")
    for marker in sorted(REQUIRED_CHECKLIST_MARKERS):
        if f"[x] {marker}" not in checklist:
            errors.append(f"missing checked checklist marker: {marker}")

    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    if "data_lake/" not in gitignore:
        errors.append("data_lake runtime directory is not ignored")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("ok: Data Platform full MVP contract is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
