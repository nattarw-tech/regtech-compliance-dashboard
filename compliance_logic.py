"""
compliance_logic.py
-------------------
Backend processing module for the RegTrack Regulatory Compliance Dashboard.

Loads the filing schedule CSV, calculates real-time Days_Remaining from the
current system date, and assigns a machine-calculated Urgency status that is
independent of the human-recorded Status field — eliminating stale data risk.
"""

import pandas as pd
from datetime import date


def process_filings(filepath: str) -> pd.DataFrame:
    """
    Load the filing schedule CSV and enrich it with computed fields.

    Parameters
    ----------
    filepath : str
        Path to the filing schedule CSV file.

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame with Days_Remaining and Urgency columns added.
    """
    df = pd.read_csv(filepath)

    # Parse Due_Date — accepts both YYYY-MM-DD and M/D/YYYY formats
    df['Due_Date'] = pd.to_datetime(df['Due_Date'], dayfirst=False)

    # Calculate days remaining from today (negative = overdue)
    today = pd.Timestamp(date.today())
    df['Days_Remaining'] = (df['Due_Date'] - today).dt.days

    # Machine-calculated Urgency — overrides human Status for display purposes
    def assign_urgency(row):
        if row['Status'].strip().lower() in ('submitted', 'completed'):
            return 'Completed'
        if row['Days_Remaining'] < 0:
            return 'Overdue'
        if row['Days_Remaining'] <= 30:
            return 'Due Soon'
        return 'On Track'

    df['Urgency'] = df.apply(assign_urgency, axis=1)

    # Format Due_Date back to a clean string for display
    df['Due_Date'] = df['Due_Date'].dt.strftime('%Y-%m-%d')

    return df
