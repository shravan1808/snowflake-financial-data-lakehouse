# Project Implementation Guide

## Snowflake Financial Data Lakehouse

This guide tracks the implementation of the PaySim-based Snowflake Financial Data Lakehouse. A checked item means the work was implemented and verified based on recorded project results. Planned or unverified features remain unchecked. The current project has a working four-page Streamlit app, Bronze/Silver/Gold objects, incremental Stream processing, and a batch-ingestion audit. Some advanced features in the original plan remain future work.

## Working rules

For each task: 1. Understand the concept and why it is used. 2. Inspect the source schema and existing Snowflake objects. 3. Write the SQL/Python implementation. 4. Execute it in a controlled order. 5. Validate row counts, sample records, and expected behavior. 6. Record issues, fixes, and results. 7. Commit tested code to GitHub; never commit secrets or large raw data.

Use fully qualified object names when context could be ambiguous. Before rerunning DDL, check whether an object already exists. Avoid replacing tables containing data unless replacement is intentional.

**Implementation boundary:** This guide documents verified work and future tasks only. Do not infer that a feature exists merely because it appears in the plan. Do not change SQL or dashboard code as part of documentation updates.

------------------------------------------------------------------------

## Phase 1 --- Dataset profiling and ingestion

### Task 1.1 --- Obtain and preserve the source

-   [ ] Record the exact PaySim source filename, file size, source page, download date, and license/usage notes in project documentation.
-   [ ] Confirm the original source is preserved outside Git.
-   [ ] Record encoding and delimiter based on the actual source file.

### Task 1.2 --- Profile the CSV locally

-   [x] A PaySim profiling notebook exists at `notebooks/01_paysim_dataset_profiling.ipynb`.
-   [ ] Confirm the notebook records exact source headers, data types, row count, nulls, duplicates, ranges, transaction types, and fraud labels.
-   [ ] Publish a data dictionary and concise profiling summary based on the actual source.

**Deliverables:** profiling notebook exists; a standalone data dictionary/profiling summary still needs confirmation or completion.

### Task 1.3 --- Design sequential batches

-   [x] Four ingestion batches are represented in the audit results.
-   [x] The recorded batch counts reconcile with Snowflake load-history counts.
-   [ ] Add or verify a committed batch manifest with the splitting method, checksums if practical, and the total source-to-batch reconciliation.
-   [ ] Keep full raw data and batch files out of GitHub.

**Recorded batch results**

| Batch | Audit row count | Load-history status |
|---|---:|---|
| `batch_001.csv` | 1,059,516 | `LOADED` |
| `batch_002.csv` | 1,322,666 | `LOADED` |
| `batch_003.csv` | 1,691,468 | `LOADED` |
| `batch_004.csv` | 2,288,970 | `LOADED` |
| **Total** | **6,362,620** | **All four matched load history** |

These results verify batch ingestion reconciliation against Snowflake load history. They do **not** by themselves prove that every Bronze row has propagated to Silver and Gold.

### Task 1.4 --- Create Snowflake environment

-   [x] Create database `FINANCIAL_LAKEHOUSE_DB`.
-   [x] Create schemas `BRONZE_RAW`, `SILVER_CURATED`, `GOLD_ANALYTICS`, and `AUDIT`.
-   [x] Configure and use a Snowflake warehouse for project processing (`COMPUTE_WH` is used by the incremental task).
-   [ ] Record the final role/privilege model and account/edition constraints.

### Task 1.5 --- Configure and load the initial batch

-   [x] Use the Bronze table `FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE`.
-   [x] Use the named stage `FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE` for ingestion setup.
-   [x] Load four batches and reconcile their counts with Snowflake load history, as recorded above.
-   [ ] Preserve a run-specific record of rejected rows and validation results, if any, for every batch.
-   [ ] Reconfirm key columns, nulls, and representative records as part of a clean rerun.

**Phase 1 status:** the recorded four-batch ingestion and load-history reconciliation are complete. The source provenance, full profiling deliverables, and clean-rerun evidence still need confirmation.

------------------------------------------------------------------------

## Phase 2 --- Medallion foundation and data quality

### Task 2.1 --- Bronze design

-   [x] Bronze raw table exists: `FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE`.
-   [x] Batch audit records are compared with Snowflake load history.
-   [ ] Document the complete raw schema and any ingestion metadata columns.
-   [ ] Run and record a fresh Bronze-to-load-history reconciliation.

### Task 2.2 --- Silver transformations

-   [x] Silver curated table exists: `FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN`.
-   [x] Incremental processing is configured around a Bronze Stream and a task that inserts new stream rows into Silver.
-   [ ] Document every source-to-Silver rename, cast, derived field, and discarded field.
-   [ ] Verify and document deterministic deduplication and invalid-record handling.
-   [ ] Test repeated ingestion and replay behavior explicitly.

### Task 2.3 --- Data quality

