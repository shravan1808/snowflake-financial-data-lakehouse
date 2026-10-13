# Snowflake Financial Data Lakehouse

**End-to-end Snowflake data engineering, incremental CDC, analytics,
governance, and Streamlit dashboards**

## Project overview

This project builds a financial transaction data platform on Snowflake
using a medallion-style architecture. It starts with a publicly
available synthetic financial transaction dataset, loads it into a raw
layer, transforms and validates it, processes later batches
incrementally, and produces analytics for an interactive Streamlit
dashboard.

The project will be developed incrementally. Database objects, code
folders, validation queries, documentation, and screenshots will be
added as each phase is implemented and tested.

## Goals

-   Load and profile a large transaction dataset.
-   Build Bronze, Silver, Gold, and Audit schemas.
-   Validate data quality and manage duplicate records.
-   Simulate recurring ingestion by splitting the source into sequential
    batches.
-   Implement Snowflake Streams, `MERGE`, UDFs, stored procedures, and
    Tasks.
-   Practice Time Travel, zero-copy cloning, Search Optimization,
    clustering, and materialized views.
-   Implement role-based access and masking for synthetic sensitive
    fields.
-   Build analytical fact/dimension models and KPI tables.
-   Use Python Connector and Snowpark Python where appropriate.
-   Explore Snowflake Cortex for suitable text analysis and vector
    similarity if the account supports it.
-   Build a Streamlit dashboard for transaction, risk/fraud, and
    pipeline monitoring.
-   Document correctness, performance, and cost considerations.

## Dataset

**Planned source:** PaySim synthetic financial transaction dataset.

-   Dataset page: https://www.kaggle.com/datasets/ealaxi/paysim1
-   The dataset is synthetic and intended for financial
    transaction/fraud-analysis exercises.
-   The original source includes fields such as transaction step,
    transaction type, amount, origin/destination identifiers, balances,
    and fraud indicators. The exact downloaded file, headers, row count,
    and null profile must be inspected before the table design is
    finalized.
-   Kaggle access may require an account.
-   The full raw CSV will not be committed to this GitHub repository.
    Download it separately and follow the implementation guide.

### Data mapping policy

Preserve original source fields in the raw layer. Any additional fields
needed for the generalized business model---such as display names,
regions, statuses, PAN-like values, or feedback text---must be
documented as **synthetic derived fields**. Do not present them as
original PaySim data.

Final mappings will be chosen only after inspecting the actual
downloaded dataset. Fraud labels in a synthetic dataset are dataset
labels, not proof of real-world fraud detection capability.

## Architecture

``` text
PaySim CSV
   |
   v
Local profiling and batch preparation
   |
   v
Snowflake ingestion (stage, file format, COPY INTO)
   |
   v
BRONZE_RAW -- source-aligned raw data
   |
   v
SILVER_CURATED -- validated, deduplicated, transformed data
   |                 ^
   |                 |
   |            Streams + MERGE + stored procedures
   |                 ^
   |                 |
   |            Later CSV batches
   v
GOLD_ANALYTICS -- fact/dimension models, KPI tables, aggregates
   |
   v
Streamlit dashboard

AUDIT -- ingestion, task, quality, and operational records
```

Initial loading and ongoing CDC are separate processes:

1.  Load the initial batch into Bronze.
2.  Validate the initial load and populate Silver.
3.  Create a Stream at the chosen CDC starting point.
4.  Load subsequent batches into Bronze.
5.  Process captured changes into Silver using a controlled `MERGE`.
6.  Refresh Gold analytics through tasks or a deliberate refresh
    process.

A Stream does not repeatedly read the original CSV. It tracks changes to
its source table from its offset.

## Planned Snowflake layout

Database: `FINANCIAL_LAKEHOUSE_DB`

-   `BRONZE_RAW` --- raw source-aligned data and ingestion objects.
-   `SILVER_CURATED` --- validated and transformed transactions, risk
    features, and CDC targets.
-   `GOLD_ANALYTICS` --- fact/dimension tables, KPI summaries, and
    analytical aggregates.
-   `AUDIT` --- load logs, task history extracts, pipeline run records,
    and data-quality results.

Actual object names and placement will be finalized as the project is
implemented.

## Implementation phases

1.  **Dataset profiling and ingestion:** inspect the CSV, profile data,
    create repeatable batches, configure Snowflake ingestion, and
    validate counts.
2.  **Medallion foundation and data quality:** create layers,
    transformations, validation rules, and deduplication.
3.  **Incremental CDC:** establish streams, risk UDFs, stored
    procedures, and `MERGE` logic; test with later batches.
4.  **Snowflake advanced features:** Time Travel, zero-copy cloning,
    Search Optimization, clustering, materialized views, RBAC, masking,
    and cost-aware performance checks.
5.  **Orchestration and Python:** task DAGs, task history, Python
    Connector, and Snowpark feature engineering.
6.  **Gold analytics:** fact/dimension modeling, KPI definitions, and
    aggregate tables.
7.  **Cortex and optional AI enrichment:** use supported Cortex
    functions for suitable text data and vector search, if enabled and
    applicable.
8.  **Streamlit showcase:** connect to Snowflake, build dashboards, and
    document results.

See [`PROJECT_IMPLEMENTATION_GUIDE.md`](PROJECT_IMPLEMENTATION_GUIDE.md)
for the task-by-task plan and validation checklist.

## Repository development approach

Folders and files will be created only when needed for the phase being
implemented. The repository will grow with tested code rather than being
populated with empty scripts upfront.

Each task should include the purpose, implementation, validation query
or test, observed result, and notes about limitations, permissions, and
cost where relevant.

## Security and repository hygiene

-   Never commit Snowflake passwords, private keys, access tokens,
    `.env` files, or credential-bearing connection configuration.
-   Do not commit the full raw CSV or generated multi-million-row batch
    files.
-   Keep local data outside version control and use `.gitignore`.
-   Commit reusable SQL, Python code, data dictionaries, non-sensitive
    test samples, and sanitized screenshots.
-   Use least-privilege roles for normal development and reserve
    administrative roles for setup operations.
-   Test masking and access controls with the intended roles.

## Important implementation notes

-   The exact source schema and row count are not assumed; they will be
    recorded after profiling the downloaded file.
-   Search Optimization, clustering, and materialized views have
    different purposes and may add cost. Test their value with
    representative queries.
-   Task scheduling and Streams must be tested with captured table
    changes.
-   A successful stored-procedure return string does not prove rows were
    inserted; validate target data and row counts.
-   Resource Monitor behavior and account-level features depend on
    Snowflake edition, privileges, and configuration.
-   Cortex functions and model availability depend on account region,
    privileges, and current Snowflake support.

## Current status

**Planning stage.** The repository name and high-level architecture are
proposed. The first implementation task is to inspect the downloaded CSV
and confirm its actual schema, row count, and quality profile before
creating Snowflake tables.

## License

Choose a license appropriate for your own code (for example, MIT) and
review the source dataset's terms separately. A license applied to this
repository does not override the dataset provider's terms.
