CREATE OR REPLACE TABLE FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
(
STEP NUMBER,
TYPE STRING,
AMOUNT NUMBER(20,2),
NAMEORIG STRING,
OLDBALORIG NUMBER(20,2),
NEWBALORIG NUMBER(20,2),
NAMEDEST STRING,
OLDBALDEST NUMBER(20,2),
NEWBALDEST NUMBER(20,2),
ISFRAUD NUMBER,
ISFLAGGEDFRAUD NUMBER,
LOAD_TIMESTAMP TIMESTAMP_NTZ
);

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
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE;

SELECT  COUNT(*) AS TOTAL_RECORDS
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;

SELECT  MIN(LOAD_TIMESTAMP) AS  MIN_TIMESTAMP,
        MAX(LOAD_TIMESTAMP) AS MAX_TIMESTAMP
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN;

SELECT  'SILVER' AS LAYER,
        ISFRAUD,
        COUNT(*) AS FRAUD_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
GROUP BY ISFRAUD
UNION ALL
SELECT  'BRONZE' AS LAYER,
        ISFRAUD,
        COUNT(*) AS FRAUD_COUNT
FROM FINANCIAL_LAKEHOUSE_DB.BRONZE_RAW.RAW_BRONZE_TABLE
GROUP BY ISFRAUD
ORDER BY FRAUD_COUNT DESC;