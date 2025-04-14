import requests
import logging
import re
from .base import BaseExtractor
# Import BeautifulSoup within the method to avoid making it a hard dependency if not used
# from bs4 import BeautifulSoup

class HtmlExtractor(BaseExtractor):
    """Extracts content from a list of HTML URLs."""
    def __init__(self, source_config, global_config):
        super().__init__(source_config, global_config)
        self.source_name = "html"
        self.urls = self.source_config.get('urls', [])
        self.content_selector = self.source_config.get('content_selector') # Optional CSS selector
        if not self.urls:
            logging.warning("No HTML URLs configured.")
        logging.info(f"HTML Extractor initialized for {len(self.urls)} URLs.")

    def extract(self):
        """Extracts text content from configured HTML pages."""
        logging.info(f"Starting HTML extraction for {len(self.urls)} URLs.")
        extracted_data = []
        # Define a user agent to be polite
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; DataIngestionBot/1.0; +http://yourdomain.com/bot)'}

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logging.error("BeautifulSoup4 library not found. Please install 'beautifulsoup4' and 'lxml'. Skipping HTML extraction.")
            return []

        for url in self.urls:
            logging.debug(f"Fetching HTML from: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
                response.raise_for_status()
                # Try to determine encoding, fall back to utf-8
                response.encoding = response.apparent_encoding or 'utf-8'

                soup = BeautifulSoup(response.text, 'lxml') # Use lxml parser for speed/robustness

                # Remove script, style, nav, header, footer elements for cleaner content
                for element_type in ["script", "style", "nav", "header", "footer", "aside"]:
                    for element in soup.find_all(element_type):
                        element.decompose()

                # Extract content based on selector or fallback to body
                text_content = ''
                if self.content_selector:
                    content_elements = soup.select(self.content_selector)
                    if content_elements:
                        text_content = "\n".join(elem.get_text(separator='\n', strip=True) for elem in content_elements)
                    else:
                        logging.warning(f"CSS selector '{self.content_selector}' not found on {url}. Falling back to body.")
                        # Fallback if selector doesn't match
                        if soup.body:
                            text_content = soup.body.get_text(separator='\n', strip=True)
                elif soup.body:
                    # Fallback: Get text from the main body if no selector provided
                    text_content = soup.body.get_text(separator='\n', strip=True)

                # Perform basic cleaning on the extracted text
                cleaned_content = re.sub(r'\n{3,}', '\n\n', text_content).strip() # Collapse multiple newlines

                if cleaned_content:
                    metadata = {'url': url, 'title': soup.title.string.strip() if soup.title and soup.title.string else ''}
                    # Use URL as ID for HTML source
                    extracted_data.append(self._standardize_output(url, 'webpage', cleaned_content, metadata))
                else:
                    logging.warning(f"No meaningful content extracted from {url} after cleaning.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch HTML from {url}: {e}")
            except Exception as e:
                logging.error(f"Error parsing HTML from {url}: {e}", exc_info=True)
        # === END HTML Extraction Logic ===

        logging.info(f"Finished HTML extraction. Fetched {len(extracted_data)} items.")
        return extracted_data 