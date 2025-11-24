"""Business density ETL job using OpenStreetMap (Overpass API).

This provides the first real ingestion pipeline end-to-end for the
"business_density" dataset.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx

from api.config import Settings, get_settings
from models.system import ETLLog
from repositories.business_density_repository import BusinessDensityRepository
from repositories.data_freshness_repository import DataFreshnessRepository


class EtlDbSession(Protocol):
    """Minimal DB session interface needed by ETL jobs."""

    def add(self, obj: Any) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError


class BusinessDensityRepositoryProtocol(Protocol):
    """Abstraction for business density persistence."""

    def upsert_many(
        self,
        db_session: Any,
        rows: list[dict[str, Any]],
        last_updated: datetime,
    ) -> int:
        raise NotImplementedError


class DataFreshnessRepositoryProtocol(Protocol):
    """Abstraction for data freshness persistence."""

    def upsert_status(
        self,
        *,
        db_session: Any,
        dataset_name: str,
        last_run: datetime,
        row_count: int,
        status: str,
    ) -> Any:
        raise NotImplementedError


logger = logging.getLogger(__name__)


class BusinessDensitySourceClient(Protocol):
    """Interface for fetching raw business density rows from a provider."""

    def fetch_business_density(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        """Fetch raw business density rows for ingestion."""
        raise NotImplementedError


class OverpassBusinessDensitySourceClient(BusinessDensitySourceClient):
    """Fetch business counts for a city using Overpass API."""

    def __init__(
        self,
        *,
        overpass_endpoint: str,
        http_client: httpx.Client,
    ) -> None:
        self._overpass_endpoint = overpass_endpoint
        self._http_client = http_client

    @classmethod
    def create_default(
        cls, *, settings: Settings
    ) -> "OverpassBusinessDensitySourceClient":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        http_client = httpx.Client(
            timeout=httpx.Timeout(settings.osm_overpass_timeout_s),
            headers={"User-Agent": settings.osm_overpass_user_agent},
        )
        return cls(
            overpass_endpoint=settings.osm_overpass_endpoint,
            http_client=http_client,
        )

    def fetch_business_density(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        if not city:
            raise ValueError("city is required for OSM business density ingestion")

        resolved_country = country or settings.osm_default_country
        business_type_specs = self._resolve_business_types(options, settings)
        city_geo_id = self._build_city_geo_id(city, settings)
        rows: list[dict[str, Any]] = []

        for business_type, spec in business_type_specs.items():
            query = self._build_overpass_query(city=city, spec=spec, settings=settings)
            response = self._http_client.post(
                self._overpass_endpoint,
                content=query,
            )
            response.raise_for_status()
            payload = response.json()
            elements = payload.get("elements", [])
            coordinates = self._extract_coordinates(elements, settings)

            rows.append(
                {
                    "geo_id": city_geo_id,
                    "country": resolved_country,
                    "city": city,
                    "business_type": business_type,
                    "count": len(elements),
                    "density_score": None,
                    "coordinates": coordinates or None,
                }
            )

        return rows

    def _resolve_business_types(
        self, options: dict[str, Any], settings: Settings
    ) -> dict[str, dict[str, str]]:
        user_specs = options.get("business_types")
        if isinstance(user_specs, dict):
            resolved_from_options: dict[str, dict[str, str]] = {}
            for name, spec in user_specs.items():
                if (
                    isinstance(name, str)
                    and isinstance(spec, dict)
                    and isinstance(spec.get("tag_key"), str)
                    and isinstance(spec.get("tag_value"), str)
                ):
                    resolved_from_options[name] = {
                        "tag_key": spec["tag_key"],
                        "tag_value": spec["tag_value"],
                    }
            if resolved_from_options:
                return resolved_from_options

        return settings.osm_business_type_specs

    def _build_city_geo_id(self, city: str, settings: Settings) -> str:
        normalized = city.lower().strip().replace(" ", "-")
        return f"{normalized}-{settings.osm_city_geo_id_suffix}"

    def _build_overpass_query(
        self, *, city: str, spec: dict[str, str], settings: Settings
    ) -> str:
        tag_key = spec["tag_key"]
        tag_value = spec["tag_value"]
        escaped_city = city.replace('"', '\\"')
        return f"""
        [out:json][timeout:{settings.osm_overpass_query_timeout_s}];
        area["name"="{escaped_city}"]["boundary"="administrative"]->.searchArea;
        (
          node["{tag_key}"="{tag_value}"](area.searchArea);
          way["{tag_key}"="{tag_value}"](area.searchArea);
          relation["{tag_key}"="{tag_value}"](area.searchArea);
        );
        out center;
        """

    def _extract_coordinates(
        self, elements: list[dict[str, Any]], settings: Settings
    ) -> list[dict[str, Any]]:
        coordinates: list[dict[str, Any]] = []
        for element in elements:
            lat = element.get("lat")
            lon = element.get("lon")
            if lat is None or lon is None:
                center = element.get("center")
                if isinstance(center, dict):
                    lat = center.get("lat")
                    lon = center.get("lon")
            if lat is None or lon is None:
                continue
            coordinates.append(
                {
                    "id": element.get("id"),
                    "lat": lat,
                    "lon": lon,
                    "type": element.get("type"),
                }
            )
            if len(coordinates) >= settings.osm_max_coordinate_samples:
                break
        return coordinates


def ingest_osm_business_density(
    *,
    country: str | None,
    city: str,
    options: dict[str, Any],
    source_client: BusinessDensitySourceClient,
    settings: Settings,
) -> list[dict[str, Any]]:
    """Fetch OSM business density rows for a single city."""
    return source_client.fetch_business_density(
        country=country,
        city=city,
        options=options,
        settings=settings,
    )


@dataclass
class BusinessDensityEtlResult:
    """Result summary for a business density ETL run."""

    dataset_name: str
    status: str
    row_count: int
    country: str | None
    city: str | None


class BusinessDensityEtlJob:
    """ETL job that loads business density rows into the database."""

    def __init__(
        self,
        *,
        business_density_repository: BusinessDensityRepositoryProtocol,
        data_freshness_repository: DataFreshnessRepositoryProtocol,
        source_client: BusinessDensitySourceClient,
        settings: Settings,
    ) -> None:
        self._business_density_repository = business_density_repository
        self._data_freshness_repository = data_freshness_repository
        self._source_client = source_client
        self._settings = settings

    @classmethod
    def create_default(cls) -> "BusinessDensityEtlJob":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        settings = get_settings()
        source_client = OverpassBusinessDensitySourceClient.create_default(
            settings=settings
        )
        return cls(
            business_density_repository=BusinessDensityRepository(),
            data_freshness_repository=DataFreshnessRepository(),
            source_client=source_client,
            settings=settings,
        )

    def run(
        self,
        *,
        db_session: EtlDbSession,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
    ) -> BusinessDensityEtlResult:
        """
        Execute one business density ETL run.

        Fetches raw rows from Overpass, upserts them, updates freshness,
        and records an `ETLLog`.
        """
        dataset_name = "business_density"
        now = datetime.now(timezone.utc)
        resolved_options = options

        try:
            logger.info(
                "Starting ETL run",
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "job": dataset_name,
                },
            )
            raw_rows = self._source_client.fetch_business_density(
                country=country,
                city=city,
                options=resolved_options,
                settings=self._settings,
            )

            affected_rows = self._business_density_repository.upsert_many(
                db_session, raw_rows, last_updated=now
            )

            self._data_freshness_repository.upsert_status(
                db_session=db_session,
                dataset_name=dataset_name,
                last_run=now,
                row_count=affected_rows,
                status="COMPLETED",
            )

            db_session.add(
                ETLLog(
                    job_name=dataset_name,
                    payload={
                        "country": country,
                        "city": city,
                        "options": resolved_options,
                    },
                    status="COMPLETED",
                    created_at=now.isoformat(),
                )
            )

            db_session.flush()
            logger.info(
                "ETL run completed",
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "row_count": affected_rows,
                    "status": "COMPLETED",
                },
            )
            return BusinessDensityEtlResult(
                dataset_name=dataset_name,
                status="COMPLETED",
                row_count=affected_rows,
                country=country,
                city=city,
            )
        except Exception:
            logger.error(
                "ETL run failed",
                exc_info=True,
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "status": "FAILED",
                },
            )
            self._data_freshness_repository.upsert_status(
                db_session=db_session,
                dataset_name=dataset_name,
                last_run=now,
                row_count=0,
                status="FAILED",
            )

            db_session.add(
                ETLLog(
                    job_name=dataset_name,
                    payload={
                        "country": country,
                        "city": city,
                        "options": resolved_options,
                    },
                    status="FAILED",
                    created_at=now.isoformat(),
                )
            )
            db_session.flush()
            raise
