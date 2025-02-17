import logging
from logging.handlers import RotatingFileHandler


# Create a logger with a specific name, you can use the root logger by omitting the name
logger = logging.getLogger('central-vault-configurations-logger')

# Set the logging level (you can change this to ERROR, WARNING, etc.)
logger.setLevel("DEBUG")

# Create handlers
console_handler = logging.StreamHandler()  # Logs to console
file_handler = logging.FileHandler('central-vault-configurations.log')  # Logs to file

# Set different logging levels for each handler if needed
console_handler.setLevel("DEBUG")  # Logs only warnings and above to console
file_handler.setLevel("WARNING")  # Logs everything to the file

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Create a rotating file handler
rotating_file_handler = RotatingFileHandler('central-vault-configurations.log', maxBytes=5*1024*1024, backupCount=30)
rotating_file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(rotating_file_handler)
