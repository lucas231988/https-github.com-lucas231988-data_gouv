"""Ingestion utilities for data.gouv.fr and public Data Fair datasets."""

from .ademe import ADEMEDPEIngester
from .ingestion import DataserviceIngester

__all__ = ["ADEMEDPEIngester", "DataserviceIngester"]
