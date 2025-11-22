from datetime import datetime, timezone
from uuid import uuid4


def test_seed_build_records_is_pure_and_non_empty():
    from scripts.seed import build_seed_records

    tenant_id = uuid4()
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    records = build_seed_records(tenant_id, now)

    assert "demographics" in records
    assert "spending" in records
    assert "labour_stats" in records
    assert "business_density" in records
    assert "report_jobs" in records
    assert len(records["demographics"]) > 0
    assert len(records["report_jobs"]) == 2
