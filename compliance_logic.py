import pandas as pd
from datetime import datetime

def process_filings(csv_file_path):
    df = pd.read_csv(csv_file_path)
    df['Due_Date'] = pd.to_datetime(df['Due_Date'])
    today = pd.to_datetime(datetime.now().date())
    df['Days_Remaining'] = (df['Due_Date'] - today).dt.days
    
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
    df['Due_Date'] = df['Due_Date'].dt.strftime('%Y-%m-%d')
    return df

if __name__ == "__main__":
    print("Testing the compliance logic...")
    processed_data = process_filings('filing_schedule.csv')
    print("\nProcessed Data Overview:")
    print(processed_data[['Filing_Name', 'Days_Remaining', 'Urgency']])
