from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests


class ADEMEDPEIngester:
    """Ingest public rows from an ADEME Data Fair dataset."""

    def __init__(
        self,
        dataset_id: str = "dpe-france",
        base_url: str = "https://data.ademe.fr/data-fair/api/v1/datasets",
        timeout: float = 30,
    ) -> None:
        self.dataset_id = dataset_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "data-gouv-ingestion/0.1",
        })

    def metadata(self) -> dict[str, Any]:
        url = f"{self.base_url}/{self.dataset_id}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object from ADEME")
        return payload

    def iter_records(
        self,
        search: str | None = None,
        size: int = 100,
        fields: list[str] | None = None,
        max_records: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        url = f"{self.base_url}/{self.dataset_id}/lines"
        params: dict[str, str | int] = {"size": size}
        if search:
            params["q"] = search
        if fields:
            params["select"] = ",".join(fields)

        fetched = 0
        while url:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results", [])
            if not isinstance(results, list):
                raise ValueError("The ADEME response field 'results' must be a list")

            for record in results:
                if not isinstance(record, dict):
                    continue
                yield record
                fetched += 1
                if max_records is not None and fetched >= max_records:
                    return

            url = payload.get("next")
            params = {}
