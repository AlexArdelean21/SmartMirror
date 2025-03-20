import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging

load_dotenv()  # Load environment variables

def get_calendar_service():
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not credentials_path:
        raise ValueError("Google credentials path not set.")

    if not credentials_path:
        raise ValueError("GOOGLE_CALENDAR_CREDENTIALS not found in .env")

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)

def get_upcoming_events(max_results=5):
    try:
        service = get_calendar_service()
        time_min = datetime.now(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId='ardelean.alex2003@gmail.com',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return {"message": "No upcoming events"}

        return events

    except Exception as e:
        logging.error(f"Calendar API error: {e}")
        return {"error": "Google Calendar API request failed"}, 500


def add_event(summary, start_time, end_time, description=None):
    try:
        service = get_calendar_service()

        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'Europe/Bucharest'},
            'end': {'dateTime': end_time, 'timeZone': 'Europe/Bucharest'},
            'description': description
        }

        logging.info(f"Attempting to add event: {event}")
        created_event = service.events().insert(
            calendarId='ardelean.alex2003@gmail.com',  # Use your calendar ID
            body=event
        ).execute()
        logging.info(f"Event added successfully: {created_event}")
        return {"status": "success", "event": created_event}
    except Exception as e:
        logging.error(f"Error adding event to calendar: {e}")
        return {"status": "error", "message": str(e)}
