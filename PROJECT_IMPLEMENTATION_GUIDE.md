# Project Implementation Guide

## Snowflake Financial Data Lakehouse

This is the working plan for implementing the project task by task. It
is a checklist, not a claim that any task is already complete. Mark a
task complete only after its validation succeeds.

## Working rules

For each task: 1. Understand the concept and why it is used. 2. Inspect
the source schema and existing Snowflake objects. 3. Write the
SQL/Python implementation. 4. Execute it in a controlled order. 5.
Validate row counts, sample records, and expected behavior. 6. Record
issues, fixes, and results. 7. Commit tested code to GitHub; never
commit secrets or large raw data.

Use fully qualified object names when context could be ambiguous. Before
rerunning DDL, check whether an object already exists. Avoid replacing
tables containing data unless replacement is intentional.

------------------------------------------------------------------------

## Phase 1 --- Dataset profiling and ingestion

### Task 1.1 --- Obtain and preserve the source

-   [ ] Download PaySim: https://www.kaggle.com/datasets/ealaxi/paysim1
-   [ ] Keep an untouched copy outside Git.
-   [ ] Record exact filename, file size, source page, download date,
    and license/usage notes.
-   [ ] Confirm the file opens and identify its encoding and delimiter.

### Task 1.2 --- Profile the CSV locally

-   [ ] Record exact headers and data types.
-   [ ] Count rows without relying only on a spreadsheet application.
-   [ ] Check nulls, blank strings, duplicate rows, and duplicate
    candidate keys.
-   [ ] Inspect min/max values and distinct transaction types.
-   [ ] Inspect source time fields and fraud labels.
-   [ ] Create a data dictionary from the actual file.

**Deliverables:** `docs/data-dictionary.md`, a profiling summary, and
documented data-quality observations.

### Task 1.3 --- Design sequential batches

-   [ ] Choose a deterministic split method after profiling, such as
    source time-step ranges or stable row ranges.
-   [ ] Keep the original source unchanged.
-   [ ] Produce a small test batch first, then remaining batches.
-   [ ] Ensure batches do not overlap unless deliberately testing
    duplicate ingestion.
-   [ ] Record each batch's row count and checksum if practical.
-   [ ] Verify that batch row counts sum to the source row count.

**Deliverable:** local batch files and a batch manifest. Do not commit
full batches to GitHub.

### Task 1.4 --- Create Snowflake environment

-   [ ] Create `FINANCIAL_LAKEHOUSE_DB`.
-   [ ] Create `BRONZE_RAW`, `SILVER_CURATED`, `GOLD_ANALYTICS`, and
    `AUDIT`.
-   [ ] Create a cost-appropriate warehouse with auto-suspend and
    auto-resume.
-   [ ] Confirm current database, schema, role, and warehouse.
-   [ ] Document account/edition/privilege constraints.

### Task 1.5 --- Configure and load the initial batch

-   [ ] Create a CSV file format matching the actual file.
-   [ ] Create an internal or external stage appropriate to the
    environment.
-   [ ] Upload the first batch.
-   [ ] Use `COPY INTO` to load the Bronze table.
-   [ ] Review load results and rejected records.
-   [ ] Compare loaded row counts with the batch manifest.
-   [ ] Validate key columns, nulls, and representative records.

**Phase 1 exit criteria:** source schema and row count are documented;
the initial batch loads successfully; load results and row counts
reconcile.

------------------------------------------------------------------------

## Phase 2 --- Medallion foundation and data quality

### Task 2.1 --- Bronze design

-   [ ] Preserve original source columns and values.
-   [ ] Add ingestion metadata only where useful, such as batch ID and
    ingestion timestamp.
-   [ ] Avoid silently changing source semantics.
-   [ ] Validate raw row counts against ingestion history.

### Task 2.2 --- Silver transformations

-   [ ] Define a canonical transaction schema from the actual source
    fields.
-   [ ] Document every rename, cast, derived field, and discarded field.
-   [ ] Build repeatable transformations from Bronze to Silver.
-   [ ] Handle invalid amounts, nulls, and malformed records.
-   [ ] Use stable identifiers where available; document any generated
    ID strategy.
-   [ ] Define deterministic deduplication rules.

### Task 2.3 --- Data quality

