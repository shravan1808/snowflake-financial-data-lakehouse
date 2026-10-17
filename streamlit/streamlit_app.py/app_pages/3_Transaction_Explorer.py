
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.title("🔎 Transaction Explorer")
st.caption(
    "Search, filter, inspect and export transaction-level records."
)

session = get_active_session()

# --------------------------------------------------
# 2. READ SHARED SIDEBAR FILTERS
# --------------------------------------------------

selected_types = st.session_state.transaction_types
fraud_status = st.session_state.fraud_status
min_amount = st.session_state.min_amount
max_amount = st.session_state.max_amount
step_start, step_end = st.session_state.step_range

if min_amount > max_amount:
    st.error("Minimum amount cannot exceed maximum amount.")
    st.stop()

# --------------------------------------------------
# 3. SEARCH AND DISPLAY CONTROLS
# --------------------------------------------------

st.subheader("Explore Transactions")

search_text = st.text_input(
    "Search origin or destination account",
    placeholder="Enter an account name, for example C123456789",
    key="explorer_search"
)

control_col1, control_col2 = st.columns(2)

with control_col1:
    page_size = st.selectbox(
        "Records per page",
        options=[25, 50, 100, 200],
        index=1,
        key="explorer_page_size"
    )

with control_col2:
    sort_order = st.selectbox(
        "Sort records by",
        options=[
            "Largest amount first",
            "Smallest amount first",
            "Latest simulation step first",
            "Earliest simulation step first"
        ],
        key="explorer_sort_order"
    )

sort_expressions = {
    "Largest amount first": "AMOUNT DESC",
    "Smallest amount first": "AMOUNT ASC",
    "Latest simulation step first": "STEP DESC",
    "Earliest simulation step first": "STEP ASC"
}

# --------------------------------------------------
# 4. BUILD FILTER CONDITIONS
# --------------------------------------------------

where_clause = """
    WHERE STEP >= ?
      AND STEP <= ?
      AND AMOUNT >= ?
      AND AMOUNT <= ?
"""

params = [
    step_start,
    step_end,
    min_amount,
    max_amount
]

# Transaction type filter
if selected_types:
    placeholders = ", ".join(["?"] * len(selected_types))
    where_clause += f" AND TYPE IN ({placeholders})"
    params.extend(selected_types)
else:
    # Return no records when no transaction types are selected
    where_clause += " AND 1 = 0"

# Fraud status filter
if fraud_status == "Fraud Only":
    where_clause += " AND ISFRAUD = 1"
elif fraud_status == "Non-Fraud Only":
    where_clause += " AND ISFRAUD = 0"

# Account search
if search_text.strip():
    where_clause += """
        AND (
            NAMEORIG ILIKE ?
            OR NAMEDEST ILIKE ?
        )
    """

    search_pattern = f"%{search_text.strip()}%"
    params.extend([search_pattern, search_pattern])

source_table = """
    FROM FINANCIAL_LAKEHOUSE_DB.SILVER_CURATED.TRANSACTIONS_CLEAN
"""

# --------------------------------------------------
# 5. COUNT MATCHING TRANSACTIONS
# --------------------------------------------------

count_query = (
    "SELECT COUNT(*) AS MATCHING_RECORDS "
    + source_table
    + where_clause
)

count_df = session.sql(
    count_query,
    params=params
).to_pandas()

total_records = int(count_df["MATCHING_RECORDS"].iloc[0])

st.metric(
    "Matching Transactions",
    f"{total_records:,}"
)

if total_records == 0:
    st.info("No transactions match the selected filters.")
    st.stop()

# --------------------------------------------------
# 6. PAGINATION
# --------------------------------------------------

total_pages = max(
    1,
    (total_records + page_size - 1) // page_size
)

if "explorer_page_number" not in st.session_state:
    st.session_state.explorer_page_number = 1

# Reset page if the current page exceeds the available pages
st.session_state.explorer_page_number = min(
    max(1, st.session_state.explorer_page_number),
    total_pages
)

page_col1, page_col2, page_col3 = st.columns([1, 2, 1])

