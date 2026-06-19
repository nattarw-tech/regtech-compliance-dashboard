import pandas as pd
from datetime import datetime, timedelta
import os

def process_filings(csv_file_path: str) -> pd.DataFrame:
    # Resolve the CSV path relative to this file's directory so it works
    # both locally and on Streamlit Cloud regardless of working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, csv_file_path)

    df = pd.read_csv(full_path)

    # Calculate the exact due date dynamically based on today's date
    today = datetime.now().date()
    df['Due_Date'] = df['Days_From_Today'].apply(
        lambda x: today + timedelta(days=int(x))
    )

    # Convert Due_Date to a clean string for Streamlit display
    df['Due_Date'] = pd.to_datetime(df['Due_Date']).dt.strftime('%Y-%m-%d')

    # Days_Remaining is the same as Days_From_Today — kept as a named alias
    # so the rest of the app can reference it without knowing the CSV column name
    df['Days_Remaining'] = df['Days_From_Today']

    def determine_urgency(row):
        # We must use the original CSV column 'Days_From_Today' here 
        # because 'Days_Remaining' might not be reliably available inside apply() 
        # depending on the Pandas version or environment (e.g. Streamlit Cloud).
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
