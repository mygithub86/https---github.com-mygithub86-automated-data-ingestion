import logging
# import nltk # If using sentence strategy
# import spacy # If using sentence strategy

def chunk_text(text, strategy='fixed', chunk_size=1000, chunk_overlap=100):
    """
    Chunks text based on the specified strategy.
    Implements FR5.2.
    """
    if not text or not isinstance(text, str):
        logging.warning("Chunking called with empty or non-string input.")
        return []

    logging.debug(f"Chunking text using strategy '{strategy}' (size: {chunk_size}, overlap: {chunk_overlap})")
    chunks = []

    if strategy == 'fixed':
        if chunk_size <= chunk_overlap:
            logging.error(f"Chunk size ({chunk_size}) must be greater than overlap ({chunk_overlap}).")
            return [text] # Fallback to single chunk on bad config

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            next_start = start + chunk_size - chunk_overlap
            # Prevent infinite loop if step is non-positive, or if start doesn't advance
            if next_start <= start:
                 logging.warning("Chunking step is non-positive or zero, stopping early.")
                 break
            start = next_start

    elif strategy == 'sentence':
        # === PLACEHOLDER: Use NLTK or spaCy for sentence splitting ===
        logging.warning("Sentence chunking requires NLTK or spaCy implementation and model download.")
        # Example structure (needs actual implementation for combining sentences into chunks):
        try:
            import nltk
            # Ensure 'punkt' tokenizer is downloaded: nltk.download('punkt')
            sentences = nltk.sent_tokenize(text)
            logging.debug(f"Split into {len(sentences)} sentences.")
            # Simple placeholder: return sentences directly (doesn't handle chunk size limits)
            # Proper implementation needs to group sentences into chunks <= chunk_size
            chunks = sentences
        except ImportError:
           logging.error("NLTK library not installed for sentence chunking.")
           chunks = [text] # Fallback to single chunk
        except LookupError:
            logging.error("NLTK 'punkt' tokenizer not downloaded. Run nltk.download('punkt').")
            chunks = [text] # Fallback
        except Exception as e:
            logging.error(f"Error during sentence chunking: {e}", exc_info=True)
            chunks = [text] # Fallback
        # === END PLACEHOLDER ===

    # Add other strategies like 'recursive character splitting' if needed

    else:
        logging.warning(f"Unsupported chunking strategy: {strategy}. Using single chunk.")
        chunks = [text]

    logging.debug(f"Generated {len(chunks)} chunks.")
    return chunks 