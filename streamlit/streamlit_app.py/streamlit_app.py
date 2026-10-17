
import streamlit as st

# Configure the application
st.set_page_config(
    page_title="Financial Data Lakehouse",
    page_icon="📊",
    layout="wide"
)


# Initialize shared filter values
if "transaction_types" not in st.session_state:
    st.session_state.transaction_types = [
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
        "PAYMENT",
        "TRANSFER"
    ]

if "fraud_status" not in st.session_state:
    st.session_state.fraud_status = "All"

# Define the navigation pages
overview_page = st.Page(
    "app_pages/1_Executive_Overview.py",
    title="Executive Overview",
    icon="📊",
    default=True
)

fraud_page = st.Page(
    "app_pages/2_Fraud_Analytics.py",
    title="Fraud Analytics",
    icon="🛡️"
)

# Page 3 — Transaction Explorer
explorer_page = st.Page(
    "app_pages/3_Transaction_Explorer.py",
    title="Transaction Explorer",
    icon="🔎"
)

# Page 4 — Pipeline Monitor
monitor_page = st.Page(
    "app_pages/4_Pipeline_Monitor.py",
    title="Pipeline Monitor",
    icon="⚙️"
)

# Register all four pages
navigation = st.navigation([
    overview_page,
    fraud_page,
    explorer_page,
    monitor_page
])

# Shared filters
st.sidebar.header("Dashboard Filters")

st.sidebar.multiselect(
    "Transaction Types",
    options=[
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
        "PAYMENT",
        "TRANSFER"
    ],
    key="transaction_types"
)

st.sidebar.selectbox(
    "Fraud Status",
    options=["All", "Fraud Only", "Non-Fraud Only"],
    key="fraud_status"
)

# Amount range filter
st.sidebar.subheader("Transaction Amount Range")

min_amount = st.sidebar.number_input(
    "Minimum Amount",
    min_value=0.0,
    value=0.0,
    step=1000.0,
    key="min_amount"
)

max_amount = st.sidebar.number_input(
    "Maximum Amount",
    min_value=0.0,
    value=1000000.0,
    step=1000.0,
    key="max_amount"
)

# Simulation step range filter
st.sidebar.subheader("Simulation Step Range")

step_range = st.sidebar.slider(
    "Select simulation steps",
    min_value=1,
    max_value=743,
    value=(1, 743),
    key="step_range"
)

# Run the selected page
navigation.run()
