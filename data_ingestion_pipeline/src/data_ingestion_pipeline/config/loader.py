import yaml
import os
import logging
from dotenv import load_dotenv

_config = None # Module-level variable to hold the loaded config

def load_configuration(config_path='config.yaml'):
    """Loads configuration from YAML file and environment variables."""
    global _config
    if _config:
        logging.warning("Configuration already loaded. Returning existing config.")
        return _config

    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        if not isinstance(config_data, dict): # Basic validation
             raise yaml.YAMLError("Config file does not contain a valid YAML dictionary.")
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        raise # Re-raise the exception to halt execution if config is critical
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        raise # Re-raise

    # Load environment variables from .env file (if exists)
    load_dotenv()

    # Securely load sensitive keys specified in config, preferring env vars
    oauth_conf = config_data.setdefault('oauth', {})
    oauth_conf['client_id'] = os.getenv(oauth_conf.get('client_id_key', 'OAUTH_CLIENT_ID'))
    oauth_conf['client_secret'] = os.getenv(oauth_conf.get('client_secret_key', 'OAUTH_CLIENT_SECRET'))

    openai_conf = config_data.setdefault('openai', {})
    openai_conf['api_key'] = os.getenv(openai_conf.get('api_key_env_var', 'OPENAI_API_KEY'))

    vector_db_conf = config_data.setdefault('vector_database', {})
    vector_db_conf['api_key'] = os.getenv(vector_db_conf.get('api_key_env_var', 'VECTOR_DB_API_KEY'))

    # Add similar loading logic for other potential secrets (e.g., ServiceNow creds)

    # Remove potentially sensitive *_key / *_env_var fields after loading
    oauth_conf.pop('client_id_key', None)
    oauth_conf.pop('client_secret_key', None)
    openai_conf.pop('api_key_env_var', None)
    vector_db_conf.pop('api_key_env_var', None)

    _config = config_data # Store loaded config
    logging.info(f"Configuration loaded successfully from {config_path} and environment.")
    return _config

def get_config():
    """Returns the loaded configuration dictionary."""
    if _config is None:
        # This case should ideally not happen if load_configuration is called first
        logging.error("Configuration accessed before loading.")
        raise RuntimeError("Configuration not loaded. Call load_configuration first.")
    return _config 