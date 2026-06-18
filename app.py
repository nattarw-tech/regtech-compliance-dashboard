import streamlit as st
import pandas as pd
import os
import plotly.express as px
from groq import Groq
from compliance_logic import process_filings

# 1. Page Configuration
st.set_page_config(page_title="Global Regulatory Compliance Tracker", layout="wide")

# 2. Initialize Groq Client
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", "").strip())
    ai_ready = True
except Exception as e:
    ai_ready = False
    st.sidebar.error("Groq API key not found. AI features disabled.")

# 3. AI Explainer Function
def explain_filing(filing_name, jurisdiction, regulator):
    """Calls Groq API to explain what a specific filing is and why it matters."""
    prompt = f"""
    Explain the regulatory filing '{filing_name}' required by the '{regulator}' in the '{jurisdiction}'. 
    Provide a brief, plain-English summary (max 3 sentences) explaining:
    1. What the filing is.
    2. Why the regulator requires it.
    3. What the penalty or risk is for missing the deadline.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert RegTech compliance consultant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate explanation. Error: {str(e)}"

# 4. App Title
st.title("🛡️ Global Regulatory Compliance Tracker")
st.markdown("This dashboard provides a real-time overview of regulatory filing obligations across US (SEC) and UK (FCA/Companies House) jurisdictions.")

# 5. Load the Processed Data
df = process_filings('filing_schedule.csv')
df['Due_Date_dt'] = pd.to_datetime(df['Due_Date'])
df['Month'] = df['Due_Date_dt'].dt.strftime('%B %Y')

# 6. Sidebar Filters
st.sidebar.header("Filter Filings")
selected_jurisdiction = st.sidebar.selectbox(
    "Select Jurisdiction",
    options=["All"] + sorted(df['Jurisdiction'].unique().tolist())
)

month_order = df.sort_values('Due_Date_dt')['Month'].unique().tolist()
selected_month = st.sidebar.selectbox(
    "Select Month",
    options=["All"] + month_order
)

# Apply Filters
filtered_df = df.copy()
if selected_jurisdiction != "All":
    filtered_df = filtered_df[filtered_df['Jurisdiction'] == selected_jurisdiction]
if selected_month != "All":
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# 7. Automated Alert Summary
urgent_filings = filtered_df[filtered_df['Urgency'].isin(['Overdue', 'Due Soon'])]
if not urgent_filings.empty:
    st.error(f"⚠️ **Action Required:** You have {len(urgent_filings)} filings that are Overdue or Due Soon.")
else:
    st.success("✅ **All Clear:** No filings are overdue or due within 30 days based on your current filters.")

# 8. Top Level Summary Metrics
display_df = filtered_df[[
    'Filing_Name', 'Urgency', 'Days_Remaining', 'Due_Date',
    'Jurisdiction', 'Regulator', 'Firm_Type', 'Frequency', 'Status'
]]

total_filings = len(display_df)
overdue = len(display_df[display_df['Urgency'] == 'Overdue'])
due_soon = len(display_df[display_df['Urgency'] == 'Due Soon'])

col1, col2, col3 = st.columns(3)
col1.metric("Total Active Filings", total_filings)
col2.metric("🚨 Overdue", overdue)
col3.metric("⚠️ Due Within 30 Days", due_soon)

st.markdown("---")

# 9. Charts Section
color_map = {
    'Overdue': '#e74c3c',
    'Due Soon': '#f39c12',
    'On Track': '#2ecc71',
    'Completed': '#3498db'
}

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Filings by Urgency")
    urgency_counts = display_df['Urgency'].value_counts().reset_index()
    urgency_counts.columns = ['Urgency', 'Count']
    fig1 = px.bar(
        urgency_counts,
        x='Urgency',
        y='Count',
        color='Urgency',
        color_discrete_map=color_map,
        text='Count'
    )
    fig1.update_layout(showlegend=False, height=320, margin=dict(t=20, b=20))
    fig1.update_traces(textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("🌍 Filings by Jurisdiction & Regulator")
    reg_df = display_df.groupby(['Jurisdiction', 'Regulator']).size().reset_index(name='Count')
    fig2 = px.sunburst(
        reg_df,
        path=['Jurisdiction', 'Regulator'],
        values='Count',
        color='Jurisdiction',
        color_discrete_map={'US': '#2980b9', 'UK': '#8e44ad'},
        height=320
    )
    fig2.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 10. AI Explainer Tool
st.subheader("🤖 AI Compliance Explainer")
st.markdown("Select a filing below to get an instant, plain-English explanation of its regulatory requirements and risks.")

filing_to_explain = st.selectbox(
    "Select a filing to explain:",
    options=["-- Select a filing --"] + display_df['Filing_Name'].tolist()
)

if filing_to_explain != "-- Select a filing --" and ai_ready:
    filing_data = display_df[display_df['Filing_Name'] == filing_to_explain].iloc[0]
    with st.spinner(f"Generating explanation for {filing_to_explain}..."):
        explanation = explain_filing(
            filing_name=filing_data['Filing_Name'],
            jurisdiction=filing_data['Jurisdiction'],
            regulator=filing_data['Regulator']
        )
    st.info(explanation)

st.markdown("---")

# 11. Display the Color-Coded Table
st.subheader("📋 Filing Schedule Details")

def color_urgency(val):
    if val == 'Overdue': return 'color: red; font-weight: bold'
    elif val == 'Due Soon': return 'color: orange; font-weight: bold'
    elif val == 'Completed': return 'color: green; font-weight: bold'
    return 'color: black'

styled_df = display_df.style.map(color_urgency, subset=['Urgency'])
st.dataframe(styled_df, use_container_width=True, hide_index=True)

st.markdown("---")

# 12. Live SEC EDGAR Data — Closed-End Fund Filings
st.subheader("📡 Live SEC EDGAR — Closed-End Fund Filings (2026)")
st.markdown(
    "Real filing data sourced from the [SEC EDGAR Closed-End Fund dataset](https://www.sec.gov/data-research/sec-markets-data/closed-end-fund-information ). "
    "Showing the most recent submissions by registered investment companies."
)

@st.cache_data(ttl=86400)  # Cache for 24 hours — the CSV is a daily snapshot
def load_edgar_csv():
    try:
        df_edgar = pd.read_csv('closed-end-investment-company-2026.csv', encoding='utf-8-sig')
        df_edgar.columns = df_edgar.columns.str.strip()
        df_edgar['Filing Date'] = pd.to_datetime(df_edgar['Filing Date'], format='%m/%d/%y', errors='coerce')
        df_edgar = df_edgar.dropna(subset=['Filing Date'])
        df_edgar = df_edgar.sort_values('Filing Date', ascending=False)

        recent = df_edgar.head(20)[['Registrant_Name', 'Filing Type', 'Filing Date', 'City', 'State', 'CIK']].copy()
        recent['Filing Date'] = recent['Filing Date'].dt.strftime('%Y-%m-%d')

        recent['EDGAR Link'] = recent['CIK'].apply(
            lambda cik: f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={str(cik ).zfill(10)}&type=&dateb=&owner=include&count=10"
        )
        recent = recent.drop(columns=['CIK'])
        recent = recent.rename(columns={
            'Registrant_Name': 'Fund Name',
            'Filing Type': 'Form Type',
            'Filing Date': 'Filed On',
        })
        return recent, None
    except Exception as e:
        return pd.DataFrame(), str(e)

edgar_df, error = load_edgar_csv()

if error:
    st.warning(f"Could not load SEC EDGAR data: {error}")
elif edgar_df.empty:
    st.info("No data available.")
else:
    e_col1, e_col2, e_col3 = st.columns(3)
    e_col1.metric("Filings Shown", len(edgar_df))
    e_col2.metric("Unique Form Types", edgar_df['Form Type'].nunique())
    e_col3.metric("Most Recent Filing", edgar_df['Filed On'].max())

    form_counts = edgar_df['Form Type'].value_counts().reset_index()
    form_counts.columns = ['Form Type', 'Count']
    fig3 = px.bar(
        form_counts,
        x='Form Type',
        y='Count',
        text='Count',
        title='Form Types in Latest 20 Filings',
        color='Count',
        color_continuous_scale='Blues'
    )
    fig3.update_layout(height=250, margin=dict(t=40, b=20), showlegend=False, coloraxis_showscale=False)
    fig3.update_traces(textposition='outside')
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(
        edgar_df,
        column_config={
            "EDGAR Link": st.column_config.LinkColumn("EDGAR Profile")
        },
        use_container_width=True,
        hide_index=True
    )
    st.caption("Source: U.S. Securities and Exchange Commission — EDGAR Closed-End Fund Information (2026)")
