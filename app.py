import streamlit as st
import pandas as pd
from compliance_logic import process_filings

st.set_page_config(page_title="Global Regulatory Compliance Tracker", layout="wide")

st.title("🛡️ Global Regulatory Compliance Tracker")
st.markdown("This dashboard provides a real-time overview of regulatory filing obligations across US (SEC) and UK (FCA/Companies House) jurisdictions.")

df = process_filings('filing_schedule.csv')

df['Due_Date_dt'] = pd.to_datetime(df['Due_Date'])
df['Month'] = df['Due_Date_dt'].dt.strftime('%B %Y')

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

filtered_df = df.copy()

if selected_jurisdiction != "All":
    filtered_df = filtered_df[filtered_df['Jurisdiction'] == selected_jurisdiction]

if selected_month != "All":
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Keep only the most important columns and reorder so Urgency is visible first
display_df = filtered_df[[
    'Filing_Name',
    'Urgency',
    'Days_Remaining',
    'Due_Date',
    'Jurisdiction',
    'Regulator',
    'Firm_Type',
    'Frequency',
    'Status'
]]

total_filings = len(display_df)
overdue = len(display_df[display_df['Urgency'] == 'Overdue'])
due_soon = len(display_df[display_df['Urgency'] == 'Due Soon'])

col1, col2, col3 = st.columns(3)
col1.metric("Total Active Filings", total_filings)
col2.metric("🚨 Overdue", overdue)
col3.metric("⚠️ Due Within 30 Days", due_soon)

st.markdown("---")
st.subheader("Filing Schedule Details")

def color_urgency(val):
    if val == 'Overdue': return 'color: red; font-weight: bold'
    elif val == 'Due Soon': return 'color: orange; font-weight: bold'
    elif val == 'Completed': return 'color: green; font-weight: bold'
    return 'color: black'

styled_df = display_df.style.map(color_urgency, subset=['Urgency'])
st.dataframe(styled_df, use_container_width=True, hide_index=True)
