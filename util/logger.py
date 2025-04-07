import logging
import os
import sys
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

# Color formatter for console logs
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[90m",     # Gray
        "INFO": "\033[97m",      # White
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "CRITICAL": "\033[91m",  # Red
    }
    RESPONSE_COLOR = "\033[94m"  # Blue for TTS responses
    RESET = "\033[0m"

    def format(self, record):
        base = super().format(record)
        if record.levelname == "INFO" and "TTS starting for response:" in record.getMessage():
            return f"{self.RESPONSE_COLOR}{base}{self.RESET}"
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{base}{self.RESET}"

# Base formatter for file handlers
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger("SmartMirror")
logger.setLevel(logging.DEBUG)

# Rotating file handler for all logs
file_handler = RotatingFileHandler(
    "logs/smart_mirror.log",
    maxBytes=1_000_000,   # 1MB per file
    backupCount=5,        # Keep 5 old logs
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Rotating file handler for errors
error_handler = RotatingFileHandler(
    "logs/error.log",
    maxBytes=500_000,     # 500KB per file
    backupCount=3,        # Keep 3 old error logs
    encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)

class NoTracebackFilter(logging.Filter):
    def filter(self, record):
        record.exc_info = None
        return True

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows emoji/log compatibility
except AttributeError:
    pass

color_console_handler = logging.StreamHandler(sys.stdout)
color_console_handler.setLevel(logging.INFO)
color_console_handler.setFormatter(ColorFormatter("%(asctime)s - %(levelname)s - %(message)s"))
color_console_handler.addFilter(NoTracebackFilter())

# Add handlers if not already attached
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(color_console_handler)
