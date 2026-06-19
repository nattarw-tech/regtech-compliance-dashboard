"""
compliance_logic.py
-------------------
Backend processing module for the RegTrack Regulatory Compliance Dashboard.

The CSV stores Days_From_Today as a relative integer offset (e.g. 45 means
due in 45 days, -1 means 1 day overdue). This module calculates the actual
Due_Date dynamically from today's system date on every run, so the dashboard
is always evergreen — a recruiter opening it in six months will still see
realistic, current-looking data rather than a wall of overdue filings.

The machine-calculated Urgency is kept separate from the human-recorded
Status field, which eliminates stale data risk.
"""

import pandas as pd
from datetime import datetime, timedelta


def process_filings(csv_file_path: str) -> pd.DataFrame:
    """
    Load the filing schedule CSV and enrich it with computed fields.

    Parameters
    ----------
    csv_file_path : str
        Path to the filing schedule CSV file.

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame with Due_Date, Days_Remaining, and Urgency added.
    """
    df = pd.read_csv(csv_file_path)

    # Calculate the exact due date dynamically based on today's date
    today = datetime.now().date()
    df['Due_Date'] = df['Days_From_Today'].apply(
        lambda x: today + timedelta(days=int(x))
    )

    # Convert Due_Date to a clean string for display
    df['Due_Date'] = pd.to_datetime(df['Due_Date']).dt.strftime('%Y-%m-%d')

    # Days_Remaining is the same as Days_From_Today — kept as a named alias
    # so the rest of the app can reference it without knowing the CSV column name
    df['Days_Remaining'] = df['Days_From_Today']

    def determine_urgency(row):
        if row['Status'].strip() == 'Submitted':
            return 'Completed'
        elif row['Days_Remaining'] < 0:
            return 'Overdue'
        elif row['Days_Remaining'] <= 30:
            return 'Due Soon'
        else:
            return 'On Track'

    df['Urgency'] = df.apply(determine_urgency, axis=1)

    return df
