# Week 1 — Docker, PostgreSQL & Local Data Ingestion (Comprehensive Notes) 🐳📦

This file is a comprehensive, runnable and workspace-tailored guide covering Docker, PostgreSQL, the NYC taxi dataset ingestion pipeline, and common SQL examples. It's based on the DataTalksClub Zoomcamp materials but adapted to the actual files in this repository (`Week1_Docker_Terraform_SQL/pipeline`).

--

## Table of contents
1. Overview
2. Quick setup (prerequisites and environment)
3. Project layout
4. Run locally with `uv` (recommended for development)
5. Run with Docker (build and run the ingestion image)
6. Run with Docker Compose (pgdatabase + pgadmin)
7. Inspecting and querying data (pgcli, pgAdmin)
8. SQL examples & analysis
9. Troubleshooting & common issues
10. Cleanup and disk space recovery
11. Credits & references

---

## 1) Overview
This workshop demonstrates:
- Containerizing services and the pipeline with Docker
- Running PostgreSQL in Docker and using `pgAdmin` to explore
- Ingesting the NYC Yellow taxi dataset into Postgres using a chunked pandas pipeline (`pipeline/nyc_taxi_load.py`)
- Using `uv` for virtual envs and reproducible dependency installs

The `pipeline/` folder in this repo contains all code used in these notes.

---

## 2) Quick setup
Requirements:
- Docker and docker-compose installed
- Python 3.11+ (3.13 recommended)
- `uv` (optional but recommended): `pip install uv`

Clone this repo (if not already):

```bash
# from a location you control
git clone https://github.com/pyou-7/Data_Engineer_Zoomcamp.git
cd Data_Engineer_Zoomcamp/Week1_Docker_Terraform_SQL/pipeline
```

Install dev dependencies (optional, from repo root):

```bash
uv init --python=3.13  # if you are setting it up from scratch
uv add --dev jupyter pgcli tqdm
uv add sqlalchemy "psycopg[binary,pool]"
```

Notes:
- This project uses `pyproject.toml`, `.python-version` and `uv.lock`.
- Running with `uv run` ensures the environment is consistent across machines.

---

## 3) Project layout (important files)
- `Dockerfile` — container image for the ingestion pipeline (copies `uv` binary and installs deps)
- `docker-compose.yaml` — example compose file to run Postgres + pgAdmin
- `nyc_taxi_load.py` — main ingestion script (Click CLI) — reads chunks and writes to Postgres
- `pipeline.py` — small example pipeline (writes a parquet file)
- `main.py` — short demo script
- `pyproject.toml`, `uv.lock`, `.python-version` — dependency & venv management

Snippet: `pipeline/nyc_taxi_load.py` (core loop)

```python
# important parts (see file for full code)
from sqlalchemy import create_engine
import pandas as pd
from tqdm.auto import tqdm

engine = create_engine(f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")

df_iter = pd.read_csv(url, dtype=dtype, parse_dates=parse_dates, iterator=True, chunksize=chunksize)

for df_chunk in tqdm(df_iter):
    if first:
        df_chunk.head(0).to_sql(name=target_table, con=engine, if_exists='replace')
        first = False
    df_chunk.to_sql(name=target_table, con=engine, if_exists='append')
```

---

## 4) Run locally (development mode)
Using `uv` is convenient for iterative development:

1. Start Postgres locally with Docker (in background):

```bash
docker run -d --name pgdatabase \
  -e POSTGRES_USER=root -e POSTGRES_PASSWORD=root -e POSTGRES_DB=ny_taxi \
  -v ny_taxi_postgres_data:/var/lib/postgresql -p 5432:5432 postgres:18
```

2. Run ingestion script directly from repo (recommended while developing):

```bash
cd Week1_Docker_Terraform_SQL/pipeline
uv run python nyc_taxi_load.py --pg-user=root --pg-pass=root --pg-host=localhost --pg-port=5432 --pg-db=ny_taxi --year=2021 --month=1 --target-table=yellow_taxi_data
```

Notes:
- For quick testing, reduce `--chunksize` to 1000.
- Use `uv run pgcli -h localhost -p 5432 -u root -d ny_taxi` to connect and inspect data from the terminal (password `root`).

---

## 5) Build & run the ingestion image (Docker)
Build image (from `pipeline/` folder):

```bash
cd Week1_Docker_Terraform_SQL/pipeline
docker build -t taxi_ingest:v001 .
```

Run (make sure `pgdatabase` is reachable; if using a docker network use the container name as host):

