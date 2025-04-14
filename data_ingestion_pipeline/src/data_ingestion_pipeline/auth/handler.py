import requests
import logging
import functools
from datetime import datetime, timedelta
import json
from ..config.loader import get_config # Use centralized config access

# Simple in-memory cache for tokens (module-level)
_token_cache = {}

def get_oauth_token(client_id, client_secret, token_url):
    """
    Retrieves an OAuth2 bearer token using client credentials grant.
    Implements FR1.1.
    """
    cache_key = f"{token_url}_{client_id}"
    cached_token = _token_cache.get(cache_key)

    # Check cache validity (FR1.2, FR1.3)
    now = datetime.now()
    if cached_token and cached_token['expires_at'] > now:
        logging.debug(f"Using cached token for {token_url}")
        return cached_token['access_token']

    logging.info(f"Requesting new token from {token_url}")
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        token_data = response.json()

        if 'access_token' not in token_data or 'expires_in' not in token_data:
            logging.error(f"Invalid token response received from {token_url}: {token_data}")
            return None

        access_token = token_data['access_token']
        # Ensure expires_in is treated as integer
        expires_in = int(token_data['expires_in'])
        # Calculate expiry time, refresh 60 seconds early
        expires_at = now + timedelta(seconds=expires_in - 60)

        # Update cache (FR1.2)
        _token_cache[cache_key] = {
            'access_token': access_token,
            'expires_at': expires_at
        }
        logging.info(f"Successfully obtained new token from {token_url}")
        return access_token

    except requests.exceptions.RequestException as e:
        logging.error(f"Error requesting token from {token_url}: {e}")
        return None
    except (json.JSONDecodeError, ValueError, TypeError) as e: # Catch potential errors in response handling
        logging.error(f"Failed to process token response from {token_url}: {e}")
        return None

def require_auth(token_url_key="token_url", client_id_key="client_id", client_secret_key="client_secret"):
    """
    Decorator to ensure a valid OAuth2 token is available before calling a function.
    Injects the token as 'auth_token' kwarg.
    Implements FR1.4. Accesses config via get_config().
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = get_config() # Get loaded configuration
            if not config:
                 raise RuntimeError("Configuration not loaded. Call load_configuration first.")

            oauth_config = config.get('oauth', {})
            # Use the keys provided in the decorator call to find values in config
            token_url = oauth_config.get(token_url_key)
            # Client ID/Secret are fetched securely via loader using env var keys from config
            client_id = oauth_config.get('client_id')
            client_secret = oauth_config.get('client_secret')

            if not all([token_url, client_id, client_secret]):
                logging.error("OAuth configuration missing (token_url, client_id, client_secret).")
                raise ValueError("OAuth configuration incomplete.")

            token = get_oauth_token(client_id, client_secret, token_url)

            if not token:
                logging.error(f"Failed to obtain auth token for {func.__name__}. Aborting.")
                raise ConnectionError(f"Could not obtain authentication token for {token_url}")

            # Inject token into the decorated function's keyword arguments
            kwargs['auth_token'] = token
            return func(*args, **kwargs)
        return wrapper
    return decorator 