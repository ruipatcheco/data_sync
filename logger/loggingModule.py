import logging
import os


# Usage examples:
# logger.info("This is an info message.")
# logger.error("This is an error message.")


# Create a custom logger class to encapsulate the logging configuration
class CustomLogger:
    def __init__(self, logger_name, log_file_name="log_file.log", logging_level="DEBUG"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging_level)

        # Create a file handler
        file_handler = logging.FileHandler(log_file_name)
        self._configure_handler(file_handler)

        # Create a console handler
        console_handler = logging.StreamHandler()
        self._configure_handler(console_handler)

    def _configure_handler(self, handler):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_info(self, message):
        self.logger.info(message)

    def log_error(self, message):
        self.logger.error(message)


# Define a global logger instance
log_level = os.getenv("LOGGING_LEVEL", "DEBUG")
log_file_name = os.getenv("LOG_FILE", "log_file.log")

# Create a logger instance with custom settings
logger = CustomLogger(__name__, log_file_name, log_level)

