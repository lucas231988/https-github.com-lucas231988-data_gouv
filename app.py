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
        progress = st.progress(0, text="Connecting to data.gouv.fr…")
        status = st.status("Fetching dataservices", expanded=True)

        try:
            records = []
            with status:
                st.write("Searching the data.gouv.fr catalog…")
                for record in ingester.iter_records(search=query or None):
                    records.append(record)
                    loaded = len(records)
                    progress.progress(min(loaded / max_records, 1.0), text=f"Fetched {loaded:,} of {max_records:,} requested records")
                    if loaded % 25 == 0:
                        status.update(label=f"Fetching dataservices — {loaded:,} loaded")
                        st.write(f"Downloaded {loaded:,} records…")
                    if loaded >= max_records:
                        break
        except Exception as error:
            progress.empty()
            status.update(label="Fetch failed", state="error", expanded=True)
            status.write(str(error))
            st.error(f"Could not load dataservices: {error}")
            st.stop()

        progress.progress(1.0, text=f"Complete — {len(records):,} records fetched")
        status.update(label=f"Fetch complete — {len(records):,} dataservices", state="complete", expanded=False)
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

    if st.sidebar.button("Load dataset", type="primary"):
        ingester = ADEMEDPEIngester(dataset_id=dataset_id, base_url=base_url)
        progress = st.progress(0, text="Loading dataset metadata…")
        status = st.status("Loading dataset", expanded=True)
        try:
            with status:
                st.write("Reading dataset metadata and fields…")
                metadata = ingester.metadata()
                field_names = [item["key"] for item in metadata.get("schema", []) if item.get("key")]
                progress.progress(0.35, text=f"Metadata loaded — {len(field_names)} fields found")
                status.update(label="Dataset metadata loaded", state="complete", expanded=False)
        except Exception as error:
            progress.empty()
            status.update(label="Metadata load failed", state="error", expanded=True)
            status.write(str(error))
            st.error(f"Could not load dataset metadata: {error}")
            st.stop()

        st.session_state["datafair_loaded"] = {
            "dataset_id": dataset_id,
            "base_url": base_url,
            "preset": preset,
            "metadata": metadata,
            "field_names": field_names,
        }

    loaded = st.session_state.get("datafair_loaded")
    if loaded:
        dataset_id = loaded["dataset_id"]
        base_url = loaded["base_url"]
        preset = loaded["preset"]
        metadata = loaded["metadata"]
        field_names = loaded["field_names"]
        ingester = ADEMEDPEIngester(dataset_id=dataset_id, base_url=base_url)

        st.header(metadata.get("title", dataset_id))
        st.caption(metadata.get("description", "")[:500])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total rows", f"{metadata.get('count', 0):,}")
        col2.metric("Fields", len(field_names))
        col3.metric("Visibility", metadata.get("visibility", "unknown"))

        st.divider()
        st.subheader("Explore rows")
        query = st.text_input("Search / filter text", placeholder="Example: 75, Paris, Vente")
        size = st.slider("Rows per API page", 10, 1000, 100, 10)
        max_records = st.number_input("Maximum records", 1, 10000, 100, 100)

        if preset == "DPE tertiaire":
            defaults = [field for field in DPE_TERTIAIRE_DEFAULT_FIELDS if field in field_names]
        else:
            defaults = field_names[:10]
        selected_fields = st.multiselect("Fields", field_names, default=defaults)

        if st.button("Fetch records", type="primary"):
            progress = st.progress(0, text="Connecting to the Data Fair API…")
            status = st.status("Fetching records", expanded=True)
            try:
                records = []
                with status:
                    st.write("Requesting the first page…")
                    for record in ingester.iter_records(
                        search=query or None,
                        size=size,
                        fields=selected_fields or None,
                        max_records=max_records,
                    ):
                        records.append(record)
                        loaded_count = len(records)
                        progress.progress(min(loaded_count / max_records, 1.0), text=f"Fetched {loaded_count:,} of {max_records:,} requested rows")
                        if loaded_count % 25 == 0:
                            status.update(label=f"Fetching records — {loaded_count:,} loaded")
                            st.write(f"Downloaded {loaded_count:,} rows…")
            except Exception as error:
                progress.empty()
                status.update(label="Fetch failed", state="error", expanded=True)
                status.write(str(error))
                st.error(f"Could not fetch records: {error}")
                st.stop()

            progress.progress(1.0, text=f"Complete — {len(records):,} rows fetched")
            status.update(label=f"Fetch complete — {len(records):,} rows", state="complete", expanded=False)
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
