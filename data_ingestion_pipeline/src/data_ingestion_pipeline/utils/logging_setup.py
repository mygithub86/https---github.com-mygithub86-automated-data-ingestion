import logging
import os

def setup_logging(config):
    """Configures logging based on the loaded configuration."""
    log_config = config.get('logging', {})
    level_name = log_config.get('level', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = log_config.get('file')
    log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(name)s - %(message)s') # Include logger name

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level) # Set root logger level

    # Remove existing handlers to avoid duplication if called multiple times
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create file handler if specified
    if log_file:
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logging.info(f"Logging to console and file: {log_file}")
        except Exception as e:
            logging.error(f"Failed to configure file logging to {log_file}: {e}", exc_info=True)
            logging.info("Logging to console only.")
    else:
        logging.info("Logging to console only.")

    # Example: Set specific levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    # Add others as needed

    logging.info(f"Logging configured at level {level_name}.") 