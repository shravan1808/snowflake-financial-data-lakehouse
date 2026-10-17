CREATE STREAM IF NOT EXISTS FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM
ON TABLE FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE;

SHOW STREAMS IN SCHEMA FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW;

LIST @FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE;

COPY INTO FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
FROM @FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE/batch_002.csv;

SELECT COUNT(*) AS STREAM_RECORDS_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM;

SELECT * 
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM
LIMIT 10; 

INSERT INTO FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN(STEP,
                                                                     TYPE,
                                                                     AMOUNT,
                                                                     NAMEORIG,
                                                                     OLDBALORIG,
                                                                     NEWBALORIG,
                                                                     NAMEDEST,
                                                                     OLDBALDEST,
                                                                     NEWBALDEST,
                                                                     ISFRAUD,
                                                                     ISFLAGGEDFRAUD,
                                                                     LOAD_TIMESTAMP
                                                                     )
SELECT  STEP,
        TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALORIG,
        NEWBALORIG,
        NAMEDEST,
        OLDBALDEST,
        NEWBALDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD,
        CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM
WHERE METADATA$ACTION = 'INSERT';

SELECT COUNT(*) AS TOTAL_RECORDS
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;

SELECT COUNT(*) AS STREAM_REMAINING_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM;

CREATE TASK IF NOT EXISTS FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.PROCESS_BRONZE_STREAM_TASK
WAREHOUSE = COMPUTE_WH
SCHEDULE = '1 MINUTE'
WHEN SYSTEM$STREAM_HAS_DATA('FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM')
AS
INSERT INTO FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN(STEP,
                                                                     TYPE,
                                                                     AMOUNT,
                                                                     NAMEORIG,
                                                                     OLDBALORIG,
                                                                     NEWBALORIG,
                                                                     NAMEDEST,
                                                                     OLDBALDEST,
                                                                     NEWBALDEST,
                                                                     ISFRAUD,
                                                                     ISFLAGGEDFRAUD,
                                                                     LOAD_TIMESTAMP
                                                                     )
SELECT  STEP,
        TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALORIG,
        NEWBALORIG,
        NAMEDEST,
        OLDBALDEST,
        NEWBALDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD,
        CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM
WHERE METADATA$ACTION = 'INSERT';

SHOW TASKS IN SCHEMA FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW;

ALTER TASK FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.PROCESS_BRONZE_STREAM_TASK RESUME;

LIST @FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE;

COPY INTO FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
FROM @FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE/batch_003.csv;

SELECT COUNT(*) AS TOTAL_UPDATED_RECORD
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;

COPY INTO FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
FROM @FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_STAGE/batch_004.csv;

SELECT COUNT(*) AS FINAL_TOTAL_RECORDS
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;

SELECT
    NAME,
    STATE,
    SCHEDULED_TIME,
    COMPLETED_TIME,
    ERROR_CODE,
    ERROR_MESSAGE
FROM TABLE(
    FINANCIAL_LAKEHOUSE_DB.INFORMATION_SCHEMA.TASK_HISTORY(
        TASK_NAME => 'PROCESS_BRONZE_STREAM_TASK',
        RESULT_LIMIT => 20
    )
)
ORDER BY SCHEDULED_TIME DESC;

SELECT COUNT(*) AS REMAINING_STREAM_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_STREAM;

SELECT (
        SELECT  COUNT(*)
        FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
        ) AS BRONZE_COUNT,
        (
        SELECT COUNT(*)
        FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
        ) AS SILVER_COUNT;

ALTER TASK FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.PROCESS_BRONZE_STREAM_TASK SUSPEND;

SHOW TASKS IN SCHEMA FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW;

