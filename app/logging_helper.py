import os
import traceback
from datetime import datetime

def save_error(error: str = "error_logs") -> str:
    """
    Catches an exception, formats the full traceback, and saves it to a timestamped file.

    Args:
        log_dir (str): The directory where the error log will be saved.

    Returns:
        str: The path to the newly created log file.
    """
    log_dir = "log_error"
    # 1. Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # 2. Generate a unique, sortable filename using a timestamp
    # We include microseconds (%f) to avoid filename collisions
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
    filepath = os.path.join(log_dir, f"error_{timestamp}.log")

    # 3. Get the full traceback as a string
    traceback_str = str(error) + '\n'

    # 4. Write the traceback to the file
    with open(filepath, "w") as f:
        f.write(traceback_str)
    
    return filepath
