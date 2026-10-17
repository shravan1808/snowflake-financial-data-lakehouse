
-- ============================================================
-- PROJECT: Snowflake Financial Data Lakehouse
-- FILE: 08_audit_and_monitoring.sql
-- PURPOSE: File audit, task monitoring, data quality and
--          Bronze / Silver / Gold reconciliation
--
-- IMPORTANT:
-- 1. Does not recreate or replace existing tables.
-- 2. Does not insert duplicate historical file audit records.
-- 3. Does not resume or modify the existing processing task.
-- ============================================================


-- ------------------------------------------------------------
-- SECTION 1: SET PROJECT CONTEXT
-- ------------------------------------------------------------

USE DATABASE FINANCIAL_LAKEHOUSE_DB;
USE SCHEMA AUDIT;

-- Check the current project objects.
SHOW TABLES IN SCHEMA FINANCIAL_LAKEHOUSE_DB.AUDIT;

SHOW TABLES IN SCHEMA FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW;

SHOW TABLES IN SCHEMA FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED;

SHOW TABLES IN SCHEMA FINANCIAL_LAKEHOUSE_DB.GOLD_ANALYTICS;


-- ------------------------------------------------------------
-- SECTION 2: VERIFY THE EXISTING AUDIT TABLE
-- ------------------------------------------------------------

-- Preserve the existing BATCH_AUDIT_LOG table.
-- Do not run CREATE OR REPLACE TABLE here.

SELECT
    AUDIT_ID,
    BATCH_NAME,
    PROCESS_NAME,
    START_TIME,
    END_TIME,
    STATUS,
    ROWS_PROCESSED,
    ERROR_MESSAGE,
    INSERTED_AT
FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
ORDER BY AUDIT_ID;


-- ------------------------------------------------------------
-- SECTION 3: FILE INGESTION AUDIT SUMMARY
-- ------------------------------------------------------------

SELECT
    PROCESS_NAME,
    STATUS,
    COUNT(*) AS BATCH_COUNT,
    SUM(COALESCE(ROWS_PROCESSED, 0)) AS TOTAL_ROWS_PROCESSED,
    MIN(START_TIME) AS FIRST_START_TIME,
    MAX(END_TIME) AS LAST_END_TIME,
    COUNT_IF(ERROR_MESSAGE IS NOT NULL) AS BATCHES_WITH_ERRORS
FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
GROUP BY PROCESS_NAME, STATUS
ORDER BY PROCESS_NAME, STATUS;


-- ------------------------------------------------------------
-- SECTION 4: RECONCILE AUDIT RECORDS WITH SNOWFLAKE
--            LOAD HISTORY
-- ------------------------------------------------------------

-- Match file names against Snowflake's load metadata.
-- LOAD_HISTORY is metadata about file loading, not the
-- downstream Silver/Gold transformation status.

WITH LOAD_HISTORY AS
(
    SELECT
        SPLIT_PART(FILE_NAME, '/', -1) AS FILE_NAME,
        STATUS AS LOAD_STATUS,
        ROW_COUNT AS LOAD_ROWS,
        ROW_PARSED,
        FIRST_ERROR_MESSAGE,
        LAST_LOAD_TIME
    FROM FINANCIAL_LAKEHOUSE_DB.INFORMATION_SCHEMA.LOAD_HISTORY
    WHERE SCHEMA_NAME = 'BRONZE_RAW'
      AND TABLE_NAME = 'RAW_BRONZE_TABLE'
)
SELECT
    A.AUDIT_ID,
    A.BATCH_NAME,
    A.STATUS AS AUDIT_STATUS,
    A.ROWS_PROCESSED AS AUDIT_ROWS,
    H.LOAD_STATUS,
    H.LOAD_ROWS,
    H.ROW_PARSED,
    H.LAST_LOAD_TIME,
    CASE
        WHEN H.FILE_NAME IS NULL
            THEN 'NOT FOUND IN LOAD HISTORY'
        WHEN A.ROWS_PROCESSED = H.LOAD_ROWS
            THEN 'MATCH'
        ELSE 'ROW COUNT MISMATCH'
    END AS RECONCILIATION_STATUS
FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG A
LEFT JOIN LOAD_HISTORY H
    ON A.BATCH_NAME = H.FILE_NAME
WHERE A.PROCESS_NAME = 'BRONZE_INGESTION'
ORDER BY A.AUDIT_ID;


