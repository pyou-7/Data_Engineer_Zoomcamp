# Week 3: Data Warehouse & BigQuery

This week focused on **Data Warehousing** concepts and **Google BigQuery** as a serverless, scalable data warehouse solution. We explored architecture, optimization techniques like partitioning and clustering, and even Machine Learning directly within SQL.

## 📚 1. Data Warehouse Concepts

### OLTP vs. OLAP
Data processing systems generally fall into two categories:

| Feature | OLTP (Online Transaction Processing) | OLAP (Online Analytical Processing) |
| :--- | :--- | :--- |
| **Purpose** | Day-to-day business operations (e.g., e-commerce purchases) | Decision support, analysis, BI reporting |
| **Updates** | Fast, frequent, small updates | Periodic large batch updates |
| **Design** | Normalized (for consistency/efficiency) | Denormalized (using Star/Snowflake schema for read speed) |
| **Target User** | Customers, Clerks | Data Analysts, Data Scientists, Executives |
| **Example** | PostgreSQL Backend for an App | BigQuery for Analytics |

### What is a Data Warehouse?
A **Data Warehouse (DW)** is an OLAP system aimed at reporting and data analysis. It consolidates data from various sources (OLTP databases, flat files, APIs).
*   **Staging Area**: Raw data is ingested here first before transformation.
*   **Data Marts**: Smaller, subject-oriented slices of the DW for specific departments (e.g., Marketing, Sales).

---

## ⚡ 2. BigQuery Architecture & Internals

BigQuery is **Serverless** and separates **Compute** from **Storage**, allowing them to scale independently.

### Key Components
1.  **Colossus (Storage)**: Google's global distributed storage system. Stores data in a **Columnar** format (unlike row-oriented CSVs/OLTP).
    *   *Benefit*: Dremel only reads the specific columns requested in the query, drastically reducing I/O and cost.
2.  **Dremel (Compute)**: The query execution engine. It breaks queries into an execution tree with **Mixers** (aggregation) and **Slots** (leaf workers).
    *   *Benefit*: Massively parallel execution.
3.  **Jupiter (Network)**: High-speed petabit network connecting Compute and Storage.
4.  **Borg (Orchestration)**: Manages resource allocation (precursor to Kubernetes).

---

## 🚀 3. Optimizing BigQuery: Partitioning & Clustering

To improve query performance and reduce cost, we minimize the amount of data scanned.

### Partitioning
Splits a large table into smaller segments (partitions) based on a specific column.
*   **Types**:
    *   **Time-unit**: `DATE`, `TIMESTAMP` column (e.g., daily partitions).
    *   **Ingestion time**: Based on when data arrived.
    *   **Integer range**: Based on a number ID.
*   **Limit**: Up to 4,000 partitions.
*   **Benefit**: If you filter by the partition column (e.g., `WHERE date = '2019-01-01'`), BQ *prunes* all other partitions and scans only the relevant data.

### Clustering
Sorts and co-locates data within a table (or partition) based on up to 4 columns.
*   **Benefit**: efficient filtering and aggregation on high-cardinality columns (e.g., `VendorID`, `Tag`).
*   **Difference**: Unlike partitioning, clustering creates a "weak sort" and doesn't strictly divide files, but BQ maintains metadata to skip data blocks during scans.

### Comparison
| Feature | Partitioning | Clustering |
| :--- | :--- | :--- |
| **Cost** | Known upfront (BQ knows exactly which partitions to scan) | Unknown until query runs |
| **Granularity** | Coarse (Day/Month) | Fine (User IDs, Tags) |
| **Use Case** | Filter by Date/Time | Filter/Sort by high-cardinality IDs |

---

## 🛠️ 4. BigQuery Best Practices

### Cost Reduction
*   🚫 **Avoid `SELECT *`**: Columnar storage means you pay for every column you select. Only select what you need.
*   👁️ **Preview Query Costs**: Always look at the top-right corner of the query editor to see "This query will process X GB".
*   🧱 **Partition & Cluster**: Always partition by Date if your queries filter by date.

### Performance
*   **Denormalize**: BigQuery loves wide tables with nested/repeated fields (`STRUCT`, `ARRAY`) rather than many small tables with complex JOINs.
*   **Order of Tables**: In JOINs, place the largest table first (distributed) and smaller tables second (broadcast).

---

## 🤖 5. Machine Learning (BigQuery ML)

We can build and deploy ML models using **Standard SQL** inside BigQuery. No Python/Pandas required.

### Example Workflow (`big_query_ml.sql`)
1.  **Feature Selection**:
    ```sql
    SELECT passenger_count, trip_distance, ... FROM ...
    ```
2.  **Create Model**:
    ```sql
    CREATE OR REPLACE MODEL `nytaxi.tip_model`
    OPTIONS (model_type='linear_reg', input_label_cols=['tip_amount'], ...) AS
    SELECT * FROM features_table;
    ```
3.  **Evaluate**:
    ```sql
    SELECT * FROM ML.EVALUATE(MODEL `nytaxi.tip_model`, (SELECT * FROM validation_data));
    ```
4.  **Predict**:
    ```sql
    SELECT * FROM ML.PREDICT(MODEL `nytaxi.tip_model`, (SELECT * FROM new_data));
    ```

### Supported Models
Linear Regression, Logistic Regression, K-Means Clustering, Matrix Factorization (Recommendations), Time Series (ARIMA), and even TensorFlow imports.
