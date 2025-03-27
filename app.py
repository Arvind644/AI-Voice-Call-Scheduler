import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pytz
from dateutil import parser
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database
def init_db():
    conn = sqlite3.connect('calls.db')
    c = conn.cursor()
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
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Function to display calls
def display_calls(calls, call_type):
    if not calls:
        st.info(f"No {call_type} calls found")
    else:
        for i, call in enumerate(calls):
            call_id, phone_number, message, voice_id, scheduled_time, status, bland_call_id, created_at = call
            
            # Format the status with color
            if status == "pending":
                status_html = f"<span style='color:orange;font-weight:bold'>{status.upper()}</span>"
            elif status == "in_progress":
                status_html = f"<span style='color:blue;font-weight:bold'>{status.upper()}</span>"
            elif status == "completed":
                status_html = f"<span style='color:green;font-weight:bold'>{status.upper()}</span>"
            else:
                status_html = f"<span style='color:red;font-weight:bold'>{status.upper()}</span>"
            
            # Use a unique key for each expander by combining call_type, call_id and index
            with st.expander(f"Call to {phone_number} - {scheduled_time} ({status})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Message:** {message}")
                    st.markdown(f"**Status:** {status_html}", unsafe_allow_html=True)
                    st.markdown(f"**Voice:** {voice_id}")
                
                with col2:
                    st.markdown(f"**Scheduled for:** {scheduled_time}")
                    st.markdown(f"**Created at:** {created_at}")
                    if bland_call_id:
                        st.markdown(f"**Bland Call ID:** {bland_call_id}")
                
                # Add buttons
                col1, col2 = st.columns(2)
                with col1:
                    if status == "pending":
                        # Create unique keys by combining call_type, call_id, and action
                        if st.button("Cancel Call", key=f"cancel_{call_type}_{call_id}_{i}"):
                            try:
                                conn = sqlite3.connect('calls.db')
                                c = conn.cursor()
                                c.execute('DELETE FROM scheduled_calls WHERE id = ?', (call_id,))
                                conn.commit()
                                conn.close()
                                st.success("Call cancelled successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error cancelling call: {str(e)}")
                
                with col2:
                    if status == "pending" and st.button("Execute Now", key=f"execute_{call_type}_{call_id}_{i}"):
                        if not api_key:
                            st.error("Please enter your Bland AI API Key in the sidebar")
                        else:
                            try:
                                # Execute the call now using Bland AI API
                                headers = {
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json"
                                }
                                
                                payload = {
                                    "phone_number": phone_number,
                                    "task": message,
                                    "voice_id": voice_id,
                                    "reduce_latency": True,
                                    "wait_for_greeting": True
                                }
                                
                                response = requests.post(
                                    "https://api.bland.ai/v1/calls",
                                    headers=headers,
                                    data=json.dumps(payload)
                                )
                                
                                if response.status_code == 200:
                                    call_data = response.json()
                                    # Update call status
                                    conn = sqlite3.connect('calls.db')
                                    c = conn.cursor()
                                    c.execute('''
                                        UPDATE scheduled_calls 
                                        SET status = 'in_progress', bland_call_id = ? 
                                        WHERE id = ?
                                    ''', (call_data.get('id', ''), call_id))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"Call executed successfully! Bland Call ID: {call_data.get('id', 'unknown')}")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"API Error: {response.status_code} - {response.text}")
                            except Exception as e:
                                st.error(f"Error executing call: {str(e)}")

# Page config
st.set_page_config(
    page_title="Voice Call Scheduler",
    page_icon="📞",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stExpander {
        border: 1px solid #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("📞 Voice Call Scheduler")
st.markdown("Schedule automated voice calls using Bland AI")

# Sidebar for API key and stats
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Bland AI API Key", type="password", value=os.getenv("BLAND_AI_API_KEY", ""))
    if not api_key:
        st.warning("Please enter your Bland AI API key to schedule calls")
    else:
        # Save API key to .env file
        with open(".env", "w") as f:
            f.write(f"BLAND_AI_API_KEY={api_key}")
    
    st.markdown("---")
    st.subheader("Call Stats")
    
    # Get call stats
    try:
        conn = sqlite3.connect('calls.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM scheduled_calls")
        total_calls = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM scheduled_calls WHERE status = 'pending'")
        pending_calls = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM scheduled_calls WHERE status = 'in_progress'")
        in_progress_calls = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM scheduled_calls WHERE status = 'completed'")
        completed_calls = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM scheduled_calls WHERE status = 'failed'")
        failed_calls = c.fetchone()[0]
        
        conn.close()
        
        st.metric("Total Calls", total_calls)
        st.metric("Pending Calls", pending_calls)
        st.metric("In Progress", in_progress_calls)
        st.metric("Completed", completed_calls)
        st.metric("Failed", failed_calls)
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Bland AI Rate Limits")
    st.markdown("- Free tier: 1,000 calls/day")
    st.markdown("- Enterprise: 20,000 calls/hour")
    st.markdown("- Enterprise: 100,000 calls/day")

# Main form for scheduling calls
st.header("Schedule a Call")

with st.form("schedule_call_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        phone_number = st.text_input("Phone Number", placeholder="+1234567890")
        message = st.text_area("Message", placeholder="Enter the message to be spoken")
    
    with col2:
        scheduled_date = st.date_input("Date", min_value=datetime.now().date())
        scheduled_time = st.time_input("Time")
        voice_options = [
            "clara", "jony", "adam", "jeremy", "ryan", 
            "karen", "neil", "christina", "matt", "jenny"
        ]
        voice_id = st.selectbox("Voice", options=voice_options, index=0)
    
    # Combine date and time
    scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
    
    submitted = st.form_submit_button("Schedule Call")
    
    if submitted:
        if not api_key:
            st.error("Please enter your Bland AI API Key in the sidebar")
        elif not phone_number or not message:
            st.error("Please fill in all fields")
        else:
            try:
                conn = sqlite3.connect('calls.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO scheduled_calls (phone_number, message, voice_id, scheduled_time)
                    VALUES (?, ?, ?, ?)
                ''', (phone_number, message, voice_id, scheduled_datetime))
                conn.commit()
                conn.close()
                st.success("Call scheduled successfully!")
            except Exception as e:
                st.error(f"Error scheduling call: {str(e)}")

# Display scheduled calls
st.header("Scheduled Calls")

# Tabs for different call statuses
tab1, tab2, tab3, tab4 = st.tabs(["All Calls", "Pending", "In Progress", "Completed/Failed"])

try:
    conn = sqlite3.connect('calls.db')
    c = conn.cursor()
    
    # All calls
    with tab1:
        c.execute('SELECT * FROM scheduled_calls ORDER BY scheduled_time DESC')
        calls = c.fetchall()
        display_calls(calls, "all")
    
    # Pending calls
    with tab2:
        c.execute('SELECT * FROM scheduled_calls WHERE status = "pending" ORDER BY scheduled_time')
        calls = c.fetchall()
        display_calls(calls, "pending")
    
    # In progress calls
    with tab3:
        c.execute('SELECT * FROM scheduled_calls WHERE status = "in_progress" ORDER BY scheduled_time DESC')
        calls = c.fetchall()
        display_calls(calls, "in_progress")
    
    # Completed/Failed calls
    with tab4:
        c.execute('SELECT * FROM scheduled_calls WHERE status IN ("completed", "failed") ORDER BY scheduled_time DESC')
        calls = c.fetchall()
        display_calls(calls, "completed")
    
    conn.close()
except Exception as e:
    st.error(f"Error fetching scheduled calls: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Bland AI and Streamlit") 