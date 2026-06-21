# Global Regulatory Compliance Tracker

## Project Overview

A regulatory compliance dashboard built with Python and Streamlit to help teams monitor filing obligations across US (SEC) and UK (FCA/Companies House) jurisdictions.

Rather than relying on manually updated status fields alone, the application recalculates deadline urgency from filing due dates each time it runs, helping teams identify overdue and upcoming obligations more reliably.

The project demonstrates how a maintained filing tracker can be enhanced with automated deadline monitoring, proactive alerts, and AI-generated plain-English filing explanations.

Live Demo: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://regtech-compliance-dashboard-jpeftg6ajanxph3onhb7vb.streamlit.app/)

---

## Key Features

1. **Automated Deadline Engine**: A Python backend that calculates real-time `Days_Remaining` and dynamically assigns Urgency status (On Track, Due Soon, Overdue) independently of human input, eliminating stale data risk.
2. **Interactive Web Dashboard**: A live Streamlit application featuring dynamic jurisdiction, chronological month, and Urgency Status filters.
3. **Generative AI Integration**: An embedded "AI Compliance Explainer" powered by Groq (LLaMA 3.3) that instantly generates plain-English summaries of complex regulatory filings, their purpose, and the risks of non-compliance.
4. **Proactive Alerting**: Surfaces overdue and near-term filing risks directly in the dashboard.
5. **Cross-Jurisdiction Tracking**: Demonstrates monitoring for both US and UK regulatory reporting workflows.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend Logic** | Python, Pandas, Datetime |
| **Frontend / UI** | Streamlit |
| **AI Integration** | Groq API (LLaMA 3.3 70B model) |
| **Deployment** | Streamlit Community Cloud, GitHub Codespaces |

---

## The Problem It Solves

Traditional compliance teams rely on static Excel trackers where a human must manually update a status from "Pending" to "Overdue." If a team member is absent, the data goes stale, increasing regulatory risk. 

This tool solves that by decoupling the human-recorded Status from the machine-calculated Urgency. Every day the application runs, it compares the `Due_Date` against the live system clock and recalculates the urgency automatically. For example, a MiFIR Transaction Report might have a human status of "Pending," but the system will correctly flag it as "Overdue" if the deadline has passed.

---

## How to Run Locally

1. Clone this repository.
2. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Groq API key as an environment variable:
   ```bash
   export GROQ_API_KEY="your-api-key"
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

---

## About

Built by **Nisrin Shoukat Attarwala**  
MSc Financial Technology & Innovation, Bayes Business School, 2026.

This project is part of a portfolio targeting roles in Fintech, RegTech, and Product Operations.  
See also: [DeFi Wallet Risk Intelligence](https://github.com/nattarw-tech/defi-wallet-risk-intelligence)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect_With_Me-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nisrin-attarwala/)
