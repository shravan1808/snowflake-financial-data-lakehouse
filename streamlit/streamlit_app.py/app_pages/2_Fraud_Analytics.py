
import streamlit as st
from snowflake.snowpark.context import get_active_session

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Fraud Analytics",
    page_icon="🛡️",
    layout="wide"
)

st.title("Fraud Analytics")
st.caption(
    "Analyze fraud patterns across transaction types "
    "and simulation steps."
)

# =========================================================
# 2. SNOWFLAKE CONNECTION AND SHARED FILTERS
# =========================================================

session = get_active_session()

selected_types = st.session_state.transaction_types
fraud_status = st.session_state.fraud_status
min_amount = st.session_state.min_amount
max_amount = st.session_state.max_amount
step_start, step_end = st.session_state.step_range

if min_amount > max_amount:
    st.error("Minimum amount cannot exceed maximum amount.")
    st.stop()

# =========================================================
# 3. REUSABLE FILTER BUILDER
# =========================================================

def build_filtered_query(base_query, apply_fraud_status=False):
    """
    Add the shared transaction type, amount and step filters.

    The fraud status filter is optional because fraud-rate
    calculations must include both fraud and non-fraud rows.
    """

    query = base_query + """
        WHERE STEP >= ? AND STEP <= ?
          AND AMOUNT >= ? AND AMOUNT <= ?
    """

    params = [
        step_start,
        step_end,
        min_amount,
        max_amount
    ]

    if selected_types:
        placeholders = ", ".join(["?"] * len(selected_types))
        query += f" AND TYPE IN ({placeholders})"
        params.extend(selected_types)
    else:
        query += " AND 1 = 0"

    if apply_fraud_status:
        if fraud_status == "Fraud Only":
            query += " AND ISFRAUD = 1"
        elif fraud_status == "Non-Fraud Only":
            query += " AND ISFRAUD = 0"

    return query, params


# =========================================================
# 4. FRAUD KPI METRICS
# =========================================================

st.subheader("Fraud KPIs")

kpi_query = """
    SELECT
        COUNT(*) AS TOTAL_TRANSACTIONS,

        COALESCE(SUM(ISFRAUD), 0) AS FRAUD_COUNT,

        COALESCE(
            100.0 * SUM(ISFRAUD) / NULLIF(COUNT(*), 0),
            0
        ) AS FRAUD_RATE,

        COALESCE(
            SUM(
                CASE
                    WHEN ISFRAUD = 1 THEN AMOUNT
                    ELSE 0
                END
            ),
            0
        ) AS FRAUD_AMOUNT,

        COALESCE(
            SUM(
                CASE
                    WHEN ISFLAGGEDFRAUD = 1 THEN 1
                    ELSE 0
                END
            ),
            0
        ) AS FLAGGED_FRAUD_COUNT

    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
"""

# Intentionally exclude the Fraud Status filter from risk KPIs.
# This keeps the denominator representative of the full
# selected population rather than only fraud or non-fraud rows.
kpi_query, kpi_params = build_filtered_query(
    kpi_query,
    apply_fraud_status=False
)

metrics_df = session.sql(
    kpi_query,
    params=kpi_params
).to_pandas()

total_transactions = int(
    metrics_df["TOTAL_TRANSACTIONS"].iloc[0]
)

fraud_count = int(
    metrics_df["FRAUD_COUNT"].iloc[0]
)

fraud_rate = float(
    metrics_df["FRAUD_RATE"].iloc[0]
)

fraud_amount = float(
    metrics_df["FRAUD_AMOUNT"].iloc[0]
)

flagged_fraud_count = int(
    metrics_df["FLAGGED_FRAUD_COUNT"].iloc[0]
)

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

col1.metric(
    "Transactions Analyzed",
    f"{total_transactions:,}"
)

col2.metric(
    "Fraud Transactions",
    f"{fraud_count:,}"
)

col3.metric(
    "Fraud Rate",
    f"{fraud_rate:.4f}%"
)

col4.metric(
    "Fraud Amount",
    f"{fraud_amount:,.2f}"
)

st.caption(
    "Fraud KPIs use transactions matching the transaction type, "
    "amount and simulation step filters. The Fraud Status filter "
    "does not affect these risk metrics."
)

st.caption(
    f"Flagged fraud transactions: {flagged_fraud_count:,}"
)

# =========================================================
# 5. FRAUD ANALYSIS BY TRANSACTION TYPE
# =========================================================

st.subheader("Fraud Analysis by Transaction Type")

