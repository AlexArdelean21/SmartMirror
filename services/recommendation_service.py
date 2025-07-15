import datetime
import os
import openai
from services.weather_service import get_weather
from services.calendar_service import get_upcoming_events

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_personal_recommendation(user_profile: dict) -> str: # Generates a personal recommendation for the user based on weather, calendar events, and time of day.
    try:
        now = datetime.datetime.now()
        hour = now.hour
        
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        location = user_profile.get('preferences', {}).get('location', 'Bucharest')
        weather_data = get_weather(location)
        weather_description = f"{weather_data['weather'][0]['description']} and {weather_data['main']['temp']}°C" if weather_data else "not available"

        event_summary = ""
        # Only fetch calendar events for Alex
        if user_profile.get("name", "").lower() == "alex":
            events = get_upcoming_events()
            if events and 'error' not in events:
                if isinstance(events, list) and len(events) > 0:
                    event = events[0]
                    # Check for 'dateTime' key before accessing it
                    if 'dateTime' in event['start']:
                        event_time = datetime.datetime.fromisoformat(event['start']['dateTime']).strftime('%H:%M')
                        event_summary = f"The user has an event: '{event['summary']}' at {event_time}."
                    else:
                        event_summary = f"The user has an all-day event: '{event['summary']}'."


        prompt = f"Give a short, creative recommendation for a user in {location}. Weather is {weather_description}. It is {time_of_day}. {event_summary} Suggest something helpful and brief."

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing concise, creative recommendations, don't add any simbold like this one * ."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return "I couldn't come up with a recommendation right now." 