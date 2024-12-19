import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()  # Load environment variables

def get_calendar_service():
    credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    if not credentials_path:
        raise ValueError("GOOGLE_CALENDAR_CREDENTIALS not found in .env")

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    return build("calendar", "v3", credentials=credentials)

def get_upcoming_events(max_results=5):
    try:
        service = get_calendar_service()
        time_min = datetime.now(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return {"error": "Failed to fetch events"}


