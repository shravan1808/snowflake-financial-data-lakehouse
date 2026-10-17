# Snowflake Financial Data Lakehouse

**An end-to-end data engineering project using Snowflake, SQL, incremental data processing, data quality auditing, and Streamlit dashboards.**

[**Launch Live Dashboard**](https://app.snowflake.com/streamlit/aarcadm/hz40948/#/apps/qiyut6u5zjt32xsc532f)

## Project Overview

The Snowflake Financial Data Lakehouse is an end-to-end data engineering project built using synthetic financial transaction data from PaySim.

The project demonstrates batch ingestion, raw and curated data layers, analytical transformations, incremental processing with Snowflake Streams and Tasks, file-ingestion auditing, and interactive financial analytics through a four-page Streamlit dashboard.

The solution follows a medallion-style architecture with separate Bronze, Silver, Gold, and Audit schemas.

## Live Demo

**Application:** [Open the Financial Data Lakehouse Dashboard](https://app.snowflake.com/streamlit/aarcadm/hz40948/#/apps/qiyut6u5zjt32xsc532f)

The application is hosted on Snowflake. Viewers must sign in and have the appropriate Snowflake permissions to access it.

## Business Objectives

- Build a scalable financial transaction data pipeline using Snowflake.
- Ingest large CSV datasets using stages, file formats, and `COPY INTO`.
- Separate raw, curated, and analytical data using medallion architecture.
- Perform data-quality checks and identify potential data issues.
- Implement incremental processing using Snowflake Streams and Tasks.
- Create Gold-layer transaction and fraud analytics.
- Reconcile file-ingestion audit records with Snowflake load metadata.
- Monitor pipeline execution and data quality.
- Present transaction analytics through an interactive Streamlit dashboard.

## Technology Stack

| Technology | Purpose |
|---|---|
| Snowflake | Cloud data platform and SQL processing |
| Snowflake SQL | Data ingestion, transformation, validation, and analytics |
| Snowflake Stages | CSV file staging |
| `COPY INTO` | Bulk data ingestion |
| Streams | Tracking source-table changes |
| Tasks | Conditional scheduled processing |
| Python | Dataset profiling and supporting development |
| Streamlit | Interactive analytics dashboard |
| Git and GitHub | Version control and project documentation |

## Dataset

**Source:** [PaySim Synthetic Financial Dataset](https://www.kaggle.com/datasets/ealaxi/paysim1)

PaySim provides synthetic financial transactions for transaction and fraud-analysis exercises.

Important fields used in this project include:

- `STEP` — simulation time step
- `TYPE` — transaction type
- `AMOUNT` — transaction amount
- `NAMEORIG` — origin account identifier
- `OLDBALORIG` and `NEWBALORIG` — origin balances before and after a transaction
- `NAMEDEST` — destination account identifier
- `OLDBALDEST` and `NEWBALDEST` — destination balances before and after a transaction
- `ISFRAUD` — source fraud label
- `ISFLAGGEDFRAUD` — source flag for potentially suspicious transactions

The raw dataset and generated batch files are excluded from the repository to avoid committing large data files.

**Note:** PaySim fraud labels are synthetic dataset labels, not proof of real-world fraud-detection performance.

## Architecture

```text
                 PaySim CSV Dataset
                         |
                         v
              Local Profiling and Batching
                         |
                         v
              Snowflake Stage and File Format
                         |
                         v
                     COPY INTO
                         |
                         v
              +----------------------+
              |     BRONZE_RAW       |
              |   Raw Transactions   |
              +----------------------+
                         |
                         v
              +----------------------+
              |   SILVER_CURATED     |
              | Curated Transactions |
              | Data Quality Checks  |
              +----------------------+
                         ^
                         |
                 Snowflake Stream
                         |
                 Conditional Task
                         |
                         v
              +----------------------+
              |    GOLD_ANALYTICS    |
              | Transaction Summary  |
              | Fraud Analytics      |
              | Step Analytics       |
              +----------------------+
                         |
                         v
                 Streamlit Dashboard

              +----------------------+
              |         AUDIT        |
              | File Load Audit Log  |
              | Task Execution View  |
              | Reconciliation       |
              +----------------------+
```

## Snowflake Database Design

**Database:** `FINANCIAL_LAKEHOUSE_DB`

| Schema | Responsibility |
|---|---|
| `BRONZE_RAW` | Raw transaction table, file stage, Stream, and processing Task |
| `SILVER_CURATED` | Curated transaction data and validation |
| `GOLD_ANALYTICS` | Transaction, fraud, and step-level summaries |
| `AUDIT` | File-ingestion audit records and monitoring objects |

### Key objects

| Object | Purpose |
|---|---|
| `BRONZE_RAW.RAW_BRONZE_TABLE` | Stores raw transactions |
| `BRONZE_RAW.RAW_STAGE` | Stage for source files |
| `BRONZE_RAW.RAW_BRONZE_STREAM` | Tracks changes to the Bronze table |
| `BRONZE_RAW.PROCESS_BRONZE_STREAM_TASK` | Processes available stream changes |
| `SILVER_CURATED.TRANSACTIONS_CLEAN` | Stores curated transaction records |
| `GOLD_ANALYTICS.GOLD_TRANSACTION_SUMMARY` | Transaction-level aggregates by type |
| `GOLD_ANALYTICS.GOLD_FRAUD_ANALYTICS` | Fraud-related analytical summaries |
| `GOLD_ANALYTICS.GOLD_STEP_ANALYTICS` | Step-level transaction summaries |
| `AUDIT.BATCH_AUDIT_LOG` | Records file-ingestion audit information |
| `AUDIT.VW_TASK_EXECUTION_AUDIT` | Exposes recent task execution history |

## Data Pipeline

### 1. Bronze ingestion

CSV batches are uploaded to a Snowflake stage and loaded into the Bronze table using `COPY INTO`. Snowflake load metadata is used to validate file status and loaded row counts.

### 2. Silver transformation and validation

The Silver layer contains curated transaction data. Validation checks inspect missing values, invalid labels, negative amounts, and repeated transaction signatures.

### 3. Incremental processing

A Snowflake Stream tracks changes to the Bronze table. A scheduled Task uses `SYSTEM$STREAM_HAS_DATA` to determine whether processing is required.

A task state of `SKIPPED` can be expected when the condition evaluates to false; it does not automatically indicate a pipeline failure.

### 4. Gold analytics

The Gold layer contains three analytical tables supporting transaction summaries, fraud analysis, and step-level reporting.

Gold metrics should be revalidated or refreshed when underlying data changes. Automatic refresh should not be assumed unless explicitly configured.

## Audit and Monitoring

The audit implementation provides operational visibility through the following mechanisms:

- **File-ingestion auditing:** batch name, process, timestamps, status, rows processed, and error details.
- **Load-history reconciliation:** compares file audit records with Snowflake `LOAD_HISTORY`.
- **Task monitoring:** inspects task states, timestamps, error messages, and query IDs.
- **Layer reconciliation:** compares Bronze and Silver row counts.
- **Data-quality checks:** checks nulls, invalid fraud labels, negative amounts, and repeated transaction signatures.
- **Gold monitoring:** reports row counts for the analytical tables.
- **Stream monitoring:** inspects stream metadata and pending stream records.

The `BATCH_AUDIT_LOG` table and `VW_TASK_EXECUTION_AUDIT` view have different purposes. The former records file-ingestion events; the latter exposes Snowflake task execution history.

## Streamlit Dashboard

The deployed dashboard has four pages for business analytics and pipeline monitoring.

### 1. Executive Overview

Presents high-level financial transaction metrics and summary charts.

![Executive Overview](docs/screenshots/executive-overview.png)

### 2. Fraud Analytics

Explores source fraud labels, fraud-related metrics, and transaction patterns.

![Fraud Analytics](docs/screenshots/fraud-analytics.png)

![Fraud Analytics — Additional View](docs/screenshots/fraud-analytics-details.png)

### 3. Transaction Explorer

Supports transaction-level exploration using the available transaction data and filters.

![Transaction Explorer](docs/screenshots/transaction-explorer.png)

### 4. Pipeline Monitor

Displays operational monitoring information, including audit records, task history, and data-quality or reconciliation results.

![Pipeline Monitor](docs/screenshots/pipeline-monitor.png)

![Pipeline Monitor — Additional View](docs/screenshots/pipeline-monitor-details.png)

**Screenshot note:** Replace the example paths above with the exact filenames of your six saved screenshots. The images must be committed to the repository for GitHub to display them.

## Repository Structure

```text
Snowflake-Financial-Data-Lakehouse/
│
├── notebooks/
│   └── 01_paysim_dataset_profiling.ipynb
│
├── sql/
│   ├── 01_create_database_and_schemas.sql
│   ├── 02_bronze_ingestion_setup.sql
│   ├── 03_bronze_data_validation.sql
│   ├── 04_silver_data_quality_checks.sql
│   ├── 05_silver_layer.sql
│   ├── 06_incremental_processing.sql
│   ├── 07_gold_analytics.sql
│   └── 08_audit_and_monitoring.sql
│
├── streamlit/
│   └── streamlit_app.py/
│       ├── .streamlit/
│       ├── app_pages/
│       │   ├── 1_Executive_Overview.py
│       │   ├── 2_Fraud_Analytics.py
│       │   ├── 3_Transaction_Explorer.py
│       │   └── 4_Pipeline_Monitor.py
│       ├── pyproject.toml
│       ├── snowflake.yml
│       └── streamlit_app.py
│
├── docs/
│   └── screenshots/
│       ├── executive-overview.png
│       ├── fraud-analytics.png
│       ├── fraud-analytics-details.png
│       ├── transaction-explorer.png
│       ├── pipeline-monitor.png
│       └── pipeline-monitor-details.png
│
├── .gitignore
├── PROJECT_IMPLEMENTATION_GUIDE.md
└── README.md
```

## Validation Results

The observed file-ingestion audit was reconciled against Snowflake load metadata.

| Validation | Observed result |
|---|---|
| File batches represented in the audit | 4 |
| Total rows across the four batches | 6,362,620 |
| File load statuses | All four reported `LOADED` |
| Audit versus load-history row counts | Matched for all four batches |
| Stream and Task | Implemented and inspected through task history |
| Streamlit dashboard | Four pages opened successfully |

These results confirm the observed ingestion and dashboard checks. They do not independently prove that all individual transactions are correct or that every Gold metric is synchronized with the latest Silver data.

Record any additional validation results only after confirming them in Snowflake.

## How to Run and Review

1. Open the Snowflake environment and select the project database.
2. Configure the warehouse, file format, and stage.
3. Upload the PaySim batch files.
4. Execute the SQL scripts in the appropriate order.
5. Validate Bronze ingestion and Silver data quality.
6. Review incremental Stream and Task processing.
7. Validate the Gold analytical tables.
8. Execute `08_audit_and_monitoring.sql` and inspect the results.
9. Open the deployed Streamlit application using the [Live Dashboard link](https://app.snowflake.com/streamlit/aarcadm/hz40948/#/apps/qiyut6u5zjt32xsc532f).

Access to the deployed application requires the appropriate Snowflake permissions.

## Security and Cost Considerations

- Never commit passwords, private keys, access tokens, or credential-bearing configuration.
- Keep large raw CSV files and generated batch files out of version control.
- Use appropriate secret-management and Snowflake connection settings.
- Apply least-privilege access where applicable.
- Monitor warehouse usage and avoid unnecessary compute consumption.
- Validate row counts and sample records before replacing or rerunning transformations.
- Treat source fraud labels as synthetic analytical inputs.

## Limitations and Future Improvements

Potential future improvements include:

- Persisting every pipeline execution in a structured audit table.
- Implementing stored-procedure-based processing with structured error handling.
- Automating Gold refresh orchestration.
- Adding historical data-quality results and alerts.
- Implementing and validating role-based access and masking policies.
- Performing query-profile and performance comparisons.
- Adding automated tests and continuous integration.

These are potential extensions, not claims that they are already implemented.

## License

Choose a license appropriate for your own code and review the PaySim dataset's source terms separately. A license applied to this repository does not override the dataset provider's terms.
