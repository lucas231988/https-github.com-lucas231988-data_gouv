import json

from data_gouv_ingestion.ademe import ADEMEDPEIngester
from data_gouv_ingestion.ingestion import DataserviceIngester


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_instantiation():
    ingester = DataserviceIngester(page_size=25)
    assert ingester.page_size == 25
    assert ingester.base_url.endswith("/dataservices/")


def test_iter_records_follows_pagination():
    ingester = DataserviceIngester(page_size=2)
    requests_made = []

    def get(url, timeout):
        requests_made.append(url)
        if "page=1" in url:
            return MockResponse({
                "data": [{"id": "1"}, {"id": "2"}],
                "next_page": "https://example.test/dataservices/?page=2",
            })
        return MockResponse({"data": [{"id": "3"}], "next_page": None})

    ingester.session.get = get

    records = list(ingester.iter_records())

    assert records == [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    assert len(requests_made) == 2


def test_ingest_ndjson(tmp_path):
    ingester = DataserviceIngester()
    ingester.iter_records = lambda search=None: iter([
        {"id": "1", "title": "API énergie"},
        {"id": "2", "title": "Second API"},
    ])
    output = tmp_path / "dataservices.ndjson"

    count = ingester.ingest_ndjson(output)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert count == 2
    assert json.loads(lines[0])["title"] == "API énergie"


def test_ingest_snapshot(tmp_path):
    ingester = DataserviceIngester()
    ingester.iter_records = lambda search=None: iter([{"id": "1"}, {"id": "2"}])
    output = tmp_path / "snapshot.json"

    count = ingester.ingest_snapshot(output)

    assert count == 2
    assert json.loads(output.read_text(encoding="utf-8")) == [{"id": "1"}, {"id": "2"}]


def test_ademe_metadata():
    ingester = ADEMEDPEIngester()
    ingester.session.get = lambda url, timeout: MockResponse({"id": "dpe-france", "count": 10728950})

    metadata = ingester.metadata()

    assert metadata["id"] == "dpe-france"
    assert metadata["count"] == 10728950


def test_ademe_record_pagination():
    ingester = ADEMEDPEIngester()

    def get(url, params, timeout):
        if params:
            return MockResponse({
                "results": [{"numero_dpe": "1"}],
                "next": "https://example.test/page-2",
            })
        return MockResponse({"results": [{"numero_dpe": "2"}], "next": None})

    ingester.session.get = get

    records = list(ingester.iter_records(size=1))

    assert records == [{"numero_dpe": "1"}, {"numero_dpe": "2"}]
