import re
import logging
# from bs4 import BeautifulSoup # Optional: for more advanced HTML cleaning

def clean_text(text, is_html=False):
    """
    Basic text cleaning: remove residual HTML (if specified), normalize whitespace.
    Implements part of FR3.1.
    """
    if not text:
        return ""

    cleaned = str(text) # Ensure string type

    # Optional: More robust HTML cleaning if content source is known HTML
    if is_html:
        # Use BeautifulSoup for better tag removal than basic regex
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(cleaned, 'lxml')
            # Get text, separating block elements with newlines
            cleaned = soup.get_text(separator='\n', strip=True)
        except ImportError:
            logging.warning("BeautifulSoup4 not installed, using basic regex for HTML cleaning.")
            cleaned = re.sub('<[^<]+?>', '', cleaned) # Basic strip fallback
        except Exception as e:
            logging.error(f"Error during BeautifulSoup cleaning: {e}")
            # Fallback to basic regex on error
            cleaned = re.sub('<[^<]+?>', '', cleaned)

    # Normalize whitespace: replace multiple spaces/tabs/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Optional: Convert multiple newlines (if preserved from BS4) to single/double
    # cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()

    return cleaned 