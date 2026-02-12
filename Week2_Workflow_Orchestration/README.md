# Week 2: Workflow Orchestration with Kestra

This folder contains the workflows and scripts for Week 2 of the Data Engineering Zoomcamp, focusing on **Workflow Orchestration** using [Kestra](https://kestra.io).

## 📚 Overview

Orchestration is the process of coordinating multiple tasks (scripts, queries, API calls) into a unified workflow. It handles scheduling, error handling, retries, and dependency management.

In this module, we used **Kestra**, an event-driven orchestrator, to build:
1.  **Postgres ETL**: Extracting CSVs, processing them in SQL, and loading them into a local Postgres database.
2.  **GCP ELT**: Moving the pipeline to the cloud using Google Cloud Storage (GCS) and BigQuery.
3.  **AI Integration**: Using LLMs to enhance workflows and documentation.

## 🛠️ Setup

### Prerequisites
- Docker & Docker Compose
- Google Cloud Platform (GCP) Account & Service Account Key
- Gemini API Key (optional, for AI flows)

### Quick Start
1.  Cloned the repo and navigated to `Week2_Workflow_Orchestration`.
2.  **Configured Secrets**:
    - Created a `.env` file (based on `.env.example` if available).
    - Added `SECRET_GCP_CREDS` (Base64 encoded GCP Service Account Key).
    - Added `GEMINI_API_KEY`.
3.  **Launched Kestra**:
    ```bash
    docker compose up -d
    ```
4.  Accessed the Kestra UI at [http://localhost:8080](http://localhost:8080).

## 🚀 Workflows Explained

### 1. Postgres ETL (`04_postgres_taxi.yaml`)
This flow demonstrates a classic ETL process running locally.
- **Extract**: Uses a `Shell` task to download taxi data (CSV) from GitHub.
- **Staging**: Loads raw CSV data into a Postgres staging table using `CopyIn`.
- **Transform**:
    - Adds a unique ID (`md5` hash of columns) and filename.
    - Handles schema differences between Yellow and Green taxi data using `If` conditions.
- **Load**: Merges the staging data into the final `tripdata` table using `MERGE` (upsert).

### 2. GCP ELT (`08_gcp_taxi.yaml`)
This flow migrates the process to the cloud, leveraging BigQuery's compute power (ELT).
- **Extract**: Downloads the same CSV data.
- **Load (to Lake)**: Uploads the raw file directly to **Google Cloud Storage (GCS)**.
- **Transform (in Warehouse)**:
    - Creates a BigQuery **External Table** linked to the GCS file.
    - Creates a native BigQuery table with partitioning/clustering.
    - Executes SQL transformations (cleanup, deduplication) directly inside BigQuery.

### 3. Scheduling & Backfills (`09_gcp_taxi_scheduled.yaml`)
Automates the pipeline to run monthly.
- **Triggers**: Uses a `Schedule` trigger (e.g., `0 9 1 * *`) to run on the 1st of every month.
- **Backfills**: Allows processing historical data (e.g., all of 2019 and 2020) by executing the flow for specific past time ranges.

### 4. AI & RAG (`11_chat_with_rag.yaml`)
Demonstrates how to use **Retrieval Augmented Generation (RAG)** to give AI context.
- **Ingestion**: Reads Kestra release notes from GitHub and creates vector embeddings.
- **Retrieval**: When asked a question, it searches the embeddings for relevant context.
- **Generation**: Passes the context + question to Gemini to generate an accurate, grounded answer.

## 🧠 Key Concepts & Architecture

### ETL vs ELT
The course demonstrates two distinct architectural patterns:
1.  **ETL (Extract-Transform-Load)**:
    *   **Flow**: `04_postgres_taxi`
    *   **Process**: Data is downloaded, transformed locally (e.g., in Python or a local Postgres instance), and then loaded into the final table.
    *   **Use Case**: Smaller datasets where local compute is sufficient.
2.  **ELT (Extract-Load-Transform)**:
    *   **Flow**: `08_gcp_taxi`
    *   **Process**: Data is extracted and immediately loaded into a **Data Lake** (GCS). Transformation happens *inside* the **Data Warehouse** (BigQuery) using its massive distributed compute power.
    *   **Use Case**: Big Data scenarios where moving data is expensive and cloud warehouses offer superior performance.

### Kestra Specifics
- **Inputs & Outputs**: Tasks typically produce outputs that can be used by downstream tasks.
    *   *Example*: `{{ outputs.extract.outputFiles['*.csv'] }}` passes the downloaded file from the `extract` task to the next task.
- **Templating**: Kestra uses **Pebble** templating (similar to Jinja2) for dynamic variables.
    *   *Example*: `{{ trigger.date | date('yyyy-MM') }}` formats the schedule date.
- **Plugin Defaults**: To avoid repeating configuration (like DB credentials) in every task, we use `pluginDefaults` to set them globally for the flow.
- **Backfills**: A powerful feature that allows re-running a scheduled flow for past dates. By using `trigger.date`, the flow processes data for the *logical date* of the execution, not the *actual wall-clock time*.

## 🛡️ Security
- **.gitignore**: Configured to ignore `.env`, `*.txt` (keys), and `*.py` helpers.
- **Environment Variables**: secrets are injected via `${VAR_NAME}` in `docker-compose.yml`.

## 📂 Workflows Reference

Here is a complete list of the flows in this directory and their purpose:

| Flow ID | Description |
| :--- | :--- |
| **01_hello_world** | Basic introduction to Kestra flow structure. |
| **02_python** | Demonstrates running Python scripts and handling outputs. |
| **03_getting_started...** | A simple ETL pipeline: Info from HTTP API -> Python Transform -> DuckDB Query. |
| **04_postgres_taxi** | **Core ETL**: Loads Taxi CSVs into local Postgres. |
| **05_postgres_taxi...** | Scheduled version of the local Postgres ETL with backfill capabilities. |
| **06_gcp_kv** | Helper utility to set KV pairs (Project ID, Bucket Name) for GCP flows. |
| **07_gcp_setup** | Infrastructure-as-Code: Creates GCS Buckets and BigQuery Datasets. |
| **08_gcp_taxi** | **Core ELT**: Loads Taxi CSVs to GCS, then processes in BigQuery. |
| **09_gcp_taxi_scheduled** | Scheduled version of the GCP ELT flow for monthly processing. |
| **10_chat_without_rag** | Demonstrates AI hallucination/limitations when querying without context. |
| **11_chat_with_rag** | **Core AI**: Uses RAG to provide accurate answers about Kestra release notes. |

