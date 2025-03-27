import sqlite3
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def execute_pending_calls():
    api_key = os.getenv("BLAND_AI_API_KEY")
    if not api_key:
        print("Error: BLAND_AI_API_KEY not found in environment variables")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    while True:
        try:
            conn = sqlite3.connect('calls.db')
            c = conn.cursor()
            
            # Get pending calls that are due
            current_time = datetime.now()
            c.execute('''
                SELECT id, phone_number, message 
                FROM scheduled_calls 
                WHERE status = 'pending' 
                AND scheduled_time <= ?
            ''', (current_time,))
            
            pending_calls = c.fetchall()
            print(f"Found {len(pending_calls)} pending call(s) to execute")
            
            for call in pending_calls:
                call_id, phone_number, message = call
                try:
                    # Make the call using Bland AI REST API
                    payload = {
                        "phone_number": phone_number,
                        "task": message,
                        "voice_id": "clara",  # You can change this to any voice_id from Bland AI
                        "reduce_latency": True,
                        "wait_for_greeting": True
                    }
                    
                    response = requests.post(
                        "https://api.bland.ai/v1/calls",
                        headers=headers,
                        data=json.dumps(payload)
                    )
                    
                    if response.status_code == 200:
                        # Update call status
                        call_data = response.json()
                        c.execute('''
                            UPDATE scheduled_calls 
                            SET status = 'in_progress' 
                            WHERE id = ?
                        ''', (call_id,))
                        print(f"Call executed successfully to {phone_number} - Call ID: {call_data.get('id', 'unknown')}")
                    else:
                        print(f"API Error: {response.status_code} - {response.text}")
                        c.execute('''
                            UPDATE scheduled_calls 
                            SET status = 'failed' 
                            WHERE id = ?
                        ''', (call_id,))
                        
                except Exception as e:
                    print(f"Error executing call to {phone_number}: {str(e)}")
                    # Update call status to failed
                    c.execute('''
                        UPDATE scheduled_calls 
                        SET status = 'failed' 
                        WHERE id = ?
                    ''', (call_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
        
        # Wait for 30 seconds before checking again
        print("Waiting 30 seconds before checking for more calls...")
        time.sleep(30)

if __name__ == "__main__":
    print("Starting Call Executor - Press Ctrl+C to stop")
    execute_pending_calls() 