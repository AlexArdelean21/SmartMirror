import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timezone
from util.logger import logger

load_dotenv()


def get_calendar_service():
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not credentials_path:
        logger.error("GOOGLE_CREDENTIALS_PATH not set in .env")
        raise ValueError("Google credentials path not set.")

    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found at: {credentials_path}")
        raise ValueError("Credentials file not found.")

    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        logger.info("Google Calendar service authenticated successfully.")
        return build("calendar", "v3", credentials=credentials)
    except Exception as e:
        logger.exception(f"Failed to authenticate with Google Calendar: {e}")
        raise


def get_upcoming_events(max_results=5):
    try:
        service = get_calendar_service()
        time_min = datetime.now(timezone.utc).isoformat()
        logger.info(f"Fetching upcoming {max_results} events from calendar...")

        events_result = service.events().list(
            calendarId='ardelean.alex2003@gmail.com',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            logger.info("No upcoming events found.")
            return {"message": "No upcoming events"}

        logger.info(f"Fetched {len(events)} event(s) from Google Calendar.")
        return events

    except Exception as e:
        logger.exception(f"Error while fetching upcoming calendar events: {e}")
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

        logger.info(f"Adding new event: {event}")
        created_event = service.events().insert(
            calendarId='ardelean.alex2003@gmail.com',
            body=event
        ).execute()

        logger.info(f"Event created successfully: {created_event.get('id')}")
        return {"status": "success", "event": created_event}

    except Exception as e:
        logger.exception(f"Error adding event to calendar: {e}")
        return {"status": "error", "message": str(e)}
