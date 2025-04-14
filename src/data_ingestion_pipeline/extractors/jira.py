import requests
import logging
from .base import BaseExtractor
from ..auth.handler import require_auth

class JiraExtractor(BaseExtractor):
    """Extracts data from Jira via REST API."""
    def __init__(self, source_config, global_config):
        super().__init__(source_config, global_config)
        self.source_name = "jira"
        self.api_endpoint = self.source_config.get('api_endpoint')
        self.jql_query = self.source_config.get('jql_query', '')
        if not self.api_endpoint:
            raise ValueError("Jira API endpoint ('api_endpoint') not configured.")
        logging.info(f"Jira Extractor initialized for endpoint: {self.api_endpoint}")

    @require_auth() # Assumes OAuth config keys match defaults in config
    def extract(self, auth_token=None):
        """Extracts data from Jira based on configured JQL query."""
        logging.info(f"Starting Jira extraction: {self.jql_query or 'All accessible issues'}")
        extracted_data = []
        headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}

        # === PLACEHOLDER: Use Jira library or construct REST API calls ===
        # Example using requests (highly simplified, needs robust pagination/error handling):
        search_url = f"{self.api_endpoint.rstrip('/')}/rest/api/3/search"
        page_size = 50
        params = {
            'jql': self.jql_query,
            'fields': 'summary,description,comment,project', # Add needed fields
            'maxResults': page_size,
            'startAt': 0
        }
        total_fetched = 0

        while True:
            logging.debug(f"Fetching Jira issues starting at {params['startAt']}")
            try:
                response = requests.get(search_url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                results = response.json()
                issues = results.get('issues', [])

                if not issues:
                    logging.debug("No more Jira issues found.")
                    break # No more issues

                for issue in issues:
                    issue_key = issue.get('key')
                    fields = issue.get('fields', {})
                    summary = fields.get('summary', '')
                    # Description might be in Atlassian Document Format (ADF) - needs parsing/conversion
                    description_adf = fields.get('description', {}) # Assuming ADF object
                    description = str(description_adf) if description_adf else '' # Basic conversion placeholder
                    # Comments might also be ADF
                    comments_adf = fields.get('comment', {}).get('comments', [])
                    comments = [str(c.get('body', '')) for c in comments_adf] # Basic conversion placeholder

                    content = f"Summary: {summary}\n\nDescription: {description}\n\nComments:\n" + "\n---\n".join(comments)
                    project_key = fields.get('project', {}).get('key')
                    metadata = {
                        'project': project_key,
                        'url': f"{self.api_endpoint.rstrip('/')}/browse/{issue_key}"
                        # Add other relevant metadata like status, reporter, dates etc.
                    }

                    extracted_data.append(self._standardize_output(issue_key, 'issue', content, metadata))
                    total_fetched += 1

                # Check if we've reached the end
                current_count = params['startAt'] + len(issues)
                if current_count >= results.get('total', 0):
                    break

                params['startAt'] = current_count # Paginate

            except requests.exceptions.RequestException as e:
                logging.error(f"Jira API request failed: {e}")
                break # Stop extraction on error
            except Exception as e:
                logging.error(f"Unexpected error during Jira extraction: {e}", exc_info=True)
                break
        # === END PLACEHOLDER ===

        logging.info(f"Finished Jira extraction. Fetched {total_fetched} items.")
        return extracted_data 