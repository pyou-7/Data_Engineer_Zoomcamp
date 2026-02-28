import sys

yaml_content = """id: week4_load_taxi_data
namespace: zoomcamp
description: |
  Loads Yellow and Green taxi data for 2019 and 2020.
  Uses Week 3 approach: Uploads all CSVs to GCS, creates external tables, 
  and then creates partitioned tables in BigQuery.

tasks:
  - id: for_each_file
    type: io.kestra.plugin.core.flow.ForEach
    concurrencyLimit: 4
    values:
"""

for taxi in ["yellow", "green"]:
    for year in ["2019", "2020"]:
        for month in range(1, 13):
            yaml_content += f"      - {taxi}_{year}-{month:02d}\n"

yaml_content += """
    tasks:
      - id: extract
        type: io.kestra.plugin.scripts.shell.Commands
        outputFiles:
          - "*.csv"
        taskRunner:
          type: io.kestra.plugin.core.runner.Process
        commands:
          - "wget -qO- https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{(taskrun.value | split('_'))[0]}}/{{(taskrun.value | split('_'))[0]}}_tripdata_{{(taskrun.value | split('_'))[1]}}.csv.gz | gunzip > {{taskrun.value}}.csv"
      
      - id: upload_to_gcs
        type: io.kestra.plugin.gcp.gcs.Upload
        from: "{{outputs.extract[taskrun.value].outputFiles[taskrun.value ~ '.csv']}}"
        to: "gs://{{kv('GCP_BUCKET_NAME')}}/raw/{{(taskrun.value | split('_'))[0]}}_tripdata_{{(taskrun.value | split('_'))[1]}}.csv"

  - id: bq_yellow_external
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE OR REPLACE EXTERNAL TABLE `{{kv('GCP_PROJECT_ID')}}.nytaxi.yellow_tripdata_ext`
      (
          VendorID STRING,
          tpep_pickup_datetime TIMESTAMP,
          tpep_dropoff_datetime TIMESTAMP,
          passenger_count INTEGER,
          trip_distance NUMERIC,
          RatecodeID STRING,
          store_and_fwd_flag STRING,
          PULocationID STRING,
          DOLocationID STRING,
          payment_type INTEGER,
          fare_amount NUMERIC,
          extra NUMERIC,
          mta_tax NUMERIC,
          tip_amount NUMERIC,
          tolls_amount NUMERIC,
          improvement_surcharge NUMERIC,
          total_amount NUMERIC,
          congestion_surcharge NUMERIC
      )
      OPTIONS (
          format = 'CSV',
          uris = ['gs://{{kv('GCP_BUCKET_NAME')}}/raw/yellow_tripdata_2019-*.csv', 'gs://{{kv('GCP_BUCKET_NAME')}}/raw/yellow_tripdata_2020-*.csv'],
          skip_leading_rows = 1,
          ignore_unknown_values = TRUE
      );

  - id: bq_yellow_partitioned
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE OR REPLACE TABLE `{{kv('GCP_PROJECT_ID')}}.nytaxi.yellow_tripdata`
      PARTITION BY DATE(tpep_pickup_datetime)
      AS
      SELECT * FROM `{{kv('GCP_PROJECT_ID')}}.nytaxi.yellow_tripdata_ext`;

  - id: bq_green_external
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE OR REPLACE EXTERNAL TABLE `{{kv('GCP_PROJECT_ID')}}.nytaxi.green_tripdata_ext`
      (
          VendorID STRING,
          lpep_pickup_datetime TIMESTAMP,
          lpep_dropoff_datetime TIMESTAMP,
          store_and_fwd_flag STRING,
          RatecodeID STRING,
          PULocationID STRING,
          DOLocationID STRING,
          passenger_count INT64,
          trip_distance NUMERIC,
          fare_amount NUMERIC,
          extra NUMERIC,
          mta_tax NUMERIC,
          tip_amount NUMERIC,
          tolls_amount NUMERIC,
          ehail_fee NUMERIC,
          improvement_surcharge NUMERIC,
          total_amount NUMERIC,
          payment_type INTEGER,
          trip_type STRING,
          congestion_surcharge NUMERIC
      )
      OPTIONS (
          format = 'CSV',
          uris = ['gs://{{kv('GCP_BUCKET_NAME')}}/raw/green_tripdata_2019-*.csv', 'gs://{{kv('GCP_BUCKET_NAME')}}/raw/green_tripdata_2020-*.csv'],
          skip_leading_rows = 1,
          ignore_unknown_values = TRUE
      );

  - id: bq_green_partitioned
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE OR REPLACE TABLE `{{kv('GCP_PROJECT_ID')}}.nytaxi.green_tripdata`
      PARTITION BY DATE(lpep_pickup_datetime)
      AS
      SELECT * FROM `{{kv('GCP_PROJECT_ID')}}.nytaxi.green_tripdata_ext`;

  - id: purge_local_files
    type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
    description: Clean up Kestra's internal storage since we moved it all to GCS and BQ

pluginDefaults:
  - type: io.kestra.plugin.gcp
    values:
      serviceAccount: "{{secret('GCP_CREDS')}}"
      projectId: "{{kv('GCP_PROJECT_ID')}}"
      location: "{{kv('GCP_LOCATION')}}"
      bucket: "{{kv('GCP_BUCKET_NAME')}}"
"""

with open("Week4_Analytics_Engineering/Load_Yellow_Green_Taxi_Data/load_taxi_data.yaml", "w") as f:
    f.write(yaml_content)

print("Generated Week4_Analytics_Engineering/Load_Yellow_Green_Taxi_Data/load_taxi_data.yaml successfully")
