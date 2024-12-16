from datetime import datetime

def get_time_date():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    return {"time": current_time, "date": current_date}
