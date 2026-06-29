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
def explain_filing(filing_name, jurisdiction, regulator, urgency, days_remaining, firm_type=""):
    days_int = int(days_remaining)

    if urgency == 'Completed':
        status_context = "Status: Completed (already submitted this cycle)."
        action_instruction = (
            "3. One post-submission best practice (e.g. record retention, audit readiness, or next-cycle preparation).\n"
            "4. Two key documents or records the compliance team should retain or archive after this submission."
        )
    else:
        status_str = f"{abs(days_int)} days {'overdue' if days_int < 0 else 'remaining'}"
        status_context = f"Status: {urgency} — {status_str}."
        action_instruction = (
            "3. The single most important action the compliance team should take right now given the urgency.\n"
            "4. A concise preparation checklist of 3–5 specific items that must be ready before this filing can be submitted "
            "(e.g. specific documents, exhibits, data checks, or agreements that need to be reviewed or updated). "
            "Be specific to this exact filing type — do not give generic advice."
        )

    prompt = (
        f"You are a senior RegTech compliance consultant with deep expertise in SEC, FCA, HMRC, CFTC, NFA, and Companies House filings.\n\n"
        f"Filing: '{filing_name}'\n"
        f"Regulator: '{regulator}' ({jurisdiction})\n"
        f"Firm Type: '{firm_type}'\n"
        f"{status_context}\n\n"
        f"Respond in 4 concise points:\n"
        f"1. What this filing is and what it reports to the regulator.\n"
        f"2. The key regulatory risk or penalty for missing or incorrectly submitting this filing.\n"
        f"{action_instruction}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior RegTech compliance consultant. "
                        "Be concise, specific, and actionable. "
                        "When listing preparation checklist items, be precise to the exact filing type — "
                        "for example, for a 485BPOS mention the transmittal letter, wrap page, Part C exhibits, "
                        "removal of liquidated fund data older than 1 year, and review of IMAs and sub-advisory agreements. "
                        "For Form 13F mention CUSIP verification and the 45-day deadline. "
                        "Always tailor your answer to the specific filing, regulator, and firm type provided."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
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
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Overview",
    "📋 Filing Schedule",
    "📊 Charts",
    "🗂 Manage Filings"
])

# ══════════════════════════════════════════════
# TAB 1 - OVERVIEW: AI Explainer
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-label">AI Compliance Explainer</p>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>"
        "Select any filing from your current filtered view to get a plain-English explanation "
        "and an actionable preparation checklist based on its current urgency status.</p>",
        unsafe_allow_html=True
    )

    if display_df.empty:
        st.info("No filings match the current filters.")
    else:
        display_df = display_df.reset_index(drop=True)
        dropdown_labels = [
            f"{row['Filing_Name']} — {row['Urgency']} ({row['Due_Date']})"
            for _, row in display_df.iterrows()
        ]

        selected_label = st.selectbox(
            "Select a filing:",
            options=["— select a filing —"] + dropdown_labels,
            label_visibility="collapsed"
        )

        if selected_label != "— select a filing —":
            selected_index = dropdown_labels.index(selected_label)
            row = display_df.iloc[selected_index]

            if ai_ready:
                with st.spinner("Generating compliance briefing..."):
                    explanation = explain_filing(
                        filing_name=row['Filing_Name'],
                        jurisdiction=row['Jurisdiction'],
                        regulator=row['Regulator'],
                        urgency=row['Urgency'],
                        days_remaining=row['Days_Remaining'],
                        firm_type=row['Firm_Type']
                    )
                st.markdown(f'<div class="ai-box">{explanation}</div>', unsafe_allow_html=True)
            else:
                st.warning("AI explainer is unavailable — GROQ_API_KEY not configured.")

# ══════════════════════════════════════════════
# TAB 2 - FILING SCHEDULE TABLE
# ══════════════════════════════════════════════
with tab2:
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
        ROW_HEIGHT  = 35
        HEADER_PAD  = 38
        table_height = min(len(display_df) * ROW_HEIGHT + HEADER_PAD, 600)

        styled_table = display_df.style.map(style_urgency, subset=['Urgency'])
        st.dataframe(styled_table, use_container_width=True, hide_index=True, height=table_height)