-   [x] Data-quality checks are surfaced by the pipeline-monitoring dashboard.
-   [ ] Record the actual tested rules, expected thresholds, and observed results in a durable report.
-   [ ] Test required columns, amount ranges, allowed transaction types, duplicate behavior, and Silver reconciliation.
-   [ ] Reconcile source/Bronze/Silver counts, including any intentionally rejected records.

**Phase 2 status:** Bronze and Silver objects and dashboard-level quality checks are present. Full transformation documentation and durable evidence for all quality rules remain to be completed.

------------------------------------------------------------------------

## Phase 3 --- Incremental CDC

### Task 3.1 --- Define the CDC starting point

-   [x] Create Stream `FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM`.
-   [x] Create task `FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.PROCESS_BRONZE_STREAM_TASK`.
-   [x] The task condition uses `SYSTEM$STREAM_HAS_DATA('FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM')` and its processing statement inserts stream rows into Silver.
-   [ ] Document the initial-load/CDC boundary and Stream offset semantics.

### Task 3.2 --- Test with a later batch

-   [x] Task history has shown successful and skipped runs. A `SKIPPED` run is expected when the Stream condition is false and is not automatically a failure.
-   [ ] Record a controlled later-batch test with expected and observed Stream/Silver row changes.
-   [ ] Inspect change metadata and verify that the Stream captures the intended changes.

### Task 3.3 --- Risk UDF and procedure

-   [ ] Define and test risk thresholds and boundary behavior in a UDF.
-   [ ] Implement and validate a stored procedure for the chosen CDC logic.
-   [ ] Verify whether the current implementation uses `MERGE`; do not assume this from the existence of a Stream/task.
-   [ ] Test new rows, matched updates, duplicate source keys, and status outputs if a procedure is implemented.

### Task 3.4 --- Idempotency and replay

-   [ ] Test an empty Stream, a new transaction, a repeated batch, and an update if supported by the model.
-   [ ] Document transaction and Stream-consumption behavior and verify resulting target counts.

**Phase 3 status:** Stream-based incremental processing is implemented and task history has been observed. Full replay/idempotency coverage and the planned UDF/procedure/MERGE pattern are not marked complete without specific validation.

------------------------------------------------------------------------

## Phase 4 --- Snowflake advanced features

### Task 4.1 --- Time Travel and cloning

-   [ ] Run a controlled Time Travel test and validate historical values.
-   [ ] Create and validate a zero-copy clone for a documented use case.
-   [ ] Document retention and storage considerations.

### Task 4.2 --- Search Optimization

-   [ ] Choose a selective lookup and evaluate Search Optimization configuration, query profile, and cost.

### Task 4.3 --- Clustering

-   [ ] Identify query patterns, evaluate clustering keys, and compare query profiles/scan behavior before and after where feasible.

### Task 4.4 --- Materialized views

-   [ ] Create a supported materialized view for a justified workload and compare its results with a direct query.

### Task 4.5 --- RBAC and masking

-   [ ] Define analyst/admin roles and least-privilege grants.
-   [ ] Test a masking policy using synthetic values and the intended roles.

**Phase 4 status:** these are still planned items; do not describe them as implemented until each is tested and documented.

------------------------------------------------------------------------

## Phase 5 --- Orchestration and Python

### Task 5.1 --- Root and child Tasks

-   [ ] Implement and validate a root/child Task DAG that processes CDC and refreshes Gold analytics.
-   [x] A single incremental-processing task exists and has task-history records.
-   [ ] Confirm dependencies, activation order, privileges, and failure handling if a DAG is added.
-   [ ] Avoid duplicate KPI snapshots unless history is intentional.

### Task 5.2 --- Python Connector

-   [ ] Validate a local Python Connector workflow using credentials outside source control.
-   [ ] Query known counts/KPIs and handle exceptions and connection cleanup.

### Task 5.3 --- Snowpark

-   [ ] Build and validate a Snowpark DataFrame transformation and compare its output with SQL.

**Phase 5 status:** one Snowflake Task is present; a root/child DAG, local Python Connector workflow, and Snowpark transformation are not verified as complete.

------------------------------------------------------------------------

## Phase 6 --- Gold analytics and dimensional modeling

### Task 6.1 --- Define business questions

Examples: How do transaction volumes and amounts change over time? Which transaction types have the highest volume? What share of records are labeled fraudulent in the source? How do amounts differ between source-labeled fraud and non-fraud records? How do pipeline freshness and data quality vary across batches?

### Task 6.2 --- Design the analytical model

-   [x] Gold analytics tables exist: `GOLD_TRANSACTION_SUMMARY`, `GOLD_FRAUD_ANALYTICS`, and `GOLD_STEP_ANALYTICS` in `FINANCIAL_LAKEHOUSE_DB.GOLD_ANALYTICS`.
-   [x] The Streamlit dashboard includes executive overview and fraud analytics pages backed by Gold analytics.
-   [ ] Document table grain, metric definitions, and any derived fields.
-   [ ] Reconcile each Gold metric to a validation query over Silver and retain the observed results.
-   [ ] Add dimensions/star-schema modeling only if it is implemented and justified by the project requirements.

