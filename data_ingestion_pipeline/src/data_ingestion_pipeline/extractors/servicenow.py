import requests
import logging
from .base import BaseExtractor
from ..auth.handler import require_auth

class ServiceNowExtractor(BaseExtractor):
    """Extracts data from ServiceNow tables via REST API."""
    def __init__(self, source_config, global_config):
        super().__init__(source_config, global_config)
        self.source_name = "servicenow"
        self.instance_url = self.source_config.get('instance_url')
        self.tables = self.source_config.get('tables', []) # List of {'name': 'incident', 'fields': [...], 'query': '...'}
        # Note: ServiceNow might use Basic Auth or dedicated OAuth flow.
        # The @require_auth decorator assumes a compatible Bearer token flow.
        # Adjust auth method if necessary (e.g., pass user/pass, handle Basic Auth).
        if not self.instance_url:
            raise ValueError("ServiceNow instance URL ('instance_url') not configured.")
        if not self.tables:
            logging.warning("No ServiceNow tables configured.")
        logging.info(f"ServiceNow Extractor initialized for instance: {self.instance_url}")

    # Assuming OAuth Bearer token is used via global config. Adjust if needed.
    @require_auth()
    def extract(self, auth_token=None):
        """Extracts records from configured ServiceNow tables."""
        logging.info(f"Starting ServiceNow extraction from {self.instance_url}")
        extracted_data = []
        # Adjust headers based on actual auth method if not Bearer token
        headers = {'Authorization': f'Bearer {auth_token}', 'Accept': 'application/json'}

        # === PLACEHOLDER: Use ServiceNow Table API ===
        for table_config in self.tables:
            table_name = table_config.get('name')
            fields = table_config.get('fields', [])
            query = table_config.get('query', '')
            if not table_name:
                logging.warning(f"Skipping invalid ServiceNow table config: {table_config}")
                continue

            logging.debug(f"Fetching data from table: {table_name} with query: {query or 'None'}")
            api_url = f"{self.instance_url.rstrip('/')}/api/now/table/{table_name}"
            page_size = 100 # ServiceNow default limit can be higher, adjust as needed
            params = {
                'sysparm_display_value': 'false', # Get raw values
                'sysparm_exclude_reference_link': 'true',
                'sysparm_fields': ','.join(fields) if fields else '',
                'sysparm_query': query,
                'sysparm_limit': page_size,
                'sysparm_offset': 0
            }
            total_fetched_for_table = 0

            # Pagination loop
            while True:
                logging.debug(f"Fetching ServiceNow records from {table_name} starting at {params['sysparm_offset']}")
                try:
                    response = requests.get(api_url, headers=headers, params=params, timeout=60)
                    response.raise_for_status()
                    results = response.json().get('result', [])

                    if not results:
                        logging.debug(f"No more records found for table {table_name}.")
                        break

                    for record in results:
                        record_id = record.get('sys_id') # Unique ID
                        if not record_id:
                            logging.warning(f"Record missing sys_id in table {table_name}: {record}")
                            continue

                        # Combine specified fields into content string
                        content_parts = []
                        for field in fields:
                            value = record.get(field, '')
                            # Handle potential reference fields (dictionaries with link/value)
                            if isinstance(value, dict) and 'value' in value:
                                value = value['value']
                            content_parts.append(f"{field}: {value}")
                        content = "\n".join(content_parts)

                        metadata = {'table': table_name, 'sys_id': record_id}
                        # Add URL for easy access
                        metadata['url'] = f"{self.instance_url.rstrip('/')}/nav_to.do?uri={table_name}.do?sys_id={record_id}"
                        # Add other useful metadata like sys_updated_on etc. if fetched
                        if 'sys_updated_on' in record:
                             metadata['updated_on'] = record['sys_updated_on']

                        extracted_data.append(self._standardize_output(record_id, table_name, content, metadata))
                        total_fetched_for_table += 1

                    params['sysparm_offset'] += len(results)

                    # Optional: Check X-Total-Count header if reliable for stopping pagination
                    # total_count = int(response.headers.get('X-Total-Count', -1))
                    # if total_count != -1 and params['sysparm_offset'] >= total_count:
                    #    break

                except requests.exceptions.RequestException as e:
                    logging.error(f"ServiceNow API request failed for table {table_name}: {e}")
                    break # Stop for this table on error
                except Exception as e:
                    logging.error(f"Unexpected error during ServiceNow extraction for table {table_name}: {e}", exc_info=True)
                    break
            logging.info(f"Fetched {total_fetched_for_table} items from table {table_name}.")
        # === END PLACEHOLDER ===

        logging.info(f"Finished ServiceNow extraction. Fetched {len(extracted_data)} total items.")
        return extracted_data 