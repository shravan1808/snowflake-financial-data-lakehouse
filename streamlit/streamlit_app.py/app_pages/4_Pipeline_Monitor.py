
import streamlit as st
from snowflake.snowpark.context import get_active_session

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.title("⚙️ Pipeline Monitor")
st.caption(
    "Monitor ingestion history, task execution, data reconciliation, "
    "data quality, and batch audit records."
)

session = get_active_session()

DATABASE = "FINANCIAL_LAKEHOUSE_DB"
BRONZE_TABLE = f"{DATABASE}.BRONZE_RAW.RAW_BRONZE_TABLE"
SILVER_TABLE = f"{DATABASE}.SILVER_CURATED.TRANSACTIONS_CLEAN"
GOLD_TABLE = f"{DATABASE}.GOLD_ANALYTICS.GOLD_TRANSACTION_SUMMARY"
AUDIT_TABLE = f"{DATABASE}.AUDIT.BATCH_AUDIT_LOG"
TASK_NAME = "PROCESS_BRONZE_STREAM_TASK"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def run_query(query):
    """Execute a Snowflake SQL query and return a pandas DataFrame."""
    return session.sql(query).to_pandas()


def show_error(section, error):
    """Display an error for one section without stopping the page."""
    st.warning(
        f"{section} could not be loaded. "
        "Check the object name, column names, and permissions."
    )

    with st.expander(f"Technical details — {section}"):
        st.code(str(error))


# ============================================================
# 3. REFRESH
# ============================================================

if st.button("🔄 Refresh Monitor"):
    st.rerun()

st.caption(
    "Refresh retrieves updated monitoring information. "
    "It does not execute or restart the pipeline task."
)

st.divider()


# ============================================================
# 4. DATA RECONCILIATION
# ============================================================

st.subheader("1. Data Reconciliation")

bronze_count = None
silver_count = None
gold_count = None

col1, col2, col3 = st.columns(3)

# Bronze row count
try:
    bronze_df = run_query(
        f"SELECT COUNT(*) AS TOTAL_ROWS FROM {BRONZE_TABLE}"
    )

    bronze_count = int(bronze_df["TOTAL_ROWS"].iloc[0])

    col1.metric("Bronze Rows", f"{bronze_count:,}")

except Exception as error:
    col1.metric("Bronze Rows", "Unavailable")
    show_error("Bronze row count", error)


# Silver row count
try:
    silver_df = run_query(
        f"SELECT COUNT(*) AS TOTAL_ROWS FROM {SILVER_TABLE}"
    )

    silver_count = int(silver_df["TOTAL_ROWS"].iloc[0])

    col2.metric("Silver Rows", f"{silver_count:,}")

except Exception as error:
    col2.metric("Silver Rows", "Unavailable")
    show_error("Silver row count", error)


# Gold aggregated transaction volume
try:
    gold_df = run_query(
        f"""
        SELECT COALESCE(SUM(TRANSACTION_VOLUME), 0) AS TOTAL_ROWS
        FROM {GOLD_TABLE}
        """
    )

    gold_count = int(gold_df["TOTAL_ROWS"].iloc[0])

    col3.metric("Gold Reported Volume", f"{gold_count:,}")

except Exception as error:
    col3.metric("Gold Reported Volume", "Unavailable")
    show_error("Gold transaction volume", error)


# Reconciliation interpretation
if bronze_count is not None and silver_count is not None:

    if bronze_count == silver_count:
        st.success(
            "Bronze and Silver row counts match. "
            "This confirms row-count equality, not complete data equality."
        )
    else:
        difference = abs(bronze_count - silver_count)

        st.warning(
            f"Bronze and Silver differ by {difference:,} rows. "
            "Review transformations, deduplication, and rejected records."
        )


if silver_count is not None and gold_count is not None:

    if silver_count == gold_count:
        st.success(
            "Silver row count matches the summed Gold transaction volume."
        )
    else:
        st.info(
            "Silver row count differs from Gold reported volume. "
            "This may be expected because Gold contains aggregated data. "
            "Verify the Gold table's grain and aggregation logic."
        )

st.divider()


# ============================================================
# 5. FILE LOAD HISTORY
# ============================================================

st.subheader("2. Recent File Load History")

try:
    load_history_query = f"""
        SELECT *
        FROM {DATABASE}.INFORMATION_SCHEMA.LOAD_HISTORY
        WHERE UPPER(SCHEMA_NAME) = 'BRONZE_RAW'
          AND UPPER(TABLE_NAME) = 'RAW_BRONZE_TABLE'
        ORDER BY LAST_LOAD_TIME DESC
        LIMIT 20
    """

    load_history_df = run_query(load_history_query)

    if load_history_df.empty:
        st.info(
            "No load history records were returned for the Bronze table. "
            "Check the ingestion method, metadata retention, and permissions."
        )
    else:
        st.dataframe(
            load_history_df,
            use_container_width=True,
            hide_index=True
        )

except Exception as error:
    show_error("File load history", error)

st.divider()


# ============================================================
# 6. TASK EXECUTION HISTORY
# ============================================================

st.subheader("3. Task Execution History")

