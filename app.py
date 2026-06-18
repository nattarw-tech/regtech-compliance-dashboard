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
    prompt = f"""
    Explain the regulatory filing '{filing_name}' required by the '{regulator}' in '{jurisdiction}'. 
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

# 8b. Charts Section
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Filings by Urgency")
    urgency_counts = display_df['Urgency'].value_counts().reset_index()
    urgency_counts.columns = ['Urgency', 'Count']
    color_map = {
        'Overdue': '#e74c3c',
        'Due Soon': '#f39c12',
        'On Track': '#2ecc71',
        'Completed': '#3498db'
    }
    fig1 = px.bar(
        urgency_counts,
        x='Urgency',
        y='Count',
        color='Urgency',
        color_discrete_map=color_map,
        text='Count'
    )
    fig1.update_layout(showlegend=False, height=300, margin=dict(t=20, b=20))
    fig1.update_traces(textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("📅 Filing Timeline")
    timeline_df = display_df.sort_values('Days_Remaining')
    fig2 = px.bar(
        timeline_df,
        x='Days_Remaining',
        y='Filing_Name',
        orientation='h',
        color='Urgency',
        color_discrete_map=color_map,
        labels={'Days_Remaining': 'Days Until Due', 'Filing_Name': ''}
    )
    fig2.update_layout(height=300, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 9. AI Explainer Tool
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

# 10. Display the Color-Coded Table
st.subheader("Filing Schedule Details")

def color_urgency(val):
    if val == 'Overdue': return 'color: red; font-weight: bold'
    elif val == 'Due Soon': return 'color: orange; font-weight: bold'
    elif val == 'Completed': return 'color: green; font-weight: bold'
    return 'color: black'

styled_df = display_df.style.map(color_urgency, subset=['Urgency'])
st.dataframe(styled_df, use_container_width=True, hide_index=True)
