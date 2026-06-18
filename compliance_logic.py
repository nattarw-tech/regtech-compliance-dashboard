import pandas as pd
from datetime import datetime, timedelta

def process_filings(csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    # Calculate the exact due date dynamically based on today's date
    today = datetime.now().date()
    df['Due_Date'] = df['Days_From_Today'].apply(lambda x: today + timedelta(days=x))
    
    # Convert Due_Date to string for Streamlit display
    df['Due_Date'] = pd.to_datetime(df['Due_Date']).dt.strftime('%Y-%m-%d')
    
    # We still need Days_Remaining for the urgency logic, which is just Days_From_Today
    df['Days_Remaining'] = df['Days_From_Today']
    
    def determine_urgency(row):
        if row['Status'] == 'Submitted':
            return 'Completed'
        elif row['Days_Remaining'] < 0:
            return 'Overdue'
        elif row['Days_Remaining'] <= 30:
            return 'Due Soon'
        else:
            return 'On Track'
            
    df['Urgency'] = df.apply(determine_urgency, axis=1)
    
    return df
