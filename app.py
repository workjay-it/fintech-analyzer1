import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
import os
from datetime import datetime


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Fintech Intelligence Platform",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# GROQ CLIENT
# --------------------------------------------------
client = Groq(api_key=st.secrets["GROQ_KEY"])


# --------------------------------------------------
# LOAD & CLEAN DATA
# --------------------------------------------------
@st.cache_data
def load_data():

    df = pd.read_excel("Payment Aggregator Research Report v1i.xlsx")

    df = df[df["Aggregator"].notna()]
    df["Aggregator"] = df["Aggregator"].astype(str)
    df = df[df["Aggregator"].str.strip() != ""]

    return df.reset_index(drop=True)


df = load_data()


# --------------------------------------------------
# CLEAN NUMBERS (₹, commas etc.)
# --------------------------------------------------
def clean_number(x):

    if pd.isna(x):
        return 0

    x = str(x)
    x = x.replace("₹", "").replace(",", "").replace("Cr", "").strip()

    try:
        return float(x)
    except:
        return 0


# --------------------------------------------------
# MARKET SNAPSHOT
# --------------------------------------------------
def save_market_snapshot(df):

    period = datetime.today().strftime("%Y-%m")

    snap = df.copy()
    snap["Period"] = period

    snap = snap[
        [
            "Period",
            "Aggregator",
            "Standard Merchant Fee (MDR)",
            "Annualized TPV (Value) (FY 25-26)",
            "Key Clients"
        ]
    ]

    file = "market_history.xlsx"

    if os.path.exists(file):
        old = pd.read_excel(file)
        snap = pd.concat([old, snap], ignore_index=True)

    snap.to_excel(file, index=False)


# --------------------------------------------------
# RISK SCORING
# --------------------------------------------------
def calculate_risk(risk, license_status, geo, settlement):

    score = 0

    score += {"Low": 1, "Medium": 2, "High": 3}[risk]

    if license_status != "Licensed PA":
        score += 2

    if geo != "Domestic":
        score += 2

    if settlement == "Instant":
        score += 1

    if score <= 3:
        return "Low", score
    elif score <= 6:
        return "Medium", score
    else:
        return "High", score


