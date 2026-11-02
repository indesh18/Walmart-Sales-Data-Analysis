import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Walmart Sales AI Dashboard", page_icon="🛒", layout="wide")
st.title("🛒 Walmart Sales Analytics")
st.caption("Interactive dashboard with a Gemini-powered AI sales assistant")
DATA_PATH = Path(__file__).parent / "Walmart_Dataset.csv"

@st.cache_data
def load_data(uploaded_file=None):
    source = uploaded_file if uploaded_file is not None else DATA_PATH
    df = pd.read_csv(source, encoding_errors="ignore")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["unit_price"] = pd.to_numeric(df["unit_price"].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df = df.dropna(subset=["unit_price", "quantity"]).copy()
    df["sales"] = df["unit_price"] * df["quantity"]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        df["month"] = df["date"].dt.to_period("M").astype(str)
    if "profit_margin" in df.columns:
        df["profit_margin"] = pd.to_numeric(df["profit_margin"], errors="coerce")
        df["estimated_profit"] = df["sales"] * df["profit_margin"]
    return df

def data_context(data):
    summary = {
        "transactions": int(len(data)),
        "total_sales": round(float(data.sales.sum()), 2),
        "units_sold": round(float(data.quantity.sum()), 2),
        "average_transaction_sales": round(float(data.sales.mean()), 2),
    }
    for col in ["branch", "city", "category", "payment_method"]:
        if col in data.columns:
            summary[f"sales_by_{col}"] = {
                str(k): round(float(v), 2)
                for k, v in data.groupby(col).sales.sum().sort_values(ascending=False).head(12).items()
            }
    if "month" in data.columns:
        summary["sales_by_month"] = {
            str(k): round(float(v), 2)
            for k, v in data.groupby("month").sales.sum().sort_index().items()
        }
    return summary

def ask_gemini(question, context):
   try:
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
except Exception:
    api_key = ""

if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not key:
        return "AI setup pending: add GOOGLE_API_KEY as described in README_AI_UPGRADE.md. The dashboard works without it."
    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "You are a careful retail sales analyst. Answer using only the supplied data. "
                "Never invent numbers. If the data is insufficient, say so.\\n"
                f"DATA: {context}\\nQUESTION: {question}"
            ),
        )
        return response.text
    except Exception as exc:
        return f"Gemini request failed: {exc}"

with st.sidebar:
    st.header("Dataset")
    upload = st.file_uploader("Upload a CSV (optional)", type=["csv"])
try:
    df = load_data(upload)
except Exception as exc:
    st.error(f"Could not load dataset: {exc}")
    st.info("Keep Walmart_Dataset.csv beside app.py, or upload a compatible CSV.")
    st.stop()

filtered = df.copy()
with st.sidebar:
    for col, label in [("city", "City"), ("branch", "Branch"), ("category", "Category"), ("payment_method", "Payment method")]:
        if col in filtered.columns:
            options = sorted(filtered[col].dropna().astype(str).unique())
            chosen = st.multiselect(label, options, default=options)
            filtered = filtered[filtered[col].astype(str).isin(chosen)]
    if "date" in filtered.columns and filtered.date.notna().any():
        low, high = filtered.date.min().date(), filtered.date.max().date()
        date_range = st.date_input("Date range", value=(low, high), min_value=low, max_value=high)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered = filtered[filtered.date.dt.date.between(*date_range)]

if filtered.empty:
    st.warning("No data matches these filters.")
    st.stop()

a, b, c, d = st.columns(4)
a.metric("Total sales", f"${filtered.sales.sum():,.2f}")
b.metric("Units sold", f"{filtered.quantity.sum():,.0f}")
c.metric("Transactions", f"{len(filtered):,}")
d.metric("Average transaction", f"${filtered.sales.mean():,.2f}")
if "estimated_profit" in filtered.columns:
    st.caption("Estimated profit uses sales × dataset profit_margin; it is not audited accounting profit.")

left, right = st.columns(2)
with left:
    if "category" in filtered.columns:
        chart = filtered.groupby("category", as_index=False).sales.sum().sort_values("sales", ascending=False)
        st.subheader("Sales by product category")
        st.plotly_chart(px.bar(chart, x="category", y="sales", color="category"), use_container_width=True)
with right:
    if "month" in filtered.columns and filtered.date.notna().any():
        chart = filtered.groupby("month", as_index=False).sales.sum().sort_values("month")
        st.subheader("Monthly sales trend")
        st.plotly_chart(px.line(chart, x="month", y="sales", markers=True), use_container_width=True)
    elif "payment_method" in filtered.columns:
        chart = filtered.groupby("payment_method", as_index=False).sales.sum()
        st.subheader("Sales by payment method")
        st.plotly_chart(px.pie(chart, names="payment_method", values="sales", hole=.4), use_container_width=True)

left, right = st.columns(2)
with left:
    if "branch" in filtered.columns:
        st.subheader("Branch performance")
        table = filtered.groupby("branch", as_index=False).agg(sales=("sales", "sum"), units=("quantity", "sum"), transactions=("sales", "size")).sort_values("sales", ascending=False)
        st.dataframe(table, use_container_width=True, hide_index=True)
with right:
    if "payment_method" in filtered.columns:
        st.subheader("Payment method analysis")
        table = filtered.groupby("payment_method", as_index=False).agg(sales=("sales", "sum"), units=("quantity", "sum"), transactions=("sales", "size")).sort_values("sales", ascending=False)
        st.dataframe(table, use_container_width=True, hide_index=True)

st.subheader("🤖 AI Sales Assistant")
st.write("Ask questions about the currently filtered Walmart data.")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
question = st.chat_input("Which category has the highest sales?")
if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    answer = ask_gemini(question, data_context(filtered))
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.chat_history.append({"role": "assistant", "content": answer})

with st.expander("View filtered records"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
st.caption("Built with Python, Pandas, Streamlit, Plotly and Google Gemini.")
