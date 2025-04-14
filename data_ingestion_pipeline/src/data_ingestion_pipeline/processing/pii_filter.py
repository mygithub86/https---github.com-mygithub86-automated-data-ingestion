import re
import logging
# import spacy # Import if using spacy method
# from presidio_analyzer import AnalyzerEngine # Import if using presidio method

def filter_pii(text, pii_config):
    """
    Filters PII based on configured rules (Regex or NER).
    Implements FR3.2.
    """
    if not text or not isinstance(pii_config, dict) or not pii_config.get('enabled', False):
        return text # Return original text if no config, disabled, or empty text

    method = pii_config.get('method', 'regex').lower()
    rules = pii_config.get('rules', []) # List of rule names (regex keys or NER labels)
    action = pii_config.get('action', 'mask').lower()
    mask_placeholder = pii_config.get('mask_placeholder', '[REDACTED_{label}]') # Use label in placeholder

    if not rules:
        logging.warning("PII filtering enabled but no rules defined.")
        return text

    processed_text = text
    pii_found_count = 0

    if method == 'regex':
        # === PLACEHOLDER: Basic Regex PII Example ===
        # WARNING: These are examples ONLY and likely insufficient for real PII detection.
        # Define patterns in config or load from a separate file for maintainability.
        patterns = pii_config.get('regex_patterns', {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            # 'ssn': r'\b\d{3}-\d{2}-\d{4}\b' # Example SSN - use with caution
        })

        for rule_name in rules:
            if rule_name in patterns:
                pattern = patterns[rule_name]
                placeholder = mask_placeholder.format(label=rule_name.upper())
                try:
                    if action == 'mask':
                        # Use function replacement to count matches
                        def mask_match(match):
                            nonlocal pii_found_count
                            pii_found_count += 1
                            return placeholder
                        processed_text = re.sub(pattern, mask_match, processed_text)
                    elif action == 'remove':
                         def remove_match(match):
                             nonlocal pii_found_count
                             pii_found_count += 1
                             return "" # Replace with empty string
                         processed_text = re.sub(pattern, remove_match, processed_text)
                    else:
                        logging.warning(f"Unsupported PII action '{action}' for rule '{rule_name}'.")
                except re.error as e:
                    logging.error(f"Regex error for PII rule '{rule_name}': {e}")
            else:
                 logging.warning(f"Regex PII pattern not found for configured rule: '{rule_name}'")
        # === END Regex PLACEHOLDER ===

    elif method in ['spacy', 'presidio']:
        # === PLACEHOLDER: Use spaCy or Presidio ===
        logging.warning(f"PII filtering method '{method}' requires library setup and model loading.")
        # Example structure (needs actual implementation and error handling):
        # try:
        #    if method == 'spacy':
        #        # Load model specified in config
        #        nlp = spacy.load(pii_config.get('spacy_model', 'en_core_web_sm'))
        #        doc = nlp(processed_text)
        #        # Iterate entities in reverse to avoid index issues when modifying
        #        ents_to_process = [ent for ent in doc.ents if ent.label_ in rules]
        #        for ent in reversed(ents_to_process):
        #            placeholder = mask_placeholder.format(label=ent.label_)
        #            pii_found_count += 1
        #            if action == 'mask':
        #                processed_text = processed_text[:ent.start_char] + placeholder + processed_text[ent.end_char:]
        #            elif action == 'remove':
        #                processed_text = processed_text[:ent.start_char] + processed_text[ent.end_char:]
        #
        #    elif method == 'presidio':
        #        # Initialize Presidio AnalyzerEngine
        #        analyzer = AnalyzerEngine()
        #        # Ensure 'rules' contains Presidio entity types (e.g., 'EMAIL_ADDRESS', 'PHONE_NUMBER')
        #        results = analyzer.analyze(text=processed_text, entities=rules, language='en')
        #        # Iterate results in reverse
        #        for res in reversed(results):
        #            placeholder = mask_placeholder.format(label=res.entity_type)
        #            pii_found_count += 1
        #            if action == 'mask':
        #                processed_text = processed_text[:res.start] + placeholder + processed_text[res.end:]
        #            elif action == 'remove':
        #                processed_text = processed_text[:res.start] + processed_text[res.end:]
        #
        # except ImportError as e:
        #     logging.error(f"Required library for PII method '{method}' not installed: {e}")
        # except Exception as e:
        #     logging.error(f"Error during {method} PII filtering: {e}", exc_info=True)
        # === END NER PLACEHOLDER ===
    else:
        logging.warning(f"Unsupported PII filtering method configured: {method}")

    if pii_found_count > 0:
        logging.debug(f"PII filtering applied ({pii_found_count} instance(s) found using method '{method}').")
    return processed_text 