```bash
docker run -it --network=pg-network taxi_ingest:v001 --pg-user=root --pg-pass=root --pg-host=pgdatabase --pg-port=5432 --pg-db=ny_taxi --year=2021 --month=1
```

If you run Postgres as a standalone container (name `pgdatabase`), you can use the `--network` flag to connect both containers into the same network.

Tips:
- Use `--rm` to remove the container after it finishes.
- Use environment variables (or better secrets) for production credentials.

---

## 6) Run with Docker Compose (pgdatabase + pgAdmin)
A `docker-compose.yaml` is present in `pipeline/`. Example:

```yaml
services:
  pgdatabase:
    image: postgres:18
    environment:
      POSTGRES_USER: "root"
      POSTGRES_PASSWORD: "root"
      POSTGRES_DB: "ny_taxi"
    volumes:
      - "ny_taxi_postgres_data:/var/lib/postgresql"
    ports:
      - "5432:5432"

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: "admin@admin.com"
      PGADMIN_DEFAULT_PASSWORD: "root"
    volumes:
      - "pgadmin_data:/var/lib/pgadmin"
    ports:
      - "8085:80"

volumes:
  ny_taxi_postgres_data:
  pgadmin_data:
```

Start services:

```bash
docker-compose up -d
```

- Access pgAdmin at: http://localhost:8085 (login: `admin@admin.com` / `root`) and register server with host `pgdatabase`, port `5432`, user `root`.
- To run the ingestion container so it can reach the DB created by compose, find the compose network name (e.g., `pipeline_default`) with `docker network ls`, and use `--network=<name>` when running `taxi_ingest`.

---

## 7) Inspecting & querying data
- Using `pgcli` (fast terminal UI):

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
# or inside the compose network use host pgdatabase
```

- Example SQL to check table schema:

```sql
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'yellow_taxi_data';
```

---

## 8) SQL examples & analysis
- Simple join with zones (example):

```sql
SELECT
  tpep_pickup_datetime,
  tpep_dropoff_datetime,
  total_amount,
  CONCAT(zpu."Borough", ' | ', zpu."Zone") AS pickup_loc
FROM yellow_taxi_data t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
LIMIT 100;
```

- Aggregation: trips per day

```sql
SELECT CAST(tpep_dropoff_datetime AS date) AS day, COUNT(*) AS trips
FROM yellow_taxi_data
GROUP BY day
ORDER BY day DESC
LIMIT 30;
```

---

## 9) Troubleshooting & common issues
- DtypeWarning when reading CSV -> explicitly pass `dtype` mapping and `parse_dates` (already in `nyc_taxi_load.py`).
- Connection refused to Postgres -> ensure Postgres container is running and port mapping is correct. Use `docker ps` and `docker logs`.
- If Docker image build fails due to `uv sync --locked`, ensure `uv.lock` and network access are available; try `uv sync` locally to validate.
- Memory issues -> reduce `--chunksize` to smaller number like 10k or 1k while testing.

---

## 10) Cleanup & free space
Stop compose services and remove volumes:

```bash
docker-compose down -v
```

Remove unused images and volumes (careful):

```bash
docker image prune -a
docker volume prune
# or: docker system prune -a --volumes  # removes everything
```

---

## 11) Credits & references
- Original workshop: DataTalksClub — Data Engineering Zoomcamp (01 Docker / Terraform / SQL)
  - https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform/docker-sql
- Dataset: NYC TLC Trip Record Data
  - https://github.com/DataTalksClub/nyc-tlc-data
- Examples inspired by community notes and repositories.

---

If you want, I can also:
- Add a `RUN.md` with short runnable command snippets in the root of `pipeline/` (recommended). ✅
- Add CI checks that run the pipeline with a small sample dataset (quick smoke test). ✅

---

*Updated to match your repository and script names.*
- You can run the provided Docker Compose in `Week1_Docker_Terraform_SQL/pipeline/` (edit paths if needed) or run services directly with provided Docker commands.

---

## Attribution & license ✍️
- Content summarized from the DataTalksClub Data Engineering Zoomcamp materials: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform/docker-sql
- This README is an original summary and includes links back to the original materials.

---

If you want, I can:
- Add detailed step-by-step run instructions tailored to your local setup (docker vs compose). ✅
- Extract and include the `pipeline/` code examples directly into this README as short annotated snippets. ✅

Would you like me to commit this README and push it to `origin/main`? (Yes/No)