-   [ ] Test uniqueness of the chosen transaction key.
-   [ ] Test required columns and valid amount ranges.
-   [ ] Test allowed transaction types and status mappings.
-   [ ] Reconcile source and target counts, including intentionally
    rejected records.
-   [ ] Store or export validation results.

**Phase 2 exit criteria:** transformations are repeatable, documented,
and validated.

------------------------------------------------------------------------

## Phase 3 --- Incremental CDC

### Task 3.1 --- Define the CDC starting point

-   [ ] Complete the initial Bronze load.
-   [ ] Populate initial Silver data.
-   [ ] Create a Stream on Bronze after deciding which changes should be
    captured.
-   [ ] Document the Stream offset and initial-load/CDC boundary.

### Task 3.2 --- Test with a later batch

-   [ ] Load the next CSV batch into Bronze.
-   [ ] Confirm that the Stream exposes expected new changes.
-   [ ] Inspect change metadata where applicable.
-   [ ] Remember that a Stream tracks table changes; it does not reread
    the original CSV.

### Task 3.3 --- Risk UDF and procedure

-   [ ] Define risk thresholds and boundary behavior.
-   [ ] Create and test the UDF independently.
-   [ ] Create the Silver target columns required by the procedure.
-   [ ] Implement a stored procedure using `SYSTEM$STREAM_HAS_DATA` and
    `MERGE`.
-   [ ] Match records using the chosen unique key with equality.
-   [ ] Define matched updates, new rows, and duplicate source-key
    behavior.
-   [ ] Return clear status messages.
-   [ ] Validate the return value and actual target row changes.

### Task 3.4 --- Idempotency and replay

-   [ ] Run the procedure when the Stream has no changes.
-   [ ] Test a new transaction.
-   [ ] Test an update if supported by the model.
-   [ ] Test a repeated batch and verify duplicate handling.
-   [ ] Document transaction and Stream-consumption behavior.

**Phase 3 exit criteria:** later batches are processed according to
defined rules, and counts reconcile.

------------------------------------------------------------------------

## Phase 4 --- Snowflake advanced features

### Task 4.1 --- Time Travel and cloning

-   [ ] Record a timestamp or query ID before a controlled change.
-   [ ] Perform a test update on a dedicated table or controlled subset.
-   [ ] Query the historical state.
-   [ ] Create a zero-copy clone from the intended historical point if
    supported by the chosen syntax.
-   [ ] Validate row counts and values.
-   [ ] Document retention and storage considerations.

### Task 4.2 --- Search Optimization

-   [ ] Choose a representative selective lookup, such as a transaction
    ID lookup.
-   [ ] Enable Search Optimization on the relevant column if
    appropriate.
-   [ ] Validate configuration and inspect query profiles.
-   [ ] Document cost and whether the workload is large/selective enough
    to benefit.

### Task 4.3 --- Clustering

-   [ ] Identify common filters and query patterns.
-   [ ] Select clustering keys based on those patterns.
-   [ ] Inspect clustering information and query profiles.
-   [ ] Compare performance/scan behavior before and after where
    feasible.
-   [ ] Document maintenance and credit considerations.

### Task 4.4 --- Materialized views

-   [ ] Define a useful aggregate using supported Snowflake SQL.
-   [ ] Create and validate the view.
-   [ ] Compare results to a direct aggregation.
-   [ ] Understand storage/maintenance costs and appropriate use cases.

### Task 4.5 --- RBAC and masking

-   [ ] Create analyst and administrator access patterns.
-   [ ] Grant only required privileges.
-   [ ] Apply a masking policy to an existing column.
-   [ ] Test using intended roles, not only the administrator role.
-   [ ] Use synthetic sensitive values only.

**Phase 4 exit criteria:** each feature is implemented, tested, and
documented with its purpose and trade-offs.

------------------------------------------------------------------------

## Phase 5 --- Orchestration and Python

### Task 5.1 --- Root and child Tasks

-   [ ] Create the Gold KPI target table before defining a task that
    writes to it.
-   [ ] Create a root Task that calls the CDC procedure.
-   [ ] Create a child Task that depends on the root and refreshes Gold
    analytics.
-   [ ] Confirm warehouse assignment and task privileges.
-   [ ] Resume child tasks before the root when activating the DAG.
-   [ ] Inspect task history and diagnose failed runs.
-   [ ] Prevent unintended duplicate KPI snapshots unless snapshot
    history is intentional.

