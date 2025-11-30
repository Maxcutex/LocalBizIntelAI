from sqlalchemy.orm import Session

from jobs.embedding_worker import EmbeddingWorker


def test_embedding_worker_dispatches_rebuild_embeddings() -> None:
    calls: list[dict] = []

    class FakeJob:
        def run(
            self,
            *,
            db_session: Session,
            country: str | None,
            city: str | None,
            regions: list[str] | None,
            options: dict,
        ):
            _ = db_session
            calls.append(
                {
                    "country": country,
                    "city": city,
                    "regions": regions,
                    "options": options,
                }
            )

            class Result:
                def __init__(self) -> None:
                    self.status = "COMPLETED"
                    self.row_count = 1

            return Result()

    worker = EmbeddingWorker(handlers_by_job_name={"rebuild-embeddings": FakeJob()})
    result = worker.consume(
        db_session=None,  # type: ignore[arg-type]
        payload={
            "job_name": "rebuild-embeddings",
            "country": "GH",
            "city": "Accra",
            "regions": ["accra-central"],
            "options": {"mode": "partial"},
        },
    )

    assert result["status"] == "COMPLETED"
    assert calls == [
        {
            "country": "GH",
            "city": "Accra",
            "regions": ["accra-central"],
            "options": {"mode": "partial"},
        }
    ]
