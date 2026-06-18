import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
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
# CUSTOM CSS — clean, professional, distinctive
# No animations. Muted navy/slate palette.
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global font & background ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #f7f8fc;
    color: #1a1f36;
}

/* ── Remove default Streamlit top padding ── */
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Page header ── */
.page-header {
    padding: 1.5rem 0 0.5rem 0;
    border-bottom: 2px solid #e2e6f0;
    margin-bottom: 1.5rem;
}
.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1a1f36;
    margin: 0;
    letter-spacing: -0.3px;
}
.page-header p {
    font-size: 0.9rem;
    color: #6b7280;
    margin: 0.25rem 0 0 0;
}

/* ── Section label ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 0.5rem;
}

/* ── Alert banner ── */
.alert-overdue {
    background: #fff5f5;
    border: 1px solid #ffc9c9;
    border-left: 4px solid #e03131;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    color: #c92a2a;
    margin-bottom: 1.25rem;
}
.alert-clear {
    background: #ebfbee;
    border: 1px solid #b2f2bb;
    border-left: 4px solid #2f9e44;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    color: #2b8a3e;
    margin-bottom: 1.25rem;
}

/* ── AI explainer box ── */
.ai-box {
    background: #f0f4ff;
    border: 1px solid #bac8ff;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-size: 0.9rem;
    color: #1a1f36;
    line-height: 1.6;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e6f0;
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ── Divider ── */
hr { border: none; border-top: 1px solid #e2e6f0; margin: 1.5rem 0; }

/* ── Hide Streamlit default branding ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", "").strip())
    ai_ready = True
except Exception:
    ai_ready = False

# ─────────────────────────────────────────────
# AI EXPLAINER FUNCTION
# ─────────────────────────────────────────────
def explain_filing(filing_name, jurisdiction, regulator, urgency, days_remaining):
    prompt = f"""
You are a senior RegTech compliance consultant. A compliance officer is reviewing their filing schedule.

Filing: '{filing_name}'
Regulator: '{regulator}' ({jurisdiction})
Status: {urgency} — {abs(int(days_remaining))} days {'overdue' if int(days_remaining) < 0 else 'remaining'}

In 3 concise sentences:
1. What this filing is and what it reports to the regulator.
2. The key regulatory risk or penalty for non-compliance.
3. One practical action the compliance team should take right now given the urgency status above.
"""
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
    st.markdown("### ⚖️ RegTrack")
    st.markdown("<p style='font-size:0.78rem;color:#6b7280;margin-top:-0.5rem;'>Regulatory Compliance Dashboard</p>", unsafe_allow_html=True)
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

    urgency_options = ["All", "Overdue", "Due Soon", "On Track", "Completed"]
    selected_urgency = st.selectbox(
        "Urgency Status",
        options=urgency_options,
        help="Filter by compliance urgency"
    )

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem;color:#9ca3af;'>Built by Nisrin Shoukat Attarwala  
MSc FinTech · Bayes Business School</p>", unsafe_allow_html=True)

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
  <h1>⚖️ RegTrack — Regulatory Compliance Dashboard</h1>
  <p>Real-time filing obligation tracker across US SEC and UK FCA / Companies House jurisdictions</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ALERT BANNER
# ─────────────────────────────────────────────
overdue_count = len(display_df[display_df['Urgency'] == 'Overdue'])
due_soon_count = len(display_df[display_df['Urgency'] == 'Due Soon'])

if overdue_count > 0 or due_soon_count > 0:
    parts = []
    if overdue_count > 0:
        parts.append(f"<strong>{overdue_count} overdue</strong>")
    if due_soon_count > 0:
        parts.append(f"<strong>{due_soon_count} due within 30 days</strong>")
    st.markdown(f'<div class="alert-overdue">⚠ Action required — {" and ".join(parts)} based on current filters.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert-clear">✓ All clear — no filings are overdue or due within 30 days based on current filters.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
total = len(display_df)
completed = len(display_df[display_df['Urgency'] == 'Completed'])
on_track = len(display_df[display_df['Urgency'] == 'On Track'])

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Filings", total, help="Filings matching current filters")
with kpi2:
    st.metric("🔴 Overdue", overdue_count, help="Past their due date and not submitted")
with kpi3:
    st.metric("🟡 Due Within 30 Days", due_soon_count, help="Require immediate attention")
with kpi4:
    st.metric("✅ Completed / On Track", completed + on_track, help="Submitted or comfortably within deadline")

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 1 — FILING SCHEDULE TABLE
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

styled_table = display_df.style.map(style_urgency, subset=['Urgency'])
st.dataframe(styled_table, use_container_width=True, hide_index=True, height=320)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 2 — DEADLINE PROXIMITY CHART
# Answers: which filings are closest to their
# deadline and how urgent are they?
# ─────────────────────────────────────────────
st.markdown('<p class="section-label">Deadline Proximity — Days Remaining by Filing</p>', unsafe_allow_html=True)
st.markdown("<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>Each bar shows how many days remain until the filing deadline. Negative values are overdue. The dotted line marks the 30-day action threshold.</p>", unsafe_allow_html=True)

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
        height=max(280, len(chart_df) * 42)
    )
    fig.update_traces(
        texttemplate='%{text}d',
        textposition='outside',
        marker_line_width=0
    )
    fig.update_layout(
        plot_bgcolor='#f7f8fc',
        paper_bgcolor='#f7f8fc',
        font=dict(family='Inter, Segoe UI, sans-serif', size=12, color='#1a1f36'),
        xaxis=dict(showgrid=True, gridcolor='#e2e6f0', zeroline=True, zerolinecolor='#adb5bd', zerolinewidth=1.5),
        yaxis=dict(showgrid=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title=''),
        margin=dict(l=10, r=60, t=10, b=30)
    )
    fig.add_vline(x=30, line_dash="dot", line_color="#adb5bd",
                  annotation_text="30-day threshold",
                  annotation_position="top right",
                  annotation_font_size=10)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No filings to display for the current filter selection.")

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 3 — AI COMPLIANCE EXPLAINER
# Context-aware: knows urgency + days remaining
# Only shows filings from the filtered view
# ─────────────────────────────────────────────
st.markdown('<p class="section-label">AI Compliance Explainer</p>', unsafe_allow_html=True)
st.markdown("<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>Select any filing from your current filtered view to get a plain-English explanation and an actionable recommendation based on its current urgency status.</p>", unsafe_allow_html=True)

if display_df.empty:
    st.info("No filings match the current filters. Adjust the sidebar to see filings.")
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
# SECTION 4 — SEC EDGAR CROSS-REFERENCE PANEL
# Only shown when jurisdiction = All or US
# ─────────────────────────────────────────────
if selected_jurisdiction in ("All", "US"):
    st.markdown('<p class="section-label">SEC EDGAR Reference — Closed-End Fund Filing Universe (2026)</p>', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>Cross-reference panel: real SEC EDGAR data showing which form types closed-end funds are currently filing. Use this to verify your own SEC obligations are complete and to identify any form types your firm may have missed.</p>", unsafe_allow_html=True)

    @st.cache_data(ttl=86400)
    def load_edgar_csv():
        try:
            df_e = pd.read_csv('closed-end-investment-company-2026.csv', encoding='utf-8-sig')
            df_e.columns = df_e.columns.str.strip()
            df_e['Filing Date'] = pd.to_datetime(df_e['Filing Date'], format='%m/%d/%y', errors='coerce')
            df_e = df_e.dropna(subset=['Filing Date'])
            return df_e, None
        except Exception as ex:
            return pd.DataFrame(), str(ex)

    edgar_full, edgar_error = load_edgar_csv()

    if edgar_error:
        st.warning(f"Could not load SEC EDGAR reference data: {edgar_error}")
    elif edgar_full.empty:
        st.info("No data available.")
    else:
        tracker_sec_forms = display_df[display_df['Jurisdiction'] == 'US']['Filing_Name'].tolist()
        edgar_form_types = sorted(edgar_full['Filing Type'].unique().tolist())

        ref_col1, ref_col2 = st.columns([1, 2])

        with ref_col1:
            st.markdown("**Your SEC Filings in Tracker**")
            if tracker_sec_forms:
                for f in tracker_sec_forms:
                    row = display_df[display_df['Filing_Name'] == f].iloc[0]
                    colour = {'Overdue': '#e03131', 'Due Soon': '#f08c00', 'On Track': '#2f9e44', 'Completed': '#1971c2'}.get(row['Urgency'], '#6b7280')
                    st.markdown(f"<span style='font-size:0.82rem;'><span style='color:{colour};font-weight:700;'>●</span> {f} <span style='color:#9ca3af;font-size:0.75rem;'>({row['Urgency']})</span></span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='font-size:0.82rem;color:#9ca3af;'>No US SEC filings in current filter.</span>", unsafe_allow_html=True)

            st.markdown("  
**EDGAR Form Types Filed (2026)**", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:0.82rem;color:#6b7280;'>{len(edgar_form_types)} distinct form types filed by {edgar_full['Registrant_Name'].nunique()} registered funds</p>", unsafe_allow_html=True)
            top_forms = edgar_full['Filing Type'].value_counts().head(8)
            for form, count in top_forms.items():
                st.markdown(f"<span style='font-size:0.8rem;'><code>{form}</code> — {count} filings</span>", unsafe_allow_html=True)

        with ref_col2:
            st.markdown("**Most Recent Filings (latest 15)**")
            recent = edgar_full.sort_values('Filing Date', ascending=False).head(15).copy()
            recent['Filed On'] = recent['Filing Date'].dt.strftime('%Y-%m-%d')
            recent['EDGAR'] = recent['CIK'].apply(
                lambda c: f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={str(c ).zfill(10)}&type=&dateb=&owner=include&count=10"
            )
            show = recent[['Registrant_Name', 'Filing Type', 'Filed On', 'City', 'State', 'EDGAR']].rename(columns={
                'Registrant_Name': 'Fund Name', 'Filing Type': 'Form'
            })
            st.dataframe(
                show,
                column_config={"EDGAR": st.column_config.LinkColumn("EDGAR Profile")},
                use_container_width=True,
                hide_index=True,
                height=380
            )
        st.caption("Source: U.S. Securities and Exchange Commission — EDGAR Closed-End Fund Information (2026) · sec.gov/data-research")
