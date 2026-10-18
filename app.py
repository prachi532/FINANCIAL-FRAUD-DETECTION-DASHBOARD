
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Online Fraud Analytics",
    page_icon="🔎",
    layout="wide"
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    file_path = Path("transactions_sample.csv")

    if not file_path.exists():
        return None

    data = pd.read_csv(file_path)

    required_columns = [
        "step", "type", "amount", "isFraud"
    ]

    missing = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    data["step"] = pd.to_numeric(
        data["step"], errors="coerce"
    )
    data["amount"] = pd.to_numeric(
        data["amount"], errors="coerce"
    )
    data["isFraud"] = pd.to_numeric(
        data["isFraud"], errors="coerce"
    )

    data = data.dropna(
        subset=["step", "amount", "type", "isFraud"]
    ).copy()

    data = data[data["amount"] >= 0]
    data = data[data["isFraud"].isin([0, 1])].copy()

    data["isFraud"] = data["isFraud"].astype(int)
    data["Fraud Status"] = data["isFraud"].map({
        0: "Legitimate",
        1: "Fraud"
    })

    return data


try:
    df = load_data()
except Exception as error:
    st.error(f"Could not read the dataset: {error}")
    st.stop()

if df is None:
    st.error(
        "Dataset not found. Add transactions_sample.csv "
        "to the same folder as app.py."
    )
    st.stop()

if df.empty:
    st.error("The dataset contains no usable transactions.")
    st.stop()

# ---------------- TITLE ----------------
st.title("🔎 Online Fraud Analytics Dashboard")
st.caption(
    "Digital payment transaction monitoring | "
    "Exploratory data analysis"
)

st.info(
    "This dashboard analyzes a sample of simulated PaySim "
    "transactions. Fraud labels are provided by the dataset; "
    "this version does not predict new fraud."
)

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("Filter Transactions")

transaction_types = sorted(df["type"].unique().tolist())

selected_types = st.sidebar.multiselect(
    "Transaction Type",
    options=transaction_types,
    default=transaction_types
)

selected_status = st.sidebar.multiselect(
    "Fraud Status",
    options=["Legitimate", "Fraud"],
    default=["Legitimate", "Fraud"]
)

min_amount = float(df["amount"].min())
max_amount = float(df["amount"].max())

amount_range = st.sidebar.slider(
    "Transaction Amount",
    min_value=min_amount,
    max_value=max_amount,
    value=(min_amount, max_amount)
)

# ---------------- APPLY FILTERS ----------------
filtered = df[
    df["type"].isin(selected_types)
    & df["Fraud Status"].isin(selected_status)
    & df["amount"].between(
        amount_range[0], amount_range[1]
    )
].copy()

st.caption(
    f"Showing {len(filtered):,} of {len(df):,} sampled transactions"
)

# ---------------- KPI METRICS ----------------
total_transactions = len(filtered)

fraud_data = filtered[filtered["isFraud"] == 1]
fraud_count = len(fraud_data)

fraud_rate = (
    fraud_count / total_transactions * 100
    if total_transactions else 0
)

fraud_value = fraud_data["amount"].sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Transactions", f"{total_transactions:,}")
c2.metric("Fraud-labeled", f"{fraud_count:,}")
c3.metric("Fraud Rate", f"{fraud_rate:.2f}%")
c4.metric("Fraud-labeled Value", f"{fraud_value:,.2f}")

st.divider()

# ---------------- CHART 1: TRANSACTION TYPES ----------------
st.subheader("1. Transactions by Type")

if not filtered.empty:
    type_data = (
        filtered.groupby("type")
        .agg(
            Transactions=("isFraud", "size"),
            Fraud_Transactions=("isFraud", "sum")
        )
        .reset_index()
    )

    fig_type = px.bar(
        type_data,
        x="type",
        y=["Transactions", "Fraud_Transactions"],
        barmode="group",
        title="Transaction Volume by Type",
        labels={
            "type": "Transaction Type",
            "value": "Number of Transactions",
            "variable": "Metric"
        }
    )

    st.plotly_chart(fig_type, use_container_width=True)

# ---------------- CHART 2: FRAUD DISTRIBUTION ----------------
st.subheader("2. Legitimate vs Fraud Transactions")

if not filtered.empty:
    status_data = (
        filtered["Fraud Status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Count")
    )

    fig_status = px.pie(
        status_data,
        names="Status",
        values="Count",
        hole=0.45,
        title="Transaction Status Distribution"
    )

    st.plotly_chart(fig_status, use_container_width=True)

# ---------------- CHART 3: FRAUD OVER TIME ----------------
st.subheader("3. Fraud Trend Over Simulated Time")

if not filtered.empty:
    trend_data = (
        filtered.groupby("step")
        .agg(
            Transactions=("isFraud", "size"),
            Fraud_Transactions=("isFraud", "sum")
        )
        .reset_index()
        .sort_values("step")
    )

    fig_trend = px.line(
        trend_data,
        x="step",
        y=["Transactions", "Fraud_Transactions"],
        markers=True,
        title="Transaction and Fraud Counts by Time Step",
        labels={
            "step": "Simulation Time Step",
            "value": "Transaction Count",
            "variable": "Metric"
        }
    )

    st.plotly_chart(fig_trend, use_container_width=True)

# ---------------- CHART 4: AMOUNT COMPARISON ----------------
st.subheader("4. Transaction Amount by Fraud Status")

if not filtered.empty:
    fig_amount = px.box(
        filtered,
        x="Fraud Status",
        y="amount",
        color="Fraud Status",
        points=False,
        title="Transaction Amount Distribution"
    )

    st.plotly_chart(fig_amount, use_container_width=True)

# ---------------- TRANSACTION TABLE ----------------
st.subheader("5. Transaction Details")

search_fraud_only = st.checkbox(
    "Show only fraud-labeled transactions"
)

table_data = filtered.copy()

if search_fraud_only:
    table_data = table_data[
        table_data["isFraud"] == 1
    ]

display_columns = [
    col for col in [
        "step", "type", "amount",
        "nameOrig", "nameDest",
        "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest",
        "isFraud", "Fraud Status"
    ]
    if col in table_data.columns
]

st.dataframe(
    table_data[display_columns],
    use_container_width=True,
    hide_index=True
)

csv_data = table_data[display_columns].to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download filtered transactions",
    data=csv_data,
    file_name="filtered_transactions.csv",
    mime="text/csv"
)

# ---------------- INSIGHTS ----------------
st.subheader("6. Quick Insights")

if filtered.empty:
    st.warning("No transactions match the selected filters.")
else:
    top_type = (
        filtered["type"].value_counts().idxmax()
    )

    fraud_types = fraud_data["type"].value_counts()

    st.write(
        f"- **Most common transaction type:** {top_type}"
    )
    st.write(
        f"- **Fraud-labeled transaction count:** {fraud_count:,}"
    )
    st.write(
        f"- **Fraud-labeled transaction value:** "
        f"{fraud_value:,.2f}"
    )

    if not fraud_types.empty:
        st.write(
            f"- **Most frequent fraud type:** "
            f"{fraud_types.index[0]}"
        )

st.caption(
    "Educational analytics project. Fraud-labeled value is not "
    "necessarily the confirmed financial loss."
)
