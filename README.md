# Meeting Assistant

This Flask application provides real-time transcription of speech and GPT-based suggestions during meetings. All transcripts and responses are stored locally using SQLAlchemy with SQLite by default. The front-end displays a built-in sheet that updates live as the conversation progresses.

## Running the App
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Set required environment variables (see `.env.example` if provided).
3. Start the server
   ```bash
   python run.py
   ```
4. Open `http://localhost:5000` in your browser.

**Note**: The old Streamlit version has been removed. Running `python app.py`
will simply start the Flask server described above.

## Features
- Real-time speech transcription and AI suggestions
- History view of past meetings
- Manage answer styles used for GPT responses

The previous Google Sheets integration has been removed; all data is kept within the app.
