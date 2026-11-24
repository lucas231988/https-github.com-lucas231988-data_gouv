import json

import pandas as pd
import streamlit as st

from data_gouv_ingestion import (
    ADEMEDPEIngester,
    DPE_TERTIAIRE_DEFAULT_FIELDS,
    DPE_TERTIAIRE_URL,
    DataserviceIngester,
)


st.set_page_config(page_title="Open API Explorer", page_icon="🇫🇷", layout="wide")
st.title("Open French API Explorer")
st.caption("Explore data.gouv.fr dataservices and public ADEME/Data Fair datasets.")

source = st.sidebar.radio("Data source", ["data.gouv.fr dataservices", "ADEME/Data Fair dataset"])

if source == "data.gouv.fr dataservices":
    query = st.sidebar.text_input("Search query", placeholder="melodi, adresse, énergie")
    page_size = st.sidebar.slider("Page size", 10, 100, 100, 10)
    max_records = st.sidebar.number_input("Maximum records", 1, 5000, 200, 100)

    if st.sidebar.button("Load catalog", type="primary"):
        ingester = DataserviceIngester(page_size=page_size)
        with st.spinner("Loading dataservices..."):
            try:
                records = []
                for record in ingester.iter_records(search=query or None):
                    records.append(record)
                    if len(records) >= max_records:
                        break
            except Exception as error:
                st.error(f"Could not load dataservices: {error}")
                st.stop()

        st.success(f"Loaded {len(records)} dataservices")
        if not records:
            st.info("No dataservices matched this search.")
            st.stop()

        rows = []
        for record in records:
            organization = record.get("organization") or {}
            owner = record.get("owner") or {}
            rows.append({
                "Title": record.get("title") or "",
                "Organization": organization.get("name") or owner.get("name") or "",
                "Access": record.get("access_type") or "",
                "Base API URL": record.get("base_api_url") or "",
                "Page": record.get("self_web_url") or "",
                "Updated": record.get("metadata_modified_at") or "",
                "Views": (record.get("metrics") or {}).get("views", 0),
            })

        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.download_button("Download NDJSON", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), "dataservices.ndjson")
        st.download_button("Download JSON", json.dumps(records, ensure_ascii=False, indent=2), "dataservices.json")

else:
    preset = st.sidebar.selectbox("Dataset preset", ["DPE tertiaire", "Custom Data Fair URL"])
    default_url = DPE_TERTIAIRE_URL if preset == "DPE tertiaire" else "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-france"
    dataset_url = st.sidebar.text_input("Dataset API URL", default_url)

    prefix = "/api/v1/datasets/"
    if prefix not in dataset_url:
        st.sidebar.error("Enter a Data Fair URL containing /api/v1/datasets/")
        st.stop()

    base_url = dataset_url.split(prefix)[0].rstrip("/") + "/api/v1/datasets"
    dataset_id = dataset_url.split(prefix)[1].split("/")[0]
    ingester = ADEMEDPEIngester(dataset_id=dataset_id, base_url=base_url)

    if st.sidebar.button("Load dataset", type="primary"):
        with st.spinner("Loading dataset metadata..."):
            try:
                metadata = ingester.metadata()
                field_names = [item["key"] for item in metadata.get("schema", []) if item.get("key")]
            except Exception as error:
                st.error(f"Could not load dataset metadata: {error}")
                st.stop()

        title = metadata.get("title", dataset_id)
        st.header(title)
        st.caption(metadata.get("description", "")[:500])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total rows", f"{metadata.get('count', 0):,}")
        col2.metric("Fields", len(field_names))
        col3.metric("Visibility", metadata.get("visibility", "unknown"))

        query = st.text_input("Search / filter text", placeholder="Example: 75, Paris, D")
        size = st.slider("Rows per API page", 10, 1000, 100, 10)
        max_records = st.number_input("Maximum records", 1, 10000, 100, 100)

        if preset == "DPE tertiaire":
            defaults = [field for field in DPE_TERTIAIRE_DEFAULT_FIELDS if field in field_names]
        else:
            defaults = field_names[:10]
        selected_fields = st.multiselect("Fields", field_names, default=defaults)

        if st.button("Fetch records", type="primary"):
            with st.spinner("Fetching records..."):
                records = list(ingester.iter_records(
                    search=query or None,
                    size=size,
                    fields=selected_fields or None,
                    max_records=max_records,
                ))

            st.success(f"Loaded {len(records)} rows")
            if records:
                table, raw = st.tabs(["Table", "Raw JSON"])
                with table:
                    st.dataframe(pd.DataFrame(records), width="stretch", hide_index=True)
                with raw:
                    st.json(records)

                st.download_button("Download NDJSON", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), f"{dataset_id}.ndjson")
                st.download_button("Download JSON", json.dumps(records, ensure_ascii=False, indent=2), f"{dataset_id}.json")
            else:
                st.info("No rows matched the request.")
