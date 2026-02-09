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
12. Terraform: Concepts & Basics

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

## 12) Terraform: Concepts & Basics

### Part 1: Conceptual Overview
**1. What is Terraform?**
- **Analogy**: Just as "terraforming" a planet means creating conditions suitable for life (atmosphere, water), HashiCorp’s Terraform prepares infrastructure (cloud or local) so software can live and run there.
- **Definition**: It is an Infrastructure as Code (IaC) tool. It allows you to define resources in human-readable configuration files that can be versioned, reused, and shared.
- **Workflow**: It uses a consistent workflow to provision and manage infrastructure throughout its lifecycle.

**2. Why use Terraform?**
- **Simplicity**: You can track infrastructure definitions in a single file, easily viewing parameters like disk size or storage type.
- **Collaboration**: Because infrastructure is code, it can be pushed to repositories (like GitHub) for review and collaboration before deployment.
- **Reproducibility**: You can easily replicate environments (e.g., copying a Dev environment to Production) or share projects with friends.
- **Resource Management**: It helps ensure resources are removed when no longer needed ("Terraform Destroy"), preventing accidental charges for unused infrastructure.

**3. What Terraform is NOT:**
- It does not manage or update code on the infrastructure (it is not a software deployment tool).
- It cannot change "immutable" resources directly (e.g., changing a VM type requires destroying and recreating the VM).
- It does not manage resources that were not defined in the Terraform files.

**4. Architecture & Providers**
- **Local Machine**: Terraform runs locally.
- **Providers**: Terraform uses "Providers" (plugins) to communicate with specific platforms (e.g., AWS, GCP, Azure, Kubernetes). You define the provider in your file, and Terraform handles the API calls.
- **Key Commands**:
    - `terraform init`: Downloads the necessary provider code/plugins.
    - `terraform plan`: Previews the resources that will be created or modified.
    - `terraform apply`: Executes the plan and builds the infrastructure.
    - `terraform destroy`: Removes all infrastructure defined in your files.

### Part 2: Practical Implementation
**1. Prerequisites & Security**
- **Service Account**: You need a Service Account (a non-human account for software) to authenticate with GCP.
- **Permissions (IAM)**: Assign specific roles to the Service Account based on what you need to build (e.g., Storage Admin for buckets, BigQuery Admin, Compute Admin).
- **Keys**: Generate a JSON key for the Service Account to authenticate locally.
    - **Security Warning**: Never commit these keys to GitHub. If exposed, attackers can spin up expensive resources (e.g., for Bitcoin mining). Always add key files to `.gitignore`.

**2. Development Environment Setup**
- **VS Code**: Recommended to install the HashiCorp Terraform extension for syntax highlighting and autocomplete.
- **Main Configuration (`main.tf`)**:
    - Define the provider block (e.g., `google`) with the project ID and region.
    - **Authentication**: You can set the credential path via an environment variable (e.g., `export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"`) to avoid hardcoding secrets in the file.

**3. The Terraform Lifecycle (Demo)**
- **Formatting**: Run `terraform fmt` to automatically format your code for readability.
- **Initialization**: Run `terraform init` to download the Google provider and create the lock file (`.terraform.lock.hcl`).
- **Defining Resources**:
    - **Example**: Creating a Google Storage Bucket.
    - **Syntax**: `resource "resource_type" "local_name" { ... }`.
    - **Note**: The bucket name inside the block must be globally unique across all of GCP.
    - **Lifecycle Rules**: You can define rules, such as deleting objects after 3 days or aborting incomplete multi-part uploads.
- **Planning**: Run `terraform plan` to see what will happen. This helps verify defaults (e.g., storage class) and catch errors before billing starts.
- **Applying**: Run `terraform apply`. This creates the resources and generates a `terraform.tfstate` file, which tracks the state of your infrastructure.
- **Destroying**: Run `terraform destroy` to remove all resources managed by the state file.

**4. Important Files**
- `main.tf`: Your primary configuration file.
- `terraform.tfstate`: Stores the mapping between your code and real-world resources (created after apply).
- `.gitignore`: Critical for excluding sensitive files (keys) and system files (`.tfstate`, `.terraform` directory) from version control.

### Part 3: Variables & Resource Expansion
**1. Expanding Resources: Adding BigQuery**
- **Documentation Strategy**: When adding new resources (like a BigQuery dataset), it is best to check the official Terraform documentation to distinguish between **required** fields (like `dataset_id`) and **optional** fields (like `location`, which defaults to "US" multi-region).
- **Resource Configuration**:
    - To create a dataset, you define a `resource "google_bigquery_dataset" "demo_dataset"` block.
    - **Crucial Argument**: When working with datasets (or buckets), it is helpful to set `delete_contents_on_destroy = true`. Without this, `terraform destroy` will fail if the dataset contains tables, forcing manual deletion.

**2. Implementing Variables**
- **Purpose**: Hardcoding values (like project IDs or regions) makes code hard to share or reuse. Variables allow you to define values in one place and reference them throughout your configuration.
- **The `variables.tf` File**: By convention, you create a separate file named `variables.tf` to declare your variables.
- **Variable Syntax**:
    - Variables are defined with a description and a default value.
    - Example:
        ```hcl
        variable "location" {
          description = "Project Location"
          default     = "US"
        }
        ```
    - You can create variables for anything, including bucket names, storage classes, and project IDs.
- **Usage in `main.tf`**: Replace hardcoded strings with `var.variable_name`.
    - Example: `location = var.location`.

**3. Handling Credentials via Config**
- **Alternative Authentication**: Instead of using the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, you can define credentials directly in the `provider` block using a variable.
- **The `file()` Function**:
    - You can create a variable (e.g., `credentials`) that holds the *path* to your JSON key file.
    - In the `provider "google"` block, you use the built-in `file()` function to load the key: `credentials = file(var.credentials)`.

**4. State Management & Advanced Concepts**
- **Backup State**: Terraform creates a `.backup` file alongside `terraform.tfstate`. If the state file is corrupted or fails to update during a destroy command, this backup can be used to restore the state so Terraform knows what to delete.
- **Future Learning (`.tfvars`)**: While `variables.tf` sets defaults, you can use `.tfvars` files to pass different sets of variables at runtime (e.g., for different environments), though this is an advanced topic for later.

---

## Attribution & license ✍️
- Content summarized from the DataTalksClub Data Engineering Zoomcamp materials: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform/docker-sql
- This README is an original summary and includes links back to the original materials.
