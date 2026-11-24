from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import requests


class DataserviceIngester:
    """Fetch every page of data.gouv.fr dataservices and persist it locally."""

    def __init__(
        self,
        base_url: str = "https://www.data.gouv.fr/api/1/dataservices/",
        page_size: int = 100,
        timeout: float = 30,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url
        self.page_size = page_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "data-gouv-ingestion/0.1",
        })

    def _get(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object from the dataservices API")
                return payload
            except (requests.RequestException, ValueError) as error:
                last_error = error
                if attempt + 1 < self.max_retries:
                    time.sleep(2**attempt)
        raise RuntimeError(f"Failed to fetch {url}: {last_error}")

    def iter_records(self, search: str | None = None) -> Iterator[dict[str, Any]]:
        url: str | None = self.base_url
        params: dict[str, str | int] = {"page": 1, "page_size": self.page_size}
        if search:
            params["q"] = search

        while url:
            separator = "&" if "?" in url else "?"
            request_url = url if "page=" in url else f"{url}{separator}" + "&".join(
                f"{key}={value}" for key, value in params.items()
            )
            payload = self._get(request_url)
            data = payload.get("data", [])
            if not isinstance(data, list):
                raise ValueError("The API response field 'data' must be a list")
            yield from (record for record in data if isinstance(record, dict))
            url = payload.get("next_page")

    def ingest_ndjson(self, output: str | Path, search: str | None = None) -> int:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for record in self.iter_records(search):
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        return count

    def ingest_snapshot(self, output: str | Path, search: str | None = None) -> int:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        records = list(self.iter_records(search))
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)
        return len(records)