-- ------------------------------------------------------------
-- SECTION 5: CURRENT BRONZE / SILVER ROW COUNTS
-- ------------------------------------------------------------

SELECT
    'BRONZE_RAW_TABLE' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE

UNION ALL

SELECT
    'TRANSACTIONS_CLEAN' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;


-- ------------------------------------------------------------
-- SECTION 6: BRONZE / SILVER ROW COUNT RECONCILIATION
-- ------------------------------------------------------------

WITH LAYER_COUNTS AS
(
    SELECT
        (
            SELECT COUNT(*)
            FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
        ) AS BRONZE_COUNT,
        (
            SELECT COUNT(*)
            FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
        ) AS SILVER_COUNT
)
SELECT
    BRONZE_COUNT,
    SILVER_COUNT,
    BRONZE_COUNT - SILVER_COUNT AS ROW_COUNT_DIFFERENCE,
    CASE
        WHEN BRONZE_COUNT = SILVER_COUNT THEN 'MATCH'
        ELSE 'REVIEW REQUIRED'
    END AS RECONCILIATION_STATUS
FROM LAYER_COUNTS;


-- ------------------------------------------------------------
-- SECTION 7: GOLD TABLE ROW COUNTS
-- ------------------------------------------------------------

SELECT
    'GOLD_TRANSACTION_SUMMARY' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.GOLD_ANALYTICS.GOLD_TRANSACTION_SUMMARY

UNION ALL

SELECT
    'GOLD_FRAUD_ANALYTICS' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.GOLD_ANALYTICS.GOLD_FRAUD_ANALYTICS

UNION ALL

SELECT
    'GOLD_STEP_ANALYTICS' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.GOLD_ANALYTICS.GOLD_STEP_ANALYTICS;


-- ------------------------------------------------------------
-- SECTION 8: SILVER DATA QUALITY CHECKS
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS TOTAL_ROWS,

    COUNT_IF(STEP IS NULL) AS NULL_STEP_ROWS,

    COUNT_IF(TYPE IS NULL) AS NULL_TYPE_ROWS,

    COUNT_IF(AMOUNT IS NULL) AS NULL_AMOUNT_ROWS,

    COUNT_IF(NAMEORIG IS NULL) AS NULL_ORIGIN_ROWS,

    COUNT_IF(NAMEDEST IS NULL) AS NULL_DESTINATION_ROWS,

    COUNT_IF(ISFRAUD IS NULL) AS NULL_FRAUD_LABEL_ROWS,

    COUNT_IF(AMOUNT < 0) AS NEGATIVE_AMOUNT_ROWS,

    COUNT_IF(ISFRAUD NOT IN (0, 1)) AS INVALID_FRAUD_LABEL_ROWS,

    COUNT_IF(
        ISFLAGGEDFRAUD IS NOT NULL
        AND ISFLAGGEDFRAUD NOT IN (0, 1)
    ) AS INVALID_FLAGGED_FRAUD_ROWS

FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;


-- ------------------------------------------------------------
-- SECTION 9: FRAUD DISTRIBUTION IN SILVER
-- ------------------------------------------------------------

SELECT
    ISFRAUD,
    COUNT(*) AS TRANSACTION_COUNT,
    SUM(AMOUNT) AS TOTAL_TRANSACTION_AMOUNT,
    ROUND(
        100.0 * COUNT(*) /
        NULLIF(
            (SELECT COUNT(*)
             FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN),
            0
        ),
        4
    ) AS PERCENT_OF_TRANSACTIONS
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
GROUP BY ISFRAUD
ORDER BY ISFRAUD;


-- ------------------------------------------------------------
-- SECTION 10: DUPLICATE SIGNATURE CHECK IN SILVER
-- ------------------------------------------------------------

-- This checks duplicate combinations of transaction attributes.
-- It is a duplicate-signature check, not proof that a row is
-- an accidental duplicate: legitimate transactions can share
-- the same values.

SELECT
    COUNT(*) AS TOTAL_ROWS,
    COUNT(DISTINCT HASH(
        STEP,
        TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALORIG,
        NEWBALORIG,
        NAMEDEST,
        OLDBALDEST,
        NEWBALDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD
    )) AS DISTINCT_ROW_SIGNATURES,
    COUNT(*) - COUNT(DISTINCT HASH(
        STEP,
        TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALORIG,
        NEWBALORIG,
        NAMEDEST,
        OLDBALDEST,
        NEWBALDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD
    )) AS REPEATED_SIGNATURE_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;


