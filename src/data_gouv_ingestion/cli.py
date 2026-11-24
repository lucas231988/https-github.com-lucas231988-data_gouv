from __future__ import annotations

import argparse

from .ingestion import DataserviceIngester


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest data.gouv.fr dataservices")
    parser.add_argument("--search", "-q", help="Optional search query")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--ndjson", default="data/dataservices.ndjson")
    parser.add_argument("--snapshot", help="Optional full JSON snapshot")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ingester = DataserviceIngester(page_size=args.page_size)
    count = ingester.ingest_ndjson(args.ndjson, search=args.search)
    if args.snapshot:
        ingester.ingest_snapshot(args.snapshot, search=args.search)
    print(f"Ingested {count} dataservices into {args.ndjson}")


if __name__ == "__main__":
    main()
