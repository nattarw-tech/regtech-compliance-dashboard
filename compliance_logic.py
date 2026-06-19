import pandas as pd
from datetime import datetime, timedelta
import os

def process_filings(csv_file_path: str) -> pd.DataFrame:
    # Resolve the CSV path relative to this file's directory so it works
    # both locally and on Streamlit Cloud regardless of working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, csv_file_path)

    df = pd.read_csv(full_path, sep=None, engine='python')

    # ─────────────────────────────────────────────────────────────────────────
    # ORIGINAL STATIC DATE LOGIC (preserved for reference — do not delete)
    # In the original version, Due_Date was a fixed string column already
    # present in the CSV (e.g. "9/1/2026"), and Days_From_Today was a
    # pre-calculated integer that did NOT update relative to today's date.
    # The urgency thresholds were therefore evaluated against those static
    # values, meaning the dashboard would gradually go stale over time as
    # real calendar dates passed.
    #
    # Example of the original approach:
    #
    #   df['Due_Date'] = df['Due_Date']          # already in CSV as a string
    #   df['Days_Remaining'] = df['Days_From_Today']  # static integer from CSV
    #
    #   def determine_urgency(row):
    #       if row['Status'].strip() == 'Submitted':
    #           return 'Completed'
    #       elif row['Days_Remaining'] < 0:
    #           return 'Overdue'
    #       elif row['Days_Remaining'] <= 30:
    #           return 'Due Soon'
    #       else:
    #           return 'On Track'
    #
    #   df['Urgency'] = df.apply(determine_urgency, axis=1)
    # ─────────────────────────────────────────────────────────────────────────

    # CURRENT LOGIC: Due_Date is recalculated dynamically from today's date
    # using Days_From_Today, so urgency is always accurate regardless of when
    # the app is loaded. The CSV's Due_Date column (if present) is ignored and
    # overwritten with the freshly computed value.
    today = datetime.now().date()
    df['Due_Date'] = df['Days_From_Today'].apply(
        lambda x: today + timedelta(days=int(x))
    )

    # Convert Due_Date to a clean string for Streamlit display
    df['Due_Date'] = pd.to_datetime(df['Due_Date']).dt.strftime('%Y-%m-%d')

    # Days_Remaining is an alias for Days_From_Today, kept so the rest of the
    # app can reference a semantically clear column name
    df['Days_Remaining'] = df['Days_From_Today']

    def determine_urgency(row):
        # Reference 'Days_From_Today' directly (the original CSV column) rather
        # than 'Days_Remaining' to avoid a KeyError on certain Pandas/Python
        # versions where the newly added alias column may not be available
        # inside the row object during df.apply(axis=1)
        if row['Status'].strip() == 'Submitted':
            return 'Completed'
        elif row['Days_From_Today'] < 0:
            return 'Overdue'
        elif row['Days_From_Today'] <= 30:
            return 'Due Soon'
        else:
            return 'On Track'

    df['Urgency'] = df.apply(determine_urgency, axis=1)

    return df