-- ------------------------------------------------------------
-- SECTION 11: TASK EXECUTION HISTORY
-- ------------------------------------------------------------

-- Snowflake task history is the authoritative execution record
-- for the existing stream-processing task.
-- SKIPPED can be expected when the stream has no pending data.

SELECT
    NAME AS TASK_NAME,
    STATE,
    SCHEDULED_TIME,
    QUERY_START_TIME,
    COMPLETED_TIME,
    ERROR_CODE,
    ERROR_MESSAGE,
    QUERY_ID
FROM TABLE(
    FINANCIAL_LAKEHOUSE_DB.INFORMATION_SCHEMA.TASK_HISTORY(
        SCHEDULED_TIME_RANGE_START =>
            DATEADD('DAY', -7, CURRENT_TIMESTAMP()),
        RESULT_LIMIT => 100
    )
)
WHERE NAME = 'PROCESS_BRONZE_STREAM_TASK'
ORDER BY SCHEDULED_TIME DESC;


-- ------------------------------------------------------------
-- SECTION 12: CREATE A TASK MONITORING VIEW
-- ------------------------------------------------------------

-- This view does not modify the existing task or data tables.
-- It provides a reusable task execution history for monitoring.

CREATE OR REPLACE VIEW
    FINANCIAL_LAKEHOUSE_DB.AUDIT.VW_TASK_EXECUTION_AUDIT
AS
SELECT
    NAME AS TASK_NAME,
    STATE AS EXECUTION_STATUS,
    SCHEDULED_TIME,
    QUERY_START_TIME,
    COMPLETED_TIME,
    ERROR_CODE,
    ERROR_MESSAGE,
    QUERY_ID,
    CASE
        WHEN STATE = 'SUCCEEDED' THEN 'SUCCESS'
        WHEN STATE = 'FAILED' THEN 'FAILURE'
        WHEN STATE = 'SKIPPED' THEN 'SKIPPED'
        ELSE 'OTHER'
    END AS AUDIT_RESULT
FROM TABLE(
    FINANCIAL_LAKEHOUSE_DB.INFORMATION_SCHEMA.TASK_HISTORY(
        SCHEDULED_TIME_RANGE_START =>
            DATEADD('DAY', -7, CURRENT_TIMESTAMP()),
        RESULT_LIMIT => 100
    )
)
WHERE NAME = 'PROCESS_BRONZE_STREAM_TASK';


-- Verify the view.
SELECT *
FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.VW_TASK_EXECUTION_AUDIT
ORDER BY SCHEDULED_TIME DESC;


-- ------------------------------------------------------------
-- SECTION 13: STREAM STATUS
-- ------------------------------------------------------------

-- Shows stream metadata, including whether it may have data.
SHOW STREAMS IN SCHEMA FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW;

-- A SELECT from a stream reads its current change records but
-- does not itself consume/advance the stream offset.

SELECT COUNT(*) AS STREAM_RECORDS_PENDING
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM;


-- ------------------------------------------------------------
-- SECTION 14: FINAL AUDIT DASHBOARD QUERY
-- ------------------------------------------------------------

-- One-row operational snapshot for quick checks.

SELECT
    CURRENT_TIMESTAMP() AS AUDIT_CHECK_TIME,

    (
        SELECT COUNT(*)
        FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
    ) AS BRONZE_ROWS,

    (
        SELECT COUNT(*)
        FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
    ) AS SILVER_ROWS,

    (
        SELECT COUNT(*)
        FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
    ) AS FILE_AUDIT_RECORDS,

    (
        SELECT COUNT_IF(STATUS = 'SUCCESS')
        FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
    ) AS SUCCESSFUL_FILE_BATCHES,

    (
        SELECT COUNT_IF(STATUS = 'FAILED')
        FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
    ) AS FAILED_FILE_BATCHES,

    (
        SELECT COUNT_IF(STATUS = 'RUNNING')
        FROM FINANCIAL_LAKEHOUSE_DB.AUDIT.BATCH_AUDIT_LOG
    ) AS RUNNING_FILE_BATCHES;


-- ============================================================
-- END OF AUDIT SCRIPT
-- ============================================================