### Task 5.2 --- Python Connector

-   [ ] Store credentials outside source control.
-   [ ] Connect from a local Python environment.
-   [ ] Query validated counts and KPI tables.
-   [ ] Handle exceptions and close cursors/connections reliably.
-   [ ] Provide useful operational output.

### Task 5.3 --- Snowpark

-   [ ] Create transaction features using Snowpark DataFrames.
-   [ ] Write output to a designated table.
-   [ ] Validate feature values against SQL logic.
-   [ ] Compare outputs and counts.

**Phase 5 exit criteria:** the pipeline can be triggered and monitored;
Python/Snowpark outputs reconcile with SQL results.

------------------------------------------------------------------------

## Phase 6 --- Gold analytics and dimensional modeling

### Task 6.1 --- Define business questions

Examples: - How many transactions and how much transaction value occur
over time? - Which transaction types have the highest volume? - What
proportion of transactions are labeled fraudulent in the source? - How
do amounts differ between source-labeled fraud and non-fraud records? -
How do pipeline freshness and data quality vary across batches?

### Task 6.2 --- Design the analytical model

-   [ ] Define the grain of the transaction fact table.
-   [ ] Design dimensions based on available source data.
-   [ ] Do not invent unsupported dimensions unless clearly documented
    as derived.
-   [ ] Create Gold tables and KPI summaries.
-   [ ] Reconcile Gold metrics to Silver queries.
-   [ ] Document metric definitions.

**Phase 6 exit criteria:** each KPI has a precise definition and agrees
with a validation query.

------------------------------------------------------------------------

## Phase 7 --- Cortex and optional AI enrichment

-   [ ] Confirm Cortex functions are enabled and supported for the
    account/region.
-   [ ] Use appropriate text data; PaySim may not contain customer
    feedback.
-   [ ] If feedback analysis is desired, create clearly labeled
    synthetic feedback or use another suitable permitted dataset.
-   [ ] Test summarization and classification with a small sample.
-   [ ] Explore embeddings and vector similarity after confirming
    inputs, output types, and model availability.
-   [ ] Record costs, permissions, limitations, and example results.
-   [ ] Never present generated sentiment or synthetic feedback as
    original source data.

**Phase 7 exit criteria:** a reproducible AI demonstration with
documented provenance and limitations.

------------------------------------------------------------------------

## Phase 8 --- Streamlit dashboard

### Planned pages

-   [ ] Transaction overview: counts, amounts, trends, and transaction
    types.
-   [ ] Risk/fraud analysis: source labels, amounts, and segment
    breakdowns.
-   [ ] Pipeline monitoring: latest batch, row counts, quality checks,
    and task status.
-   [ ] Data quality: nulls, duplicates, invalid records, and
    reconciliation.
-   [ ] Optional AI analysis page if Cortex enrichment is implemented.

### Dashboard quality checks

-   [ ] Use a least-privilege Snowflake role.
-   [ ] Keep credentials out of Git.
-   [ ] Define metrics in SQL or a shared testable layer.
-   [ ] Validate dashboard metrics against SQL queries.
-   [ ] Add screenshots and setup instructions.

**Phase 8 exit criteria:** the dashboard runs from documented setup
instructions and displays validated data.

------------------------------------------------------------------------

## Phase 9 --- Final validation and portfolio packaging

-   [ ] Re-run the pipeline from a clean environment where practical.
-   [ ] Validate source-to-Bronze, Bronze-to-Silver, and Silver-to-Gold
    counts.
-   [ ] Verify duplicate handling and repeated batch behavior.
-   [ ] Verify task dependencies and execution history.
-   [ ] Document query-performance observations and costs.
-   [ ] Add architecture diagrams, data dictionary, screenshots, and a
    demo walkthrough.
-   [ ] Update README with completed features only.
-   [ ] Ensure no credentials or large raw data files are committed.
-   [ ] Record known limitations and future improvements.

## Task tracking template

For each task, record: - **Task** - **Purpose** - **Objects/files
created** - **Implementation** - **Validation query/test** - **Expected
result** - **Observed result** - **Issues and fixes** - **Status:** Not
started / In progress / Validated

## Current starting point

Start with Phase 1, Task 1.1: obtain and preserve the dataset, then
inspect the exact file. Do not finalize table DDL, field mappings, or
batch boundaries until the actual file has been profiled.
