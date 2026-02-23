import streamlit as st
import pandas as pd
from groq import Groq


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Fintech Intelligence Analyzer",
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

    # Keep only valid aggregators
    df = df[df["Aggregator"].notna()]
    df["Aggregator"] = df["Aggregator"].astype(str)
    df = df[df["Aggregator"].str.strip() != ""]

    return df.reset_index(drop=True)


df = load_data()


# --------------------------------------------------
# RISK SCORING LOGIC
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
# AI ANALYSIS FUNCTION (GROQ)
# --------------------------------------------------
def ai_analysis(data, volume, merchant, risk, license_s, geo, settle, risk_score):

    prompt = f"""
You are a senior fintech strategy consultant.

Payment Aggregator Data:
{data}

Merchant Type: {merchant}
Risk Profile: {risk}
License Status: {license_s}
Geographic Focus: {geo}
Settlement Speed: {settle}
Monthly Volume: ₹{volume:,}
Internal Risk Score: {risk_score}/8

Provide:
1. Strategic Fit
2. Revenue Potential
3. Compliance & Regulatory Risk
4. Scaling Advice
5. Partnership Suitability
6. Red Flags (if any)

Be concise, factual, and practical.
"""

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.25,
    max_tokens=900
)

    return response.choices[0].message.content


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("📊 Fintech Intelligence Analyzer")
st.caption("Internal research & strategy platform for payment aggregators")


# --------------------------------------------------
# SIDEBAR — INPUTS
# --------------------------------------------------
st.sidebar.header("🔧 Analysis Settings")

# Comparison selector (max 2)
aggregators = st.sidebar.multiselect(
    "Select Aggregator(s) (Max 2)",
    sorted(df["Aggregator"].unique()),
    max_selections=2
)

if not aggregators:
    st.info("Please select at least one aggregator")
    st.stop()


volume = st.sidebar.number_input(
    "Monthly Transaction Volume (₹)",
    min_value=0,
    step=100_000,
    value=1_000_000
)

merchant_type = st.sidebar.selectbox(
    "Merchant Type",
    ["D2C", "SaaS", "Marketplace", "Enterprise", "MSME", "Cross-border"]
)

risk_profile = st.sidebar.selectbox(
    "Merchant Risk Level",
    ["Low", "Medium", "High"]
)

license_status = st.sidebar.selectbox(
    "Your License Status",
    ["Licensed PA", "Unlicensed PG", "Startup"]
)

geo_focus = st.sidebar.selectbox(
    "Geographic Focus",
    ["Domestic", "Cross-border", "Global"]
)

settlement_speed = st.sidebar.selectbox(
    "Settlement Preference",
    ["Standard (T+2)", "Fast (T+1)", "Instant"]
)


# --------------------------------------------------
# RISK CALCULATION
# --------------------------------------------------
risk_level, risk_score = calculate_risk(
    risk_profile,
    license_status,
    geo_focus,
    settlement_speed
)


# --------------------------------------------------
# SHOW RISK
# --------------------------------------------------
st.subheader("⚠️ Internal Risk Index")

c1, c2 = st.columns(2)

with c1:
    st.metric("Risk Level", risk_level)

with c2:
    st.metric("Risk Score", f"{risk_score}/8")


# --------------------------------------------------
# FILTER DATA
# --------------------------------------------------
selected = df[df["Aggregator"].isin(aggregators)]


# --------------------------------------------------
# DISPLAY PROFILES
# --------------------------------------------------
st.subheader("🏦 Aggregator Profile(s)")

for _, row in selected.iterrows():

    with st.container():

        st.markdown(f"## {row['Aggregator']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Payment Methods", row["Payment Methods"])
            st.metric("Standard MDR", row["Standard Merchant Fee (MDR)"])

        with col2:
            st.metric("Unlicensed MDR", row["Unlicensed (Standard MDR)"])
            st.metric("Licensed Rate", row["Licensed (Buy Rate/Interchange+)"])

        with col3:
            st.metric("White Labeling", row["White-Labeling Level"])
            st.metric("Annual TPV", row["Annualized TPV (Value) (FY 25-26)"])

        st.write("**Partnership Model:**", row["Partnership model"])
        st.write("**Primary Driver:**", row["Primary Volume Driver"])
        st.write("**Key Clients:**", row["Key Clients"])

        st.write("**Tech Stack:**", row["Technology Stack Highlights"])
        st.write("**Core Tech:**", row["Core/Edge technology"])

        st.divider()


# --------------------------------------------------
# AI ANALYSIS
# --------------------------------------------------
st.subheader("🧠 AI Strategic Report")

if st.button("Run AI Analysis"):

    with st.spinner("Running intelligence analysis..."):

        reports = []

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

            reports.append((row["Aggregator"], result))

    st.success("Analysis Complete")

    for name, report in reports:

        st.markdown(f"### 📋 {name}")
        st.write(report)


# --------------------------------------------------
# RAW DATA
# --------------------------------------------------
with st.expander("📄 View Full Dataset"):
    st.dataframe(df, use_container_width=True)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("Built for internal fintech research, planning, and strategy")