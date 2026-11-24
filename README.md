# data-gouv-ingestion

A Python ingestion unit for the public [data.gouv.fr dataservices API](https://www.data.gouv.fr/dataservices/search).

## Features

- Follows API pagination through `next_page`
- Supports optional API search text
- Writes streaming NDJSON or a full JSON snapshot
- Retries transient HTTP and JSON failures
- Provides a reusable Python class and command-line interface

## Install

```powershell
C:/Python314/python.exe -m pip install -e ".[dev]"
```

## Run

Ingest the complete catalog to NDJSON:

```powershell
C:/Python314/python.exe -m data_gouv_ingestion.cli
```

Create an NDJSON file and a JSON snapshot with a search:

```powershell
C:/Python314/python.exe -m data_gouv_ingestion.cli --search "energie" --snapshot data/dataservices.json
```

## Python usage

```python
from data_gouv_ingestion import DataserviceIngester

ingester = DataserviceIngester(page_size=100)
count = ingester.ingest_ndjson("data/dataservices.ndjson")
print(count)
```

## Test

```powershell
C:/Python314/python.exe -m pytest
```

## API contract

The ingester calls `https://www.data.gouv.fr/api/1/dataservices/` with `page` and `page_size` parameters. API responses contain a `data` list plus `next_page`, `page`, `page_size`, and `total` metadata.
