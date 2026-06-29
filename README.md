# Global Regulatory Compliance Tracker

A regulatory compliance dashboard built with Python and Streamlit to help teams monitor filing obligations across US (SEC, CFTC, NFA) and UK (FCA, Companies House, HMRC) jurisdictions.

Live Demo: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg )](https://regtech-compliance-dashboard-jpeftg6ajanxph3onhb7vb.streamlit.app/ )

---

## Screenshots

![Main Dashboard - Overview Tab](Screenshot1.png)
*The Overview tab showing real-time KPI cards (44 total filings, 2 overdue, 5 due within 30 days), the action alert banner, the four-tab navigation, and the AI Compliance Explainer with the "Assigned To" filter visible in the sidebar.*

![Filing Schedule - Filtered by Owner](Screenshot2.png)
*The Filing Schedule tab filtered by Jurisdiction: UK and Assigned To: Tom Walsh - showing only Tom's 5 UK FCA filings with Days Remaining, Due Date, Firm Type, and Assigned_To columns.*

![Charts Tab - Due Soon Filter](Screenshot3.png)
*The Charts tab filtered by Urgency Status: Due Soon - showing the Deadline Proximity bar chart capped at the 20 most urgent filings, with the 30-day action threshold dotted line.*

![AI Compliance Explainer - Overdue Filing](Screenshot4.png)
*The AI Compliance Explainer generating a filing-specific briefing for Form 486APOS (Overdue) - including Filing Purpose, Regulatory Risk, Immediate Action, and a 4-item Preparation Checklist with EDGAR filing codes and Part C exhibits.*

![Manage Filings Tab - Database Update Tool](Screenshot5.png)
*The Manage Filings tab showing the Database Update Tool with the calendar date picker open on the Form 40 row, and the Urgency Status filter set to Overdue.*

---

## Project Overview

Rather than relying on manually updated status fields alone, the application recalculates deadline urgency from filing due dates each time it runs, helping teams identify overdue and upcoming obligations more reliably.

The project demonstrates how a maintained filing tracker can be enhanced with automated deadline monitoring, in-app data management, proactive alerts, owner-based filtering, and AI-generated plain-English filing explanations with filing-specific preparation checklists.

---

## Key Features

1. **Automated Deadline Engine**: A Python backend that calculates real-time `Days_Remaining` and dynamically assigns Urgency status (On Track, Due Soon, Overdue, Completed) independently of human input, eliminating stale data risk.
2. **Interactive Web Dashboard**: A live Streamlit application featuring dynamic filters for jurisdiction, due month, urgency status, and assigned owner - allowing individual team members to view only their own filings.
3. **Database Update Tool**: An in-app filing manager (Manage Filings tab) that lets users edit existing filings, add new ones, and update due dates via a calendar date picker - all without touching the CSV file directly. Days Remaining is automatically recalculated on save.
4. **Automatic Next-Cycle Scheduling**: When a filing is marked as Submitted, the system automatically creates a new Pending entry for the next cycle based on the filing's frequency (Daily, Monthly, Quarterly, Semi-Annual, Annual), carrying forward the assigned owner. Ad-hoc filings (As Required) are excluded and must be added manually.
5. **Generative AI Compliance Explainer**: An embedded AI assistant powered by Groq (LLaMA 3.3 70B) that generates plain-English filing summaries, regulatory risk warnings, an immediate action recommendation, and a filing-specific preparation checklist - all tailored to the exact filing type, regulator, firm type, and current urgency status.
6. **Proactive Alerting**: Surfaces overdue and near-term filing risks directly in the dashboard via a dynamic action banner.
7. **Cross-Jurisdiction Tracking**: Monitors US (SEC, CFTC, NFA) and UK (FCA, Companies House, HMRC) regulatory reporting workflows in a single view.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend Logic** | Python 3.11, Pandas, Datetime |
| **Frontend / UI** | Streamlit |
| **AI Integration** | Groq API (LLaMA 3.3 70B model) |
| **Deployment** | Streamlit Community Cloud, GitHub Codespaces |

---

## The Problem It Solves

Traditional compliance teams rely on static Excel trackers where a human must manually update a status from "Pending" to "Overdue." If a team member is absent, the data goes stale, increasing regulatory risk.

This tool solves that by decoupling the human-recorded Status from the machine-calculated Urgency. Every day the application runs, it compares the `Due_Date` against the live system clock and recalculates the urgency automatically. For example, a MiFIR Transaction Report might have a human status of "Pending," but the system will correctly flag it as "Overdue" if the deadline has passed.

---

## Architecture

The project follows a simple pipeline architecture where data flows in one direction:

1. **`filing_schedule.csv`**: The source of truth containing the list of filings, their jurisdiction, relative due dates, owner email, description, and assigned team member.
2. **`compliance_logic.py`**: The backend engine. It reads the CSV, calculates the actual calendar `Due_Date` based on the current system clock, and determines the `Urgency` status (Overdue, Due Soon, On Track, Completed).
3. **`app.py`**: The Streamlit frontend. It imports the processed DataFrame from `compliance_logic.py`, renders the interactive tabbed UI, handles user filtering (including by assigned owner), makes API calls to Groq for the AI Explainer, and manages the Database Update Tool including auto next-cycle scheduling.

The Database Update Tool creates a feedback loop: users can edit the CSV through the UI, and the deadline engine recalculates urgency on the next load.

**Note:** On Streamlit Community Cloud, changes made via the Database Update Tool are written to the server's temporary filesystem and will be lost when the app restarts or redeploys. For persistent changes, update `filing_schedule.csv` in the GitHub repository and redeploy.

---

## Design Choices and Methodology

- **Dynamic Date Calculation**: Instead of hardcoding static dates which would eventually become stale, the CSV stores `Days_From_Today`. The `compliance_logic.py` script calculates the actual date dynamically every time the app runs, keeping the project evergreen and functional for anyone reviewing it months later.
- **Tabbed Layout for Scalability**: The interface is organised into four tabs (Overview, Filing Schedule, Charts, Manage Filings) so each section lives on its own tab rather than stacking vertically. This keeps the UI clean regardless of how many filings are added.
- **Chart Capping**: The Deadline Proximity Chart displays only the 20 most urgent filings (sorted by days remaining), keeping the chart focused and readable as the filing list grows.
- **Two-Layer Secret Management**: For local development in Codespaces, a `.env` file is used (strictly ignored via `.gitignore`). For production, Streamlit Cloud's built-in Secrets management is used. This prevents accidental exposure of the Groq API key while ensuring the app runs smoothly in both environments.
- **Context-Aware AI Prompt Engineering**: The prompt sent to the Groq API is dynamically constructed from the filing name, regulator, firm type, urgency, and days remaining. A single prompt template works for every filing in the CSV - including new ones added by users - without requiring any hardcoded dictionaries. The AI generates filing-specific checklists (e.g. transmittal letters and Part C exhibits for 485BPOS, EDGAR codes for 486APOS) because the model already has this domain knowledge; the prompt simply instructs it to apply it.
- **Duplicate-Aware Auto-Scheduling**: When a filing is marked Submitted, the next-cycle logic checks the live edited table before creating a new row, preventing duplicate Pending entries from being generated on repeated saves.
- **Unique Dropdown Labels for Duplicate Filings**: The AI Explainer dropdown appends urgency status and due date to each label (e.g. `485BPOS - Due Soon (2026-10-10)`), ensuring users can distinguish between multiple open cycles of the same filing.
- **System-Wide Dependency Installation**: The `.devcontainer/devcontainer.json` is configured to run `pip install -r requirements.txt` globally within the container, which is the correct standard approach for Docker-based environments like GitHub Codespaces.

---

## Limitations and Disclaimer

- **Not Financial or Legal Advice**: This dashboard is a portfolio project demonstrating technical implementation of RegTech concepts. It is not intended for use in actual regulatory reporting.
- **Simulated Data**: The filings and deadlines provided in the CSV are representative examples. In a production environment, this system would connect directly to a regulatory data feed or an internal GRC platform API.
- **Stateless Persistence on Cloud**: Changes made via the Database Update Tool on Streamlit Community Cloud are not permanently stored. The CSV resets to the GitHub version on each redeploy. A production version would use a persistent database backend (e.g. Supabase or PostgreSQL).
- **Stateless AI**: The Groq AI integration evaluates each filing in isolation based on the prompt. It does not maintain conversational memory or access to a firm's historical filing data.

---

## How to Run Locally

### Prerequisites
- Python 3.11
- A free API key from [Groq](https://console.groq.com/ )

### Setup Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/nattarw-tech/regtech-compliance-dashboard.git
   cd regtech-compliance-dashboard
   ```

2. Create a `.env` file in the root directory and add your Groq API key:
   ```
   GROQ_API_KEY="your_key_here"
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

---

## About the Author

Built by **Nisrin Shoukat Attarwala**  
MSc Financial Technology & Innovation, Bayes Business School, 2026.

This project is part of a portfolio targeting roles in Fintech, RegTech, and Product Operations.  
See also: [DeFi Wallet Risk Intelligence](https://github.com/nattarw-tech/defi-wallet-risk-intelligence)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect_With_Me-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nisrin-attarwala/)