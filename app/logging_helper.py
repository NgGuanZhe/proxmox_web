import os
import traceback
from datetime import datetime

def save_error(e: Exception) -> str:
    """
    Catches an exception, formats the full traceback, saves it to a timestamped file,
    and returns the traceback as a string.

    Args:
        e (Exception): The exception object caught.

    Returns:
        str: The full traceback string.
    """
    log_dir = "log_error"
    # 1. Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # 2. Generate a unique, sortable filename using a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
    filepath = os.path.join(log_dir, f"error_{timestamp}.log")

    # 3. Get the full traceback as a string
    traceback_str = traceback.format_exc()

    # 4. Write the traceback to the file
    with open(filepath, "w") as f:
        f.write(f"Error: {str(e)}\n\n")
        f.write(traceback_str)
    
    # 5. Return the traceback string to be logged
    return f"Error saved to {filepath}. Traceback: {traceback_str}"
