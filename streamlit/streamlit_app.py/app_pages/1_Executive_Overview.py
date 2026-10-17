
import streamlit as st
from snowflake.snowpark.context import get_active_session

# Configure the page
st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide"
)

# Display the heading
st.title("Financial Data Lakehouse")
st.caption("Executive Overview | Transaction Performance & Fraud Analytics")

# Connect to the active Snowflake session
session = get_active_session()


# Retrieve transaction summary data from Snowflake

# Read shared filter selections
selected_types = st.session_state.transaction_types
fraud_status = st.session_state.fraud_status
min_amount = st.session_state.min_amount
max_amount = st.session_state.max_amount
step_start, step_end = st.session_state.step_range

# Validate the selected amount range
if min_amount > max_amount:
    st.error("Minimum amount cannot exceed maximum amount.")
    st.stop()


# Build the base SQL query
query = """
    SELECT
        TYPE AS TRANSACTION_TYPE,
        COUNT(*) AS TRANSACTION_VOLUME,
        SUM(AMOUNT) AS TRANSACTION_AMOUNT,
        SUM(ISFRAUD) AS FRAUD_TOTAL
    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
    WHERE 1 = 1
"""

params = []

# Apply the simulation step range
query += " AND STEP >= ? AND STEP <= ?"
params.extend([step_start, step_end])




# Apply the amount range
query += " AND AMOUNT >= ? AND AMOUNT <= ?"
params.extend([min_amount, max_amount])

# Apply transaction type filter
if selected_types:
    placeholders = ", ".join(["?"] * len(selected_types))
    query += f" AND TYPE IN ({placeholders})"
    params.extend(selected_types)
else:
    # No selected types means no matching transactions
    query += " AND 1 = 0"

# Apply fraud status filter
if fraud_status == "Fraud Only":
    query += " AND ISFRAUD = 1"
elif fraud_status == "Non-Fraud Only":
    query += " AND ISFRAUD = 0"

# Group and sort the filtered results
query += """
    GROUP BY TYPE
    ORDER BY TRANSACTION_AMOUNT DESC
"""

# Execute the query
summary_df = session.sql(query, params=params).to_pandas()

if summary_df.empty:
    st.info("No transactions match the selected filters.")

# Calculate the overall transaction metrics
total_transactions = int(
    summary_df["TRANSACTION_VOLUME"].sum()
)

total_amount = float(
    summary_df["TRANSACTION_AMOUNT"].sum()
)

total_fraud = int(
    summary_df["FRAUD_TOTAL"].sum()
)


# Calculate fraud amount using the same filters as the summary
fraud_amount_query = """
    SELECT COALESCE(SUM(AMOUNT), 0) AS TOTAL_FRAUD_AMOUNT
    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
    WHERE ISFRAUD = 1
"""

fraud_amount_params = []


# Apply the same amount range to fraud amount
fraud_amount_query += " AND AMOUNT >= ? AND AMOUNT <= ?"
fraud_amount_params.extend([min_amount, max_amount])

fraud_amount_query += " AND STEP >= ? AND STEP <= ?"
fraud_amount_params.extend([step_start, step_end])


if selected_types:
    placeholders = ", ".join(["?"] * len(selected_types))
    fraud_amount_query += f" AND TYPE IN ({placeholders})"
    fraud_amount_params.extend(selected_types)
else:
    fraud_amount_query += " AND 1 = 0"

if fraud_status == "Non-Fraud Only":
    fraud_amount_query += " AND 1 = 0"

fraud_amount_df = session.sql(
    fraud_amount_query,
    params=fraud_amount_params
).to_pandas()

total_fraud_amount = float(
    fraud_amount_df["TOTAL_FRAUD_AMOUNT"].iloc[0]
)


# Display the KPI cards
st.subheader("Key Performance Indicators")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

col1.metric(
    "Total Transactions",
    f"{total_transactions:,}"
)

col2.metric(
    "Total Transaction Amount",
    f"{total_amount:,.2f}"
)

col3.metric(
    "Fraud Transactions",
    f"{total_fraud:,}"
)

col4.metric(
    "Total Fraud Amount",
    f"{total_fraud_amount:,.2f}"
)


st.subheader("Transaction Volume by Type")

volume_chart_df = summary_df[
    ["TRANSACTION_TYPE", "TRANSACTION_VOLUME"]
].copy()

volume_chart_df = volume_chart_df.set_index("TRANSACTION_TYPE")

st.bar_chart(volume_chart_df)


st.subheader("Transaction Amount by Type")

amount_chart_df = summary_df[
    ["TRANSACTION_TYPE", "TRANSACTION_AMOUNT"]
].copy()

amount_chart_df = amount_chart_df.set_index("TRANSACTION_TYPE")

st.bar_chart(amount_chart_df)

# Display the retrieved data
st.subheader("Transaction Summary — Data Preview")
st.caption(
    "Transaction volume, total amount, and fraud counts "
    "grouped by transaction type."
)
st.dataframe(summary_df, use_container_width=True, hide_index=True)