# ══════════════════════════════════════════════
# TAB 3 - CHARTS (capped at 20 most urgent)
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-label">Deadline Proximity &mdash; Days Remaining by Filing</p>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>"
        "Each bar shows how many days remain until the filing deadline. "
        "Negative values are overdue. The dotted line marks the 30-day action threshold. "
        "Showing the 20 most urgent filings.</p>",
        unsafe_allow_html=True
    )

    if display_df.empty:
        st.info("No filings match the current filters.")
    else:
        # Cap to 20 most urgent (lowest Days_Remaining first)
        chart_df = display_df.sort_values('Days_Remaining').head(20).copy()

        colour_map = {
            'Overdue':   '#e03131',
            'Due Soon':  '#f59f00',
            'On Track':  '#1971c2',
            'Completed': '#2f9e44'
        }

        fig = px.bar(
            chart_df,
            x='Days_Remaining',
            y='Filing_Name',
            orientation='h',
            color='Urgency',
            color_discrete_map=colour_map,
            labels={'Days_Remaining': 'Days Remaining', 'Filing_Name': ''},
            height=max(300, len(chart_df) * 28 + 60)
        )
        fig.add_vline(x=30, line_dash="dot", line_color="#adb5bd", annotation_text="30-day threshold")
        fig.add_vline(x=0,  line_dash="solid", line_color="#868e96", line_width=1)
        fig.update_layout(
            plot_bgcolor='#f7f8fc',
            paper_bgcolor='#f7f8fc',
            font=dict(family='Inter, Segoe UI, sans-serif', size=12),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=10, r=20, t=10, b=40),
            yaxis=dict(autorange='reversed')
        )
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 - MANAGE FILINGS (Database Update Tool)
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-label">Database Update Tool</p>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem;color:#6b7280;margin-top:-0.25rem;margin-bottom:0.75rem;'>"
        "Edit existing filings or add new ones. Use the date picker to set a due date — "
        "Days Remaining will be recalculated automatically when you click Save Changes. "
        "Marking a filing as Submitted will automatically schedule the next cycle.</p>",
        unsafe_allow_html=True
    )

    import os
    from datetime import date, datetime, timedelta

    # Frequency → days mapping for auto-scheduling next cycle
    FREQUENCY_DAYS = {
        "Daily":        1,
        "Monthly":      30,
        "Quarterly":    91,
        "Semi-Annual":  182,
        "Annual":       365,
        "As Required":  None,
    }

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filing_schedule.csv')
    raw_df = pd.read_csv(csv_path, sep=None, engine='python')
    # Convert Due_Date to real date objects for the calendar picker
    raw_df['Due_Date'] = pd.to_datetime(raw_df['Due_Date'], errors='coerce').dt.date

    column_config = {
        "Due_Date": st.column_config.DateColumn(
            "Due Date",
            format="MM/DD/YYYY",
            help="Click to open the date picker"
        ),
        "Days_From_Today": st.column_config.NumberColumn(
            "Days Remaining",
            help="Auto-calculated from Due Date on Save — do not edit manually",
            disabled=True
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Pending", "Submitted", "Overdue"],
        ),
        "Jurisdiction": st.column_config.SelectboxColumn(
            "Jurisdiction",
            options=["US", "UK"]
        ),
    }

    edited_df = st.data_editor(
        raw_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        key="filing_editor"
    )

    # Initialise session state flag
    if 'save_success_msg' not in st.session_state:
        st.session_state.save_success_msg = None

    if st.button("Save Changes", type="primary"):
        try:
            today = date.today()
            new_rows = []

            def recalc_days(due_date_val):
                if pd.isnull(due_date_val) or due_date_val is None:
                    return 0
                if isinstance(due_date_val, str):
                    due_date_val = datetime.strptime(due_date_val, "%Y-%m-%d").date()
                return (due_date_val - today).days

            edited_df['Days_From_Today'] = edited_df['Due_Date'].apply(recalc_days)

            for _, row in edited_df.iterrows():
                if str(row.get('Status', '')).strip() == 'Submitted':
                    freq = str(row.get('Frequency', '')).strip()
                    interval = FREQUENCY_DAYS.get(freq)
                    if interval is not None:
                        existing = edited_df[
                            (edited_df['Filing_Name'] == row['Filing_Name']) &
                            (edited_df['Status'] != 'Submitted')
                        ]
                        if existing.empty:
                            due_date_val = row['Due_Date']
                            if isinstance(due_date_val, str):
                                due_date_val = datetime.strptime(due_date_val, "%Y-%m-%d").date()
                            next_due = due_date_val + timedelta(days=interval)
                            next_days = (next_due - today).days
                            next_row = row.copy()
                            next_row['Due_Date'] = next_due
                            next_row['Days_From_Today'] = next_days
                            next_row['Status'] = 'Pending'
                            new_rows.append(next_row)

            if new_rows:
                next_cycle_df = pd.DataFrame(new_rows)
                edited_df = pd.concat([edited_df, next_cycle_df], ignore_index=True)

            edited_df['Due_Date'] = pd.to_datetime(
                edited_df['Due_Date'], errors='coerce'
            ).dt.strftime('%-m/%-d/%Y')

            edited_df.to_csv(csv_path, index=False)

            n_new = len(new_rows)
            if n_new > 0:
                st.session_state.save_success_msg = f"✅ Saved! {n_new} next-cycle filing(s) auto-scheduled."
            else:
                st.session_state.save_success_msg = "✅ Changes saved successfully!"

            st.rerun()

        except Exception as e:
            st.error(f"Error saving changes: {e}")

    if st.session_state.save_success_msg:
        st.success(st.session_state.save_success_msg)
        st.session_state.save_success_msg = None