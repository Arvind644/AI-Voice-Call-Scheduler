# Voice Call Scheduler

A simple application to schedule automated voice calls using Bland AI and Streamlit.

## Features

- Schedule voice calls with custom messages
- View all scheduled calls
- Cancel scheduled calls
- Real-time call status updates
- Simple and intuitive interface
- Batch process calls from CSV files
- Support for multiple Bland AI voices
- Call execution monitoring

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and add your Bland AI API key:
```
BLAND_AI_API_KEY=your_api_key_here
```

3. Run the Streamlit application:
```bash
streamlit run app.py
```

4. In a separate terminal, run the call executor:
```bash
python call_executor.py
```

## Usage

### Web Interface

1. Open the Streamlit application in your browser (usually at http://localhost:8501)
2. Enter your Bland AI API key in the sidebar
3. Fill in the call details:
   - Phone number
   - Message to be spoken
   - Voice selection
   - Date and time for the call
4. Click "Schedule Call" to create the call
5. View and manage your scheduled calls in the list below

### Batch Processing

To schedule multiple calls at once, use the batch processor:

1. Create a CSV file with the following columns:
   - `phone_number`: The recipient's phone number (including country code)
   - `message`: The message to be spoken
   - `voice_id`: (Optional) The Bland AI voice to use (defaults to "clara")

2. Run the batch processor:
```bash
python batch_processor.py path/to/your/file.csv
```

3. To schedule calls for a specific time:
```bash
python batch_processor.py path/to/your/file.csv --time "2023-08-15 14:30:00"
```

## Available Voices

The application supports the following Bland AI voices:
- clara
- jony
- adam
- jeremy
- ryan
- karen
- neil
- christina
- matt
- jenny

## Notes

- The call executor runs in the background and checks for pending calls every 30 seconds
- Calls are stored in a SQLite database (`calls.db`)
- Make sure to keep the call executor running to execute scheduled calls
- Bland AI free tier allows up to 1,000 calls per day
- Enterprise customers can make up to 20,000 calls per hour and 100,000 calls per day 