# --------------------------------------------------
# AI ANALYSIS (GROQ)
# --------------------------------------------------
def ai_analysis(data, volume, merchant, risk, license_s, geo, settle, risk_score):

    prompt = f"""
You are a fintech strategy consultant.

Aggregator Data:
{data}

Merchant Type: {merchant}
Risk Profile: {risk}
License Status: {license_s}
Geography: {geo}
Settlement: {settle}
Monthly Volume: ₹{volume:,}
Internal Risk Score: {risk_score}/8

Provide:
1. Strategic Fit
2. Revenue Potential
3. Compliance Risk
4. Scaling Advice
5. Red Flags
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    return res.choices[0].message.content


# --------------------------------------------------
# HEADER + TABS
# --------------------------------------------------
st.title("📊 Fintech Intelligence Platform")
st.caption("Internal research, analytics & market monitoring")

tab1, tab2 = st.tabs([
    "🏦 Company Analysis",
    "📈 Market Analysis"
])


# ==================================================
# TAB 1 — COMPANY ANALYSIS
# ==================================================
with tab1:

    # ---------------- SIDEBAR ----------------
    st.sidebar.header("🔧 Analysis Settings")

    aggregators = st.sidebar.multiselect(
        "Select Aggregator(s) (Max 2)",
        sorted(df["Aggregator"].unique()),
        max_selections=2
    )

    if not aggregators:
        st.info("Select at least one aggregator")
        st.stop()

    volume = st.sidebar.number_input(
        "Monthly Volume (₹)",
        min_value=0,
        step=100000,
        value=1000000
    )

    merchant_type = st.sidebar.selectbox(
        "Merchant Type",
        ["D2C", "SaaS", "Marketplace", "Enterprise", "MSME", "Cross-border"]
    )

    risk_profile = st.sidebar.selectbox(
        "Merchant Risk",
        ["Low", "Medium", "High"]
    )

    license_status = st.sidebar.selectbox(
        "License Status",
        ["Licensed PA", "Unlicensed PG", "Startup"]
    )

    geo_focus = st.sidebar.selectbox(
        "Geography",
        ["Domestic", "Cross-border", "Global"]
    )

    settlement_speed = st.sidebar.selectbox(
        "Settlement",
        ["Standard (T+2)", "Fast (T+1)", "Instant"]
    )


    # ---------------- RISK ----------------
    risk_level, risk_score = calculate_risk(
        risk_profile,
        license_status,
        geo_focus,
        settlement_speed
    )

    st.subheader("⚠️ Internal Risk Index")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Risk Level", risk_level)

    with c2:
        st.metric("Risk Score", f"{risk_score}/8")


    # ---------------- DATA ----------------
    selected = df[df["Aggregator"].isin(aggregators)]


    # ---------------- VISUAL: MARKET SHARE ----------------
    st.subheader("📊 Market Share (TPV)")

    tpv_df = df[["Aggregator", "Annualized TPV (Value) (FY 25-26)"]].copy()
    tpv_df["TPV"] = tpv_df.iloc[:, 1].apply(clean_number)

    fig_pie = px.pie(
        tpv_df,
        values="TPV",
        names="Aggregator",
        title="Market Share by TPV"
    )

    st.plotly_chart(fig_pie, use_container_width=True)


    # ---------------- VISUAL: MDR ----------------
    st.subheader("💳 MDR Comparison")

    mdr_df = df[["Aggregator", "Standard Merchant Fee (MDR)"]].copy()
    mdr_df["MDR"] = mdr_df.iloc[:, 1].apply(clean_number)

    fig_bar = px.bar(
        mdr_df,
        x="Aggregator",
        y="MDR",
        title="MDR by Aggregator",
        text="MDR"
    )

    st.plotly_chart(fig_bar, use_container_width=True)


    # ---------------- PROFILES ----------------
    st.subheader("🏦 Aggregator Profiles")

    for _, row in selected.iterrows():

        st.markdown(f"## {row['Aggregator']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("MDR", row["Standard Merchant Fee (MDR)"])
            st.metric("Payment Methods", row["Payment Methods"])

        with col2:
            st.metric("Unlicensed MDR", row["Unlicensed (Standard MDR)"])
            st.metric("White Label", row["White-Labeling Level"])

        with col3:
            st.metric("Annual TPV", row["Annualized TPV (Value) (FY 25-26)"])
            st.metric("Clients", row["Key Clients"])

        st.write("**Partnership Model:**", row["Partnership model"])
        st.write("**Tech Stack:**", row["Technology Stack Highlights"])

        st.divider()


    # ---------------- AI ----------------
    st.subheader("🧠 AI Strategic Report")

    if st.button("Run AI Analysis"):

        with st.spinner("Analyzing..."):

            for _, row in selected.iterrows():

                data_dict = {
                    "Name": row["Aggregator"],
                    "MDR": row["Standard Merchant Fee (MDR)"],
                    "TPV": row["Annualized TPV (Value) (FY 25-26)"],
                    "Clients": row["Key Clients"],
                    "Tech": row["Technology Stack Highlights"]
                }

                result = ai_analysis(
                    data_dict,
                    volume,
                    merchant_type,
                    risk_profile,
                    license_status,
                    geo_focus,
                    settlement_speed,
                    risk_score
                )

                st.markdown(f"### 📋 {row['Aggregator']}")
                st.write(result)



# ==================================================
# TAB 2 — MARKET ANALYSIS
# ==================================================
with tab2:

    st.header("📈 Market Analysis & Reports")


    # -------- SNAPSHOT --------
    if st.button("📸 Save Monthly Snapshot"):
        save_market_snapshot(df)
        st.success("Snapshot saved")


    # -------- HISTORY --------
    if not os.path.exists("market_history.xlsx"):
        st.warning("No history yet. Save snapshot first.")
        st.stop()

    history = pd.read_excel("market_history.xlsx")


    st.subheader("📊 Historical Data")
    st.dataframe(history, use_container_width=True)


    # -------- TPV TREND --------
    st.subheader("📈 TPV Trend")

    history["TPV"] = history["Annualized TPV (Value) (FY 25-26)"].apply(clean_number)

    trend = history.groupby(
        ["Period", "Aggregator"]
    )["TPV"].sum().reset_index()

    fig_trend = px.line(
        trend,
        x="Period",
        y="TPV",
        color="Aggregator",
        markers=True,
        title="TPV Growth Over Time"
    )

    st.plotly_chart(fig_trend, use_container_width=True)


    # -------- REPORT --------
    report_type = st.selectbox(
        "Report Type",
        ["Monthly", "Quarterly"]
    )

    if st.button("🧠 Generate Market Report"):

        rows = len(df)

        latest = history.tail(rows)
        previous = history.iloc[:-rows].tail(rows)

        if previous.empty:
            st.warning("Not enough historical data")
        else:

            prompt = f"""
You are a fintech market analyst.

Previous Period:
{previous}

Current Period:
{latest}

Generate a {report_type} report covering:

1. Market trends
2. Pricing changes
3. Market leaders
4. Risk signals
5. Regulatory impact
6. Outlook
"""

            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=900
            )

            st.subheader("📄 Market Intelligence Report")
            st.write(res.choices[0].message.content)



# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("Built for internal fintech research & analytics")