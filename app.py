import streamlit as st
import pandas as pd
import os
import plotly.express as px
from groq import Groq
from compliance_logic import process_filings

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RegTrack — Regulatory Compliance Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #f7f8fc;
    color: #1a1f36;
}
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.page-header {
    padding: 1.5rem 0 0.5rem 0;
    border-bottom: 2px solid #e2e6f0;
    margin-bottom: 1.5rem;
}
.page-header h1 { font-size: 1.75rem; font-weight: 700; color: #1a1f36; margin: 0; letter-spacing: -0.3px; }
.page-header p  { font-size: 0.9rem; color: #6b7280; margin: 0.25rem 0 0 0; }
.section-label  {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #6b7280; margin-bottom: 0.5rem;
}
.alert-overdue {
    background: #fff5f5; border: 1px solid #ffc9c9; border-left: 4px solid #e03131;
    border-radius: 6px; padding: 0.75rem 1rem; font-size: 0.875rem;
    color: #c92a2a; margin-bottom: 1.25rem;
}
.alert-clear {
    background: #ebfbee; border: 1px solid #b2f2bb; border-left: 4px solid #2f9e44;
    border-radius: 6px; padding: 0.75rem 1rem; font-size: 0.875rem;
    color: #2b8a3e; margin-bottom: 1.25rem;
}
.ai-box {
    background: #f0f4ff; border: 1px solid #bac8ff; border-radius: 8px;
    padding: 1rem 1.25rem; font-size: 0.9rem; color: #1a1f36; line-height: 1.6;
}
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e6f0; }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
hr { border: none; border-top: 1px solid #e2e6f0; margin: 1.5rem 0; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", "").strip())
    ai_ready = bool(os.environ.get("GROQ_API_KEY", "").strip())
except Exception:
    ai_ready = False

# ─────────────────────────────────────────────
# AI EXPLAINER FUNCTION
# ─────────────────────────────────────────────
def explain_filing(filing_name, jurisdiction, regulator, urgency, days_remaining):
    days_int = int(days_remaining)

    if urgency == 'Completed':
        prompt = (
            f"You are a senior RegTech compliance consultant.\n\n"
            f"Filing: '{filing_name}'\n"
            f"Regulator: '{regulator}' ({jurisdiction})\n"
            f"Status: Completed (already submitted)\n\n"
            f"In 3 concise sentences:\n"
            f"1. What this filing is and what it reports to the regulator.\n"
            f"2. Confirm that this filing has been successfully submitted and no further action is required for this cycle.\n"
            f"3. One practical post-submission best practice the compliance team should follow "
            f"(e.g. retaining records, preparing for the next cycle, or ensuring audit readiness)."
        )
    else:
        status_str = f"{abs(days_int)} days {'overdue' if days_int < 0 else 'remaining'}"
        prompt = (
            f"You are a senior RegTech compliance consultant.\n\n"
            f"Filing: '{filing_name}'\n"
            f"Regulator: '{regulator}' ({jurisdiction})\n"
            f"Status: {urgency} — {status_str}\n\n"
            f"In 3 concise sentences:\n"
            f"1. What this filing is and what it reports to the regulator.\n"
            f"2. The key regulatory risk or penalty for non-compliance.\n"
            f"3. One practical action the compliance team should take right now given the urgency status above."
        )
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a senior RegTech compliance consultant. Be concise and actionable."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate explanation: {str(e)}"

# ─────────────────────────────────────────────
# LOAD & PROCESS DATA
# ─────────────────────────────────────────────
df = process_filings('filing_schedule.csv')
df['Due_Date_dt'] = pd.to_datetime(df['Due_Date'])
df['Month'] = df['Due_Date_dt'].dt.strftime('%B %Y')

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### RegTrack")
    st.markdown(
        "<p style='font-size:0.78rem;color:#6b7280;margin-top:-0.5rem;'>Regulatory Compliance Dashboard</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("**Filter Filings**")

    selected_jurisdiction = st.selectbox(
        "Jurisdiction",
        options=["All"] + sorted(df['Jurisdiction'].unique().tolist()),
        help="Filter by regulatory jurisdiction"
    )

    month_order = df.sort_values('Due_Date_dt')['Month'].unique().tolist()
    selected_month = st.selectbox(
        "Due Month",
        options=["All"] + month_order,
        help="Filter by the month the filing is due"
    )

    selected_urgency = st.selectbox(
        "Urgency Status",
        options=["All", "Overdue", "Due Soon", "On Track", "Completed"],
        help="Filter by compliance urgency"
    )

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.75rem;color:#9ca3af;'>Built by Nisrin Shoukat Attarwala<br/>MSc Financial Technology &amp; Innovation<br/>Bayes Business School<br/>2026</p>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
filtered_df = df.copy()
if selected_jurisdiction != "All":
    filtered_df = filtered_df[filtered_df['Jurisdiction'] == selected_jurisdiction]
if selected_month != "All":
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]
if selected_urgency != "All":
    filtered_df = filtered_df[filtered_df['Urgency'] == selected_urgency]

display_df = filtered_df[[
    'Filing_Name', 'Urgency', 'Days_Remaining', 'Due_Date',
    'Jurisdiction', 'Regulator', 'Firm_Type', 'Frequency', 'Status'
]].copy()

# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>RegTrack &mdash; Regulatory Compliance Dashboard</h1>
  <p>Filing obligation tracker across US (SEC / CFTC / NFA) and UK (FCA / Companies House / HMRC) jurisdictions</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ALERT BANNER
# ─────────────────────────────────────────────
overdue_count   = len(display_df[display_df['Urgency'] == 'Overdue'])
due_soon_count  = len(display_df[display_df['Urgency'] == 'Due Soon'])
completed_count = len(display_df[display_df['Urgency'] == 'Completed'])
on_track_count  = len(display_df[display_df['Urgency'] == 'On Track'])
total           = len(display_df)

if overdue_count > 0 or due_soon_count > 0:
    parts = []
    if overdue_count > 0:
        parts.append(f"<strong>{overdue_count} overdue</strong>")
    if due_soon_count > 0:
        parts.append(f"<strong>{due_soon_count} due within 30 days</strong>")
    st.markdown(
        f'<div class="alert-overdue">&#9888; Action required &mdash; {" and ".join(parts)} based on current filters.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="alert-clear">&#10003; All clear &mdash; no filings are overdue or due within 30 days based on current filters.</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# FIX 1 — KPI CARDS: 5 separate cards, Completed and On Track split
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Filings", total)
with k2:
    st.metric("Overdue", overdue_count)
with k3:
    st.metric("Due Within 30 Days", due_soon_count)
with k4:
    st.metric("On Track", on_track_count)
with k5:
    st.metric("Completed", completed_count)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FIX 3 — AI COMPLIANCE EXPLAINER moved ABOVE the filing schedule table
# ─────────────────────────────────────────────
st.markdown('<p class="section-label">AI Compliance Explainer</p>', unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>"
    "Select any filing from your current filtered view to get a plain-English explanation "
    "and an actionable recommendation based on its current urgency status.</p>",
    unsafe_allow_html=True
)

if display_df.empty:
    st.info("No filings match the current filters.")
else:
    filing_to_explain = st.selectbox(
        "Select a filing:",
        options=["— select a filing —"] + display_df['Filing_Name'].tolist(),
        label_visibility="collapsed"
    )
    if filing_to_explain != "— select a filing —":
        row = display_df[display_df['Filing_Name'] == filing_to_explain].iloc[0]
        if ai_ready:
            with st.spinner("Generating compliance briefing..."):
                explanation = explain_filing(
                    filing_name=row['Filing_Name'],
                    jurisdiction=row['Jurisdiction'],
                    regulator=row['Regulator'],
                    urgency=row['Urgency'],
                    days_remaining=row['Days_Remaining']
                )
            st.markdown(f'<div class="ai-box">{explanation}</div>', unsafe_allow_html=True)
        else:
            st.warning("AI explainer is unavailable — GROQ_API_KEY not configured.")

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILING SCHEDULE TABLE
# FIX 2 — table height auto-sizes to actual row count; no blank rows on filter
# ─────────────────────────────────────────────
st.markdown('<p class="section-label">Filing Schedule</p>', unsafe_allow_html=True)

def style_urgency(val):
    colours = {
        'Overdue':   'color: #c92a2a; font-weight: 700;',
        'Due Soon':  'color: #e67700; font-weight: 700;',
        'Completed': 'color: #2b8a3e; font-weight: 700;',
        'On Track':  'color: #1a1f36;'
    }
    return colours.get(val, '')

if display_df.empty:
    st.info("No filings match the current filters.")
else:
    ROW_HEIGHT   = 35   # px per data row
    HEADER_PAD   = 38   # px for the header row
    # Height is calculated from the actual number of rows in the filtered result
    # so the table shrinks cleanly when filters reduce the row count
    table_height = len(display_df) * ROW_HEIGHT + HEADER_PAD

    styled_table = display_df.style.map(style_urgency, subset=['Urgency'])
    st.dataframe(styled_table, use_container_width=True, hide_index=True, height=table_height)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DEADLINE PROXIMITY CHART
# ─────────────────────────────────────────────
st.markdown('<p class="section-label">Deadline Proximity &mdash; Days Remaining by Filing</p>', unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>"
    "Each bar shows how many days remain until the filing deadline. "
    "Negative values are overdue. The dotted line marks the 30-day action threshold.</p>",
    unsafe_allow_html=True
)

colour_map = {
    'Overdue':   '#e03131',
    'Due Soon':  '#f08c00',
    'On Track':  '#2f9e44',
    'Completed': '#1971c2'
}

if not display_df.empty:
    chart_df = display_df.sort_values('Days_Remaining')
    fig = px.bar(
        chart_df,
        x='Days_Remaining',
        y='Filing_Name',
        orientation='h',
        color='Urgency',
        color_discrete_map=colour_map,
        text='Days_Remaining',
        labels={'Days_Remaining': 'Days Until Due (negative = overdue)', 'Filing_Name': ''},
        height=max(300, len(chart_df) * 42)
    )
    fig.update_traces(texttemplate='%{text}d', textposition='outside', marker_line_width=0)
    fig.update_layout(
        plot_bgcolor='#f7f8fc',
        paper_bgcolor='#f7f8fc',
        font=dict(family='Inter, Segoe UI, sans-serif', size=12, color='#1a1f36'),
        xaxis=dict(showgrid=True, gridcolor='#e2e6f0', zeroline=True, zerolinecolor='#adb5bd', zerolinewidth=1.5),
        yaxis=dict(showgrid=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title=''),
        margin=dict(l=10, r=70, t=10, b=30)
    )
    fig.add_vline(
        x=30, line_dash="dot", line_color="#adb5bd",
        annotation_text="30-day threshold",
        annotation_position="top right",
        annotation_font_size=10
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No filings to display for the current filter selection.")