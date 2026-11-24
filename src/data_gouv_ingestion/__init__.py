"""Ingestion utilities for data.gouv.fr and public Data Fair datasets."""

from .ademe import (
    DPE_TERTIAIRE_DEFAULT_FIELDS,
    DPE_TERTIAIRE_URL,
    ADEMEDPEIngester,
)
from .ingestion import DataserviceIngester

__all__ = [
    "ADEMEDPEIngester",
    "DataserviceIngester",
    "DPE_TERTIAIRE_URL",
    "DPE_TERTIAIRE_DEFAULT_FIELDS",
]