**Phase 6 status:** Gold analytics tables and dashboard pages exist. Formal metric definitions and a retained Silver-to-Gold reconciliation report remain outstanding.

------------------------------------------------------------------------

## Phase 7 --- Cortex and optional AI enrichment

-   [ ] Confirm Cortex functions are enabled and supported for the account/region before implementation.
-   [ ] Use appropriate text data; PaySim may not contain customer feedback.
-   [ ] If feedback analysis is desired, use clearly labeled synthetic feedback or another suitable permitted dataset.
-   [ ] Test summarization/classification on a small sample and document provenance, costs, permissions, and limitations.
-   [ ] Explore embeddings only after confirming input suitability, output types, and model availability.
-   [ ] Never present generated sentiment or synthetic feedback as original source data.

**Phase 7 status:** optional future work; not verified as implemented.

------------------------------------------------------------------------

## Phase 8 --- Streamlit dashboard

### Planned pages

-   [x] Executive overview: transaction metrics and summary views.
-   [x] Fraud analytics: fraud-related summaries and details.
-   [x] Transaction explorer: transaction-level exploration and filters.
-   [x] Pipeline monitor: load history, task history, row counts, quality checks, and audit monitoring.
-   [ ] A separate data-quality page is not part of the current four-page app unless added later.
-   [ ] Optional AI analysis page remains future work unless Cortex enrichment is implemented.

### Dashboard quality checks

-   [x] All four current pages were reported to load successfully in the deployed Streamlit app.
-   [x] The Snowflake-hosted app has been deployed; the README contains the user-provided live app URL.
-   [ ] Verify the deployed app using a non-administrator/least-privilege role where feasible.
-   [ ] Confirm no credentials are committed and setup instructions match the current app structure.
-   [ ] Add the six planned screenshots to `docs/screenshots/` and verify the paths in the README.
-   [ ] Retain evidence that dashboard KPIs match their SQL validation queries.

**Phase 8 status:** four pages are implemented, deployed, and reported working. Screenshot files and final metric-to-SQL evidence remain to be checked.

------------------------------------------------------------------------

## Phase 9 --- Audit, final validation and portfolio packaging

### Task 9.1 --- Batch audit and monitoring

-   [x] Audit table exists: `FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG`.
-   [x] Audit SQL file exists: `sql/08_audit_and_monitoring.sql`.
-   [x] View `FINANCIAL_LAKEHOUSE_DB.AUDIT.VW_TASK_EXECUTION_AUDIT` is used to expose task-history information for monitoring.
-   [x] Four batch audit counts reconcile with Snowflake load history: 6,362,620 total rows across the four batches; all four load statuses were `LOADED`.
-   [x] Historical audit rows 101–103 have `START_TIME` as `NULL` because they were synchronized from load history; batch 001's audit row includes start/end timestamps.
-   [ ] Do not claim that all task executions are written into `BATCH_AUDIT_LOG`: task history is surfaced through the view, and automatic task-run logging into the batch table has not been verified.
-   [ ] Decide whether task executions should be persisted into a separate run-audit table or continue to be read from `TASK_HISTORY`.

### Task 9.2 --- Final validation

-   [ ] Re-run the pipeline from a clean environment where practical.
-   [ ] Validate source-to-Bronze, Bronze-to-Silver, and Silver-to-Gold counts separately.
-   [ ] Verify duplicate handling, replay behavior, and task execution history.
-   [ ] Record query-performance observations and costs only when measured.

### Task 9.3 --- Portfolio packaging

-   [x] Update the main `README.md` with project architecture, implemented features, ingestion results, and the deployed app link.
-   [ ] Add the six actual screenshots under `docs/screenshots/` and verify each referenced file exists.
-   [ ] Review `.gitignore`; confirm credentials, local secrets, and large raw CSV/batch files are excluded.
-   [ ] Review the Git diff for accidental secrets, generated clutter, and unrelated changes.
-   [ ] Commit the verified final documentation and project changes to GitHub.
-   [ ] Record known limitations and future improvements without overstating implemented features.

**Phase 9 status:** batch-level load reconciliation and audit/task-history monitoring are implemented. End-to-end layer reconciliation, screenshot addition, and final GitHub hygiene/commit are still open.

------------------------------------------------------------------------

## Task tracking template

For each remaining task, record:

- **Task**
- **Purpose**
- **Objects/files created**
- **Implementation**
- **Validation query/test**
- **Expected result**
- **Observed result**
- **Issues and fixes**
- **Status:** Not started / In progress / Validated

## Current starting point

The core pipeline and four-page dashboard are already implemented. Continue with **Phase 9, Task 9.3**: add the six real dashboard screenshots to `docs/screenshots/`, verify the `.gitignore` and Git diff, then perform the final GitHub review. Before calling the project fully validated, separately test Bronze-to-Silver and Silver-to-Gold reconciliation. Keep advanced features in Phases 4, 5, and 7 marked as planned until implemented and validated.
