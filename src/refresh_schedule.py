from datetime import datetime, timedelta
import random
import time

def calculate_refresh_interval():
    #return random.randint(1800, 10800)  # Between 30 mins to 3 hours
    #return random.randint(30, 300) # between 30s and 5 mins
    #return random.randint(1800, 64800) # Between 30 mins and 24 hours (actually mistake - it was 18 hours I think)
    return random.randint(21600, 172800) # Between 6 hours and 48 hours

def calculate_next_refresh(current_time, refresh_interval):
    return current_time + timedelta(seconds=refresh_interval)

def sleep_until_next_refresh(next_refresh, shutdown_event=None):
    time_remaining = next_refresh - datetime.now()
    if time_remaining.total_seconds() > 0:
        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60
        seconds = time_remaining.seconds % 60
        print(f"Time until next refresh: {days}d {hours}h {minutes}m {seconds}s", flush=True)
        terminated = sleep_until_shutdown(time_remaining.total_seconds(), shutdown_event)
        return terminated
    else: 
        return False

def read_refresh_from_file(file_path):
    """
    Reads the next refresh Unix timestamp from a file.
    Returns the timestamp as a float, or None if the file is missing/empty.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if content:
                timestamp = float(content)
                return datetime.fromtimestamp(timestamp)
    except (FileNotFoundError, IOError, ValueError):
        # If file doesn't exist or can't be parsed, return None
        # This allows the caller to set an initial or default timestamp
        pass
    
    return None

from threading import Event

def sleep_until_shutdown(duration_seconds, shutdown_event=None):
    """
    Interruptible sleep that breaks down longer sleeps into 1-second chunks.
    Checks shutdown_event periodically and returns True if terminated early.
    
    Args:
        duration_seconds: Total sleep duration in seconds (can be any duration)
        shutdown_event: threading.Event to check for shutdown signal
        
    Returns:
        True if terminated early due to shutdown, False if completed normally
    """
    if duration_seconds <= 0:
        return False
    
    if shutdown_event is None:
        shutdown_event = Event()
    
    remaining = int(duration_seconds)
    
    while remaining > 0 and not shutdown_event.is_set():
        sleep_time = min(remaining, 1)
        time.sleep(sleep_time)
        remaining -= 1
    
    return not shutdown_event.is_set() and remaining > 0

def write_refresh_to_file(next_refresh, file_path):
    """
    Writes the next refresh Unix timestamp (as an int) to a file.
    Overwrites any existing content in the file.
    """
    try:
        # Ensure the timestamp is an integer before writing
        timestamp = next_refresh.timestamp()
        with open(file_path, 'w') as f:
            f.write(str(timestamp))
    except (ValueError, IOError):
        # Log the error or handle appropriately
        # print(f"Error writing refresh time to {file_path}: {next_refresh}")
        pass