fraud_type_base_query = """
    SELECT
        TYPE AS TRANSACTION_TYPE,
        COUNT(*) AS TOTAL_TRANSACTIONS,
        COALESCE(SUM(ISFRAUD), 0) AS FRAUD_COUNT,

        COALESCE(
            SUM(
                CASE
                    WHEN ISFRAUD = 1 THEN AMOUNT
                    ELSE 0
                END
            ),
            0
        ) AS FRAUD_AMOUNT,

        COALESCE(
            100.0 * SUM(ISFRAUD) / NULLIF(COUNT(*), 0),
            0
        ) AS FRAUD_RATE

    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
"""

fraud_type_query, fraud_type_params = build_filtered_query(
    fraud_type_base_query,
    apply_fraud_status=False
)

fraud_type_query += """
    GROUP BY TYPE
    ORDER BY FRAUD_COUNT DESC
"""

fraud_type_df = session.sql(
    fraud_type_query,
    params=fraud_type_params
).to_pandas()

if fraud_type_df.empty:
    st.info("No transactions match the selected filters.")
else:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.caption("Fraud transaction count by type")

        st.bar_chart(
            fraud_type_df.set_index("TRANSACTION_TYPE")[
                ["FRAUD_COUNT"]
            ]
        )

    with chart_col2:
        st.caption("Fraud amount by type")

        st.bar_chart(
            fraud_type_df.set_index("TRANSACTION_TYPE")[
                ["FRAUD_AMOUNT"]
            ]
        )

    st.caption(
        "Fraud rates are calculated using all matching transactions, "
        "regardless of the Fraud Status selection."
    )

    st.dataframe(
        fraud_type_df,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 6. HIGH-RISK SIMULATION STEPS
# =========================================================

st.subheader("High-Risk Simulation Steps")

step_base_query = """
    SELECT
        STEP,
        COUNT(*) AS TOTAL_TRANSACTIONS,
        COALESCE(SUM(ISFRAUD), 0) AS FRAUD_COUNT,

        COALESCE(
            SUM(
                CASE
                    WHEN ISFRAUD = 1 THEN AMOUNT
                    ELSE 0
                END
            ),
            0
        ) AS FRAUD_AMOUNT,

        COALESCE(
            100.0 * SUM(ISFRAUD) / NULLIF(COUNT(*), 0),
            0
        ) AS FRAUD_RATE

    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
"""

step_query, step_params = build_filtered_query(
    step_base_query,
    apply_fraud_status=False
)

step_query += """
    GROUP BY STEP
    HAVING SUM(ISFRAUD) > 0
    ORDER BY FRAUD_RATE DESC, FRAUD_AMOUNT DESC
    LIMIT 20
"""

step_df = session.sql(
    step_query,
    params=step_params
).to_pandas()

if step_df.empty:
    st.info("No fraud transactions match the selected filters.")
else:
    st.caption(
        "Top 20 steps ranked by fraud rate, then fraud amount."
    )

    step_chart_col1, step_chart_col2 = st.columns(2)

    with step_chart_col1:
        st.caption("Fraud count by simulation step")

        st.bar_chart(
            step_df.set_index("STEP")[["FRAUD_COUNT"]]
        )

    with step_chart_col2:
        st.caption("Fraud rate by simulation step (%)")

        st.bar_chart(
            step_df.set_index("STEP")[["FRAUD_RATE"]]
        )

    st.dataframe(
        step_df,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 7. FRAUD INVESTIGATION
# =========================================================

st.subheader("Fraud Investigation")

st.caption(
    "Review individual transactions labeled as fraud. "
    "This section always shows fraud-labeled records, "
    "regardless of the Fraud Status selection."
)

investigation_base_query = """
    SELECT
        STEP,
        TYPE AS TRANSACTION_TYPE,
        AMOUNT,
        NAMEORIG,
        NAMEDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD
    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
    WHERE ISFRAUD = 1
"""

# Add shared filters except Fraud Status:
# this table always investigates fraud-labeled transactions.
investigation_query = investigation_base_query + """
    AND STEP >= ? AND STEP <= ?
    AND AMOUNT >= ? AND AMOUNT <= ?
"""

investigation_params = [
    step_start,
    step_end,
    min_amount,
    max_amount
]

if selected_types:
    placeholders = ", ".join(["?"] * len(selected_types))
    investigation_query += f" AND TYPE IN ({placeholders})"
    investigation_params.extend(selected_types)
else:
    investigation_query += " AND 1 = 0"

investigation_query += """
    ORDER BY AMOUNT DESC
    LIMIT 500
"""

investigation_df = session.sql(
    investigation_query,
    params=investigation_params
).to_pandas()

st.caption(
    f"Showing {len(investigation_df):,} fraud-labeled transactions "
    "with a maximum of 500 records."
)

if investigation_df.empty:
    st.info(
        "No fraud-labeled transactions match the selected filters."
    )
else:
    st.dataframe(
        investigation_df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = investigation_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Fraud Records as CSV",
        data=csv_data,
        file_name="fraud_investigation.csv",
        mime="text/csv"
    )
