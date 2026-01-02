import logging
import os
from datetime import datetime

# DEBUG, INFO, WARNING, ERROR, CRITICAL
# Use DEBUG to understand how the code is working.
# Use INFO for normal, successful operations.
# Use WARNING when something is unexpected, but the system can still continue.
# Use ERROR when an operation fails, but the application does not crash completely.
# Use CRITICAL when the entire system or service is at risk.
# ================================================================
# LOGGER UTILITY
# ================================================================

def get_logger(logger_name: str,
               log_dir: str = "logs",
               level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger instance.

    Parameters
    ----------
    logger_name : str
        Name of the logger.
    log_dir : str
        Directory to store log files.
    level : int
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns
    -------
    logging.Logger
    """

    # ----------------------------------------------------------------
    # Prevent duplicate loggers if already created
    # ----------------------------------------------------------------
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger  # logger already configured

    # ----------------------------------------------------------------
    # Ensure directory exists
    # ----------------------------------------------------------------
    os.makedirs(log_dir, exist_ok=True)

    # ----------------------------------------------------------------
    # Create timestamped log file
    # ----------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log_file_path = os.path.join(log_dir, f"{logger_name}_{timestamp}.log")

    # ----------------------------------------------------------------
    # Set logger level
    # ----------------------------------------------------------------
    logger.setLevel(level)
    logger.propagate = False

    # ----------------------------------------------------------------
    # Formatter
    # ----------------------------------------------------------------
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ----------------------------------------------------------------
    # FILE HANDLER
    # ----------------------------------------------------------------
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # ----------------------------------------------------------------
    # STREAM HANDLER (console)
    # ----------------------------------------------------------------
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    # ----------------------------------------------------------------
    # Add handlers to logger
    # ----------------------------------------------------------------
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# ================================================================
# LOGGER EXAMPLE
# ================================================================
# logger = get_logger(__name__)
# logger.info("Hello, world!")
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")
