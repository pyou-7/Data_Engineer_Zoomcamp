# Data Engineering Zoomcamp

This repository contains my work and notes for the DataTalksClub Data Engineering Zoomcamp.

## Course Structure

### [Week 1: Docker, Terraform, SQL](./Week1_Docker_Terraform_SQL/README.md)
**Focus**: Containerization, Infrastructure as Code (IaC), and basic SQL.

**Key Topics Covered**:
- **Docker**: Containerizing Python scripts and running PostgreSQL/pgAdmin locally.
- **Data Ingestion**: Building a data pipeline to ingest NYC Taxi data into Postgres.
- **SQL**: Basic data exploration and analysis using SQL.
- **Terraform**:
    - Basics: Providers, Resources, State (`terraform.tfstate`).
    - Cloud: Provisioning Google Cloud Storage (GCS) buckets and BigQuery datasets.
    - **Variables**: Using `variables.tf` to make configurations reusable and secure.

[View Week 1 Comprehensive Notes & Code](./Week1_Docker_Terraform_SQL/README.md)

---
### [Week 2: Workflow Orchestration](./Week2_Workflow_Orchestration/README.md)
**Focus**: Orchestrating data pipelines with **Kestra**, managing dependencies, and automating workflows.

**Key Topics Covered**:
- **Kestra Basics**: Flows, Tasks, Inputs/Outputs, and Docker deployment.
- **ETL vs ELT**:
    - **ETL**: Extracting to local Postgres, transforming with SQL.
    - **ELT**: Loading to **GCS** and transforming in **BigQuery** for scale.
- **Scheduling**: Cron-based triggers and managing **Backfills** for historical data.
- **AI Integration**: Using LLMs (Gemini) and RAG to enhance engineering workflows.

[View Week 2 Comprehensive Notes & Code](./Week2_Workflow_Orchestration/README.md)

---

### [Week 3: Data Warehouse & BigQuery](./Week3_Data_Warehouse_GCP/README.md)
**Focus**: Building a modern Data Warehouse using **Google BigQuery**, optimizing for performance/cost, and running ML models with SQL.

**Key Topics Covered**:
- **Data Warehousing**: OLAP vs. OLTP, and the role of a DW in analytics.
- **BigQuery Architecture**: Serverless design separating Compute (Dremel) from Storage (Colossus).
- **Optimization**: Using **Partitioning** and **Clustering** to drastically reduce query costs.
- **BigQuery ML**: Training and deploying Machine Learning models directly using SQL.

[View Week 3 Comprehensive Notes & Code](./Week3_Data_Warehouse_GCP/README.md)

---