try:
    task_history_query = f"""
        SELECT *
        FROM TABLE(
            {DATABASE}.INFORMATION_SCHEMA.TASK_HISTORY(
                TASK_NAME => '{TASK_NAME}',
                RESULT_LIMIT => 20
            )
        )
        ORDER BY SCHEDULED_TIME DESC
    """

    task_history_df = run_query(task_history_query)

    if task_history_df.empty:
        st.info(
            "No task execution history was returned. "
            "Verify the task name, privileges, and execution history."
        )
    else:
        preferred_columns = [
            "NAME",
            "STATE",
            "SCHEDULED_TIME",
            "QUERY_START_TIME",
            "COMPLETED_TIME",
            "ERROR_CODE",
            "ERROR_MESSAGE",
            "QUERY_ID"
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in task_history_df.columns
        ]

        if available_columns:
            st.dataframe(
                task_history_df[available_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(
                task_history_df,
                use_container_width=True,
                hide_index=True
            )

except Exception as error:
    show_error("Task execution history", error)

st.divider()


# ============================================================
# 7. SILVER DATA QUALITY CHECKS
# ============================================================

st.subheader("4. Silver Data Quality Checks")

quality_query = f"""
    SELECT
        COUNT(*) AS TOTAL_ROWS,

        COALESCE(COUNT_IF(STEP IS NULL), 0)
            AS NULL_STEP_ROWS,

        COALESCE(COUNT_IF(TYPE IS NULL), 0)
            AS NULL_TYPE_ROWS,

        COALESCE(COUNT_IF(AMOUNT IS NULL), 0)
            AS NULL_AMOUNT_ROWS,

        COALESCE(COUNT_IF(ISFRAUD IS NULL), 0)
            AS NULL_FRAUD_LABEL_ROWS,

        COALESCE(COUNT_IF(ISFLAGGEDFRAUD IS NULL), 0)
            AS NULL_FLAGGED_LABEL_ROWS,

        COALESCE(COUNT_IF(AMOUNT < 0), 0)
            AS NEGATIVE_AMOUNT_ROWS,

        COALESCE(COUNT_IF(ISFRAUD NOT IN (0, 1)), 0)
            AS INVALID_FRAUD_LABEL_ROWS,

        COALESCE(COUNT_IF(ISFLAGGEDFRAUD NOT IN (0, 1)), 0)
            AS INVALID_FLAGGED_LABEL_ROWS,

        COUNT(*) - COUNT(
            DISTINCT HASH(
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
            )
        ) AS DUPLICATE_SIGNATURE_ROWS

    FROM {SILVER_TABLE}
"""

try:
    quality_df = run_query(quality_query)

    if not quality_df.empty:

        quality_row = quality_df.iloc[0]

        null_columns = [
            "NULL_STEP_ROWS",
            "NULL_TYPE_ROWS",
            "NULL_AMOUNT_ROWS",
            "NULL_FRAUD_LABEL_ROWS",
            "NULL_FLAGGED_LABEL_ROWS"
        ]

        null_count = sum(
            int(quality_row[column])
            for column in null_columns
        )

        invalid_label_count = (
            int(quality_row["INVALID_FRAUD_LABEL_ROWS"])
            + int(quality_row["INVALID_FLAGGED_LABEL_ROWS"])
        )

        negative_count = int(
            quality_row["NEGATIVE_AMOUNT_ROWS"]
        )

        duplicate_count = int(
            quality_row["DUPLICATE_SIGNATURE_ROWS"]
        )

        # Summary metrics
        qcol1, qcol2, qcol3 = st.columns(3)

        qcol1.metric(
            "Total Silver Rows",
            f"{int(quality_row['TOTAL_ROWS']):,}"
        )

        qcol2.metric(
            "Null Critical Fields",
            f"{null_count:,}"
        )

        qcol3.metric(
            "Negative Amount Rows",
            f"{negative_count:,}"
        )

        # Detailed quality results
        st.markdown("**Detailed Quality Results**")

        st.dataframe(
            quality_df,
            use_container_width=True,
            hide_index=True
        )

        # Quality status
        if (
            null_count == 0
            and invalid_label_count == 0
            and negative_count == 0
        ):
            st.success(
                "The configured null, fraud-label, and negative-amount "
                "checks passed."
            )
        else:
            st.warning(
                "One or more configured quality checks found issues. "
                "Review the detailed results above."
            )

        st.caption(
            f"Repeated row signatures detected: {duplicate_count:,}. "
            "This is a diagnostic indicator, not a definitive count of "
            "duplicate business transactions. Repeated signatures may "
            "represent legitimate records."
        )

except Exception as error:
    show_error("Silver data quality checks", error)

st.divider()


# ============================================================
# 8. BATCH AUDIT LOG
# ============================================================

st.subheader("5. Batch Audit Log")

try:
    audit_query = f"""
        SELECT *
        FROM {AUDIT_TABLE}
        LIMIT 100
    """

    audit_df = run_query(audit_query)

    if audit_df.empty:
        st.info(
            "The audit table exists, but no audit records were returned."
        )
    else:
        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True
        )

        audit_csv = audit_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Audit Log as CSV",
            data=audit_csv,
            file_name="financial_lakehouse_audit_log.csv",
            mime="text/csv"
        )

except Exception as error:
    show_error("Batch audit log", error)

st.divider()


# ============================================================
# 9. PIPELINE MONITORING GUIDE
# ============================================================

st.subheader("6. Monitoring Guide")

st.markdown(
    """
    **Bronze layer**
    - Stores raw ingested records.
    - Review row counts and file load history.

    **Silver layer**
    - Stores cleaned and curated transactions.
    - Review null values, invalid fraud labels, negative amounts,
      and repeated row signatures.

    **Gold layer**
    - Stores analytics-ready aggregates.
    - Validate aggregation logic before comparing its volume with Silver.

    **Task history**
    - Review execution states, timestamps, query IDs, and error messages.

    **Audit log**
    - Review batch processing information when the pipeline writes audit rows.

    **Operational note:** This page reads monitoring information only.
    It does not start, resume, suspend, or execute the pipeline task.
    """
)
