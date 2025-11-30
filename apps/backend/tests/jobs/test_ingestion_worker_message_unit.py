from jobs.ingestion_worker import IngestionMessage


def test_ingestion_message_uses_dataset_when_present() -> None:
    msg = IngestionMessage.from_payload(
        {"job_name": "census-demographics-refresh", "dataset": "demographics"}
    )
    assert msg.dataset == "demographics"
    assert msg.job_name == "census-demographics-refresh"


def test_ingestion_message_falls_back_to_job_name_when_dataset_missing() -> None:
    msg = IngestionMessage.from_payload({"job_name": "labour-stats-refresh"})
    assert msg.dataset == "labour-stats-refresh"
    assert msg.job_name == "labour-stats-refresh"
