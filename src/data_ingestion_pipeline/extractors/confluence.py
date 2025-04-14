import requests
import logging
import re
from .base import BaseExtractor
from ..auth.handler import require_auth

class ConfluenceExtractor(BaseExtractor):
    """Extracts data from Confluence via REST API."""
    def __init__(self, source_config, global_config):
        super().__init__(source_config, global_config)
        self.source_name = "confluence"
        self.api_endpoint = self.source_config.get('api_endpoint')
        self.space_keys = self.source_config.get('space_keys', [])
        if not self.api_endpoint:
             raise ValueError("Confluence API endpoint ('api_endpoint') not configured.")
        if not self.space_keys:
             logging.warning("No Confluence space keys configured.")
        logging.info(f"Confluence Extractor initialized for endpoint: {self.api_endpoint}")

    @require_auth()
    def extract(self, auth_token=None):
        """Extracts pages from configured Confluence spaces."""
        logging.info(f"Starting Confluence extraction for spaces: {self.space_keys}")
        extracted_data = []
        headers = {'Authorization': f'Bearer {auth_token}', 'Accept': 'application/json'}

        # === PLACEHOLDER: Use Confluence library or construct REST API calls ===
        for space_key in self.space_keys:
            logging.debug(f"Fetching pages for space: {space_key}")
            content_url = f"{self.api_endpoint.rstrip('/')}/wiki/rest/api/content"
            page_size = 50
            params = {
                'spaceKey': space_key,
                'type': 'page', # Or 'blogpost'
                'limit': page_size,
                'start': 0,
                'expand': 'body.storage,version,history' # Expand necessary fields
            }
            total_fetched_for_space = 0

            while True:
                logging.debug(f"Fetching Confluence pages for space {space_key} starting at {params['start']}")
                try:
                    response = requests.get(content_url, headers=headers, params=params, timeout=30)
                    response.raise_for_status()
                    results = response.json() # Note: Confluence API might use 'results' key or be direct list
                    pages = results.get('results', []) # Adjust based on actual API response structure

                    if not pages:
                        logging.debug(f"No more pages found for space {space_key}.")
                        break

                    for page in pages:
                        page_id = page.get('id')
                        title = page.get('title', '')
                        # Content is often in 'storage' format (XML/HTML) - needs cleaning
                        content_html = page.get('body', {}).get('storage', {}).get('value', '')

                        # Basic HTML stripping (use BeautifulSoup for better results in cleaning module)
                        # raw_content = re.sub('<[^<]+?>', '', content_html) # Move cleaning to processing step
                        content = f"Title: {title}\n\n{content_html}" # Pass HTML to processing

                        metadata = {
                            'space': space_key,
                            'title': title,
                            'url': page.get('_links', {}).get('webui'),
                            'version': page.get('version', {}).get('number'),
                            'lastModified': page.get('history', {}).get('lastUpdated', {}).get('when')
                        }
                        extracted_data.append(self._standardize_output(page_id, 'page', content, metadata))
                        total_fetched_for_space += 1

                    # Check for pagination link (Confluence often uses _links.next)
                    next_page_link = results.get('_links', {}).get('next')
                    if next_page_link:
                        # Update params based on the next link (complex parsing might be needed)
                        # For simplicity, assume start/limit based pagination if next link isn't easily parsed
                        params['start'] += len(pages)
                    else:
                        break # No more pages

                except requests.exceptions.RequestException as e:
                     logging.error(f"Confluence API request failed for space {space_key}: {e}")
                     break # Stop for this space
                except Exception as e:
                    logging.error(f"Unexpected error during Confluence extraction for space {space_key}: {e}", exc_info=True)
                    break
            logging.info(f"Fetched {total_fetched_for_space} items from space {space_key}.")
        # === END PLACEHOLDER ===

        logging.info(f"Finished Confluence extraction. Fetched {len(extracted_data)} total items.")
        return extracted_data 