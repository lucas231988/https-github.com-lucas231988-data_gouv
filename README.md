# Open French API Explorer

A Python project for discovering and ingesting public French open-data APIs. It currently supports:

- **data.gouv.fr dataservices** catalog search
- **ADEME/Data Fair datasets**, including a preset for DPE tertiaire buildings
- Generic Data Fair dataset URLs
- Browser exploration, tables, raw JSON, NDJSON, and JSON downloads

## Project overview

The project has two ingestion layers:

1. `DataserviceIngester` searches and paginates the public data.gouv.fr dataservices API.
2. `ADEMEDPEIngester` loads Data Fair dataset metadata and paginated records through `/lines` endpoints.

The Streamlit UI is a visual layer on top of these ingestion units. API logic remains reusable from Python and does not require the browser UI.

## Installation

Requirements:

- Python 3.11 or newer
- Internet access to the public APIs

Install the project and development dependencies:

```powershell
C:/Python314/python.exe -m pip install -e ".[dev]"
```

If `python` is available in the active terminal, use `python` instead.

## Start the browser UI

```powershell
C:/Python314/python.exe -m streamlit run app.py
```

Open `http://localhost:8501`.

### Explore data.gouv.fr dataservices

1. Keep **data.gouv.fr dataservices** selected.
2. Enter an optional search query.
3. Choose the API page size and maximum record count.
4. Select **Load catalog**.
5. Download the displayed records as NDJSON or JSON.

### Explore a Data Fair dataset

1. Select **ADEME/Data Fair dataset**.
2. Choose **DPE tertiaire** or enter a custom Data Fair URL.
3. Select **Load dataset**.
4. Review metadata: title, row count, field count, and visibility.
5. Enter an optional search/filter term.
6. Choose fields, rows per API page, and the maximum record count.
7. Select **Fetch records**.
8. Browse the table or raw JSON and download NDJSON or JSON.

The DPE tertiaire preset targets:

```text
https://data.ademe.fr/data-fair/api/v1/datasets/dpe-tertiaire
```

The verified dataset contains 515,562 public rows with 135 fields.

## Command-line ingestion

Ingest the complete data.gouv.fr dataservices catalog:

```powershell
C:/Python314/python.exe -m data_gouv_ingestion.cli
```

Search dataservices and create a JSON snapshot:

```powershell
C:/Python314/python.exe -m data_gouv_ingestion.cli --search "energie" --snapshot data/dataservices.json
```

## Python usage

### data.gouv.fr dataservices

```python
from data_gouv_ingestion import DataserviceIngester

ingester = DataserviceIngester(page_size=100)
count = ingester.ingest_ndjson("data/dataservices.ndjson")
print(f"Ingested {count} dataservices")
```

### Generic ADEME/Data Fair dataset

```python
from data_gouv_ingestion import ADEMEDPEIngester

ingester = ADEMEDPEIngester(
    dataset_id="dpe-tertiaire",
    base_url="https://data.ademe.fr/data-fair/api/v1/datasets",
)

records = ingester.iter_records(
    search="NÎMES",
    size=100,
    fields=["numero_dpe", "commune", "classe_consommation_energie"],
    max_records=100,
)

for record in records:
    print(record)
```

Write Data Fair records to NDJSON:

```python
from data_gouv_ingestion import ADEMEDPEIngester

ingester = ADEMEDPEIngester(dataset_id="dpe-tertiaire")
count = ingester.ingest_ndjson(
    "data/dpe-tertiaire.ndjson",
    size=100,
    max_records=1000,
)
print(f"Ingested {count} rows")
```

## Adding a new endpoint

When a new public JSON endpoint or dataservice URL is provided, the ingestion unit is created by following this workflow:

1. Identify metadata, list, and record endpoints.
2. Inspect the API response and pagination mechanism.
3. Create a dedicated Python ingester or reuse the generic Data Fair ingester.
4. Support search, field selection, limits, and retries where available.
5. Provide NDJSON and JSON export methods.
6. Add a preset or custom URL option to the Streamlit UI.
7. Add mocked unit tests and a live smoke test.
8. Update this README and push the verified changes to GitHub.

A typical dataservice JSON file downloaded from data.gouv.fr identifies the public API URL. URLs ending in `/api/v1/datasets/<dataset-id>` can be supplied to the Data Fair explorer. APIs with an account requirement or custom authentication will need API-key or OAuth support before ingestion.

## API contracts

### data.gouv.fr

Endpoint:

```text
GET https://www.data.gouv.fr/api/1/dataservices/
```

Relevant parameters:

- `page`
- `page_size`
- `q` for search

Pagination uses the response `next_page` field.

### Data Fair

Metadata:

```text
GET <base-url>/api/v1/datasets/<dataset-id>
```

Rows:

```text
GET <base-url>/api/v1/datasets/<dataset-id>/lines
```

Relevant parameters:

- `size`
- `q` for text search
- `select` for a comma-separated field list
- `after` or the API-provided `next` URL for pagination

The ingester follows the `next` URL returned by Data Fair.

## Tests

Run the unit suite:

```powershell
C:/Python314/python.exe -m pytest -q
```

The suite uses mocked API responses for determinism and includes live endpoint smoke tests when the public API is available.

## Project structure

```text
app.py                                  Streamlit explorer
src/data_gouv_ingestion/ingestion.py    data.gouv.fr dataservices ingester
src/data_gouv_ingestion/ademe.py        Generic Data Fair ingester and DPE preset
src/data_gouv_ingestion/cli.py          Command-line interface
src/data_gouv_ingestion/__init__.py     Public Python exports
tests/test_ingestion.py                 Unit and mock tests
```

## Data usage

Check each dataset's license and usage terms before large-scale ingestion or redistribution. Public availability does not remove attribution, licensing, or responsible-use obligations.