with page_col1:
    if st.button(
        "← Previous",
        disabled=st.session_state.explorer_page_number <= 1
    ):
        st.session_state.explorer_page_number -= 1
        st.rerun()

with page_col2:
    requested_page = st.number_input(
        "Page number",
        min_value=1,
        max_value=total_pages,
        value=st.session_state.explorer_page_number,
        step=1,
        key="explorer_page_input"
    )

    if requested_page != st.session_state.explorer_page_number:
        st.session_state.explorer_page_number = int(requested_page)
        st.rerun()

with page_col3:
    if st.button(
        "Next →",
        disabled=st.session_state.explorer_page_number >= total_pages
    ):
        st.session_state.explorer_page_number += 1
        st.rerun()

current_page = st.session_state.explorer_page_number
offset = (current_page - 1) * page_size

# --------------------------------------------------
# 7. FETCH CURRENT PAGE
# --------------------------------------------------

transaction_query = """
    SELECT
        STEP,
        TYPE AS TRANSACTION_TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALORIG,
        NEWBALORIG,
        NAMEDEST,
        OLDBALDEST,
        NEWBALDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD
"""

transaction_query += source_table
transaction_query += where_clause

transaction_query += f"""
    ORDER BY {sort_expressions[sort_order]}
    LIMIT ? OFFSET ?
"""

page_params = params + [page_size, offset]

transactions_df = session.sql(
    transaction_query,
    params=page_params
).to_pandas()

# --------------------------------------------------
# 8. DISPLAY TRANSACTION TABLE
# --------------------------------------------------

st.subheader("Transaction Records")

st.caption(
    f"Page {current_page:,} of {total_pages:,} "
    f"• Showing {len(transactions_df):,} records "
    f"out of {total_records:,} matching transactions"
)

st.dataframe(
    transactions_df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# 9. TRANSACTION DETAILS
# --------------------------------------------------

st.divider()
st.subheader("Transaction Details")

if not transactions_df.empty:

    selected_index = st.selectbox(
        "Select a transaction to inspect",
        options=list(range(len(transactions_df))),
        format_func=lambda i: (
            f"Row {i + 1} | "
            f"{transactions_df.iloc[i]['TRANSACTION_TYPE']} | "
            f"Amount: {transactions_df.iloc[i]['AMOUNT']:,.2f} | "
            f"Step: {transactions_df.iloc[i]['STEP']}"
        ),
        key="explorer_selected_transaction"
    )

    selected_row = transactions_df.iloc[selected_index]

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.markdown("**Transaction Information**")

        st.write(
            "Transaction Type:",
            selected_row["TRANSACTION_TYPE"]
        )

        st.write("Amount:", f"{selected_row['AMOUNT']:,.2f}")
        st.write("Simulation Step:", selected_row["STEP"])

        st.write(
            "Fraud Status:",
            "Fraud" if selected_row["ISFRAUD"] == 1
            else "Non-Fraud"
        )

        st.write(
            "Flagged by System:",
            "Yes" if selected_row["ISFLAGGEDFRAUD"] == 1
            else "No"
        )

    with detail_col2:
        st.markdown("**Account and Balance Information**")

        st.write("Origin Account:", selected_row["NAMEORIG"])
        st.write("Destination Account:", selected_row["NAMEDEST"])

        st.write(
            "Origin Balance Before:",
            selected_row["OLDBALORIG"]
        )

        st.write(
            "Origin Balance After:",
            selected_row["NEWBALORIG"]
        )

        st.write(
            "Destination Balance Before:",
            selected_row["OLDBALDEST"]
        )

        st.write(
            "Destination Balance After:",
            selected_row["NEWBALDEST"]
        )

# --------------------------------------------------
# 10. EXPORT CURRENT PAGE TO CSV
# --------------------------------------------------

st.divider()
st.subheader("Export Transactions")

csv_data = transactions_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Current Page as CSV",
    data=csv_data,
    file_name=f"transactions_page_{current_page}.csv",
    mime="text/csv"
)

st.caption(
    "The CSV contains the records displayed on the current page, "
    "not every matching record across all pages."
)
