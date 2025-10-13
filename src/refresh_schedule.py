from datetime import datetime, timedelta
import random
import time

def calculate_refresh_interval():
    #return random.randint(1800, 10800)  # Between 30 mins to 3 hours
    #return random.randint(30, 300) # between 30s and 5 mins
    return random.randint(1800, 64800) # Between 30 mins and 24 hours

def calculate_next_refresh(current_time, refresh_interval):
    return current_time + timedelta(seconds=refresh_interval)

def sleep_until_next_refresh(next_refresh):
    time_remaining = next_refresh - datetime.now()
    if time_remaining.total_seconds() > 0:
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60
        seconds = time_remaining.seconds % 60
        print(f"Time until next refresh: {hours}h {minutes}m {seconds}s")
        time.sleep(time_remaining.total_seconds())