import logging
import sys

# Custom formatter with colors for console
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return result

# Configure logging format
SIMPLE_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'

# Create formatter
console_formatter = ColoredFormatter(
    fmt=SIMPLE_FORMAT,
    datefmt='%H:%M:%S'
)

# Create console handler (only terminal output)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Configure root logger - ONLY console, no files
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)

# Create app logger
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

# Reduce noise from other libraries
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# Log startup message
logger.info("=" * 60)
logger.info("🚀 Analytics Dashboard Backend Started - Live Logs Only")
logger.info("📺 Watching terminal for live API calls and errors...")
logger.info("=" * 60)
