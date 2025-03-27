import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys
import argparse

def process_batch_file(file_path, scheduled_time=None):
    """
    Process a CSV file with phone numbers and messages to schedule calls
    
    CSV format:
    phone_number,message,voice_id
    +1234567890,Hello this is a test call,clara
    +1987654321,Another test message,adam
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_columns = ['phone_number', 'message']
        for col in required_columns:
            if col not in df.columns:
                print(f"Error: Required column '{col}' not found in CSV file")
                return False
        
        # Add voice_id column if not present
        if 'voice_id' not in df.columns:
            df['voice_id'] = 'clara'  # Default voice
        
        # Connect to database
        conn = sqlite3.connect('calls.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_calls
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             phone_number TEXT NOT NULL,
             message TEXT NOT NULL,
             voice_id TEXT DEFAULT 'clara',
             scheduled_time DATETIME NOT NULL,
             status TEXT DEFAULT 'pending',
             bland_call_id TEXT,
             created_at DATETIME DEFAULT CURRENT_TIMESTAMP)
        ''')
        
        # If scheduled time is not provided, use current time + 5 minutes
        if scheduled_time is None:
            scheduled_time = datetime.now().replace(microsecond=0)
        
        # Insert records
        total_records = len(df)
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                c.execute('''
                    INSERT INTO scheduled_calls (phone_number, message, voice_id, scheduled_time)
                    VALUES (?, ?, ?, ?)
                ''', (row['phone_number'], row['message'], row['voice_id'], scheduled_time))
                success_count += 1
            except Exception as e:
                print(f"Error inserting record for {row['phone_number']}: {str(e)}")
                error_count += 1
        
        # Commit and close
        conn.commit()
        conn.close()
        
        print(f"Batch processing complete!")
        print(f"Total records: {total_records}")
        print(f"Successfully scheduled: {success_count}")
        print(f"Failed to schedule: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"Error processing batch file: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a batch file of calls to schedule')
    parser.add_argument('file_path', help='Path to CSV file with phone numbers and messages')
    parser.add_argument('--time', help='Scheduled time (format: YYYY-MM-DD HH:MM:SS)')
    
    args = parser.parse_args()
    
    scheduled_time = None
    if args.time:
        try:
            scheduled_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("Error: Invalid time format. Use YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    success = process_batch_file(args.file_path, scheduled_time)
    if not success:
        sys.exit(1) 