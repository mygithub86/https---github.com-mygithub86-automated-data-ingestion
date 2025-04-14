import logging
import re
# import pinecone # If using Pinecone
# import weaviate # If using Weaviate
# etc.

def upsert_to_vector_db(chunks, embeddings, file_metadata, config):
    """
    Upserts chunks and embeddings to the configured Vector DB.
    Implements FR5.4.
    """
    if not chunks or not embeddings or len(chunks) != len(embeddings):
        logging.error("Mismatch between chunks and embeddings for upsert.")
        return False

    db_config = config.get('vector_database', {})
    db_type = db_config.get('type', 'pinecone').lower()
    index_name = db_config.get('index_name')
    # API key loaded securely by config loader
    api_key = db_config.get('api_key')
    environment = db_config.get('environment') # e.g., for Pinecone

    if not all([db_type, index_name, api_key]): # Environment might be optional for some DBs
         logging.error("Vector DB configuration incomplete (type, index_name, api_key).")
         return False

    logging.debug(f"Upserting {len(chunks)} vectors to {db_type} index '{index_name}'.")

    # === PLACEHOLDER: Use specific Vector DB client ===
    logging.warning(f"Vector DB upsert requires client implementation for '{db_type}'.")

    if db_type == 'pinecone':
        # Example structure for Pinecone:
        try:
            import pinecone
            # Initialize connection
            pinecone.init(api_key=api_key, environment=environment)
            if index_name not in pinecone.list_indexes():
                logging.error(f"Pinecone index '{index_name}' does not exist in environment '{environment}'.")
                # Optionally create index if configured:
                # if db_config.get('create_index_if_not_exists', False):
                #     dimension = len(embeddings[0]) # Get dimension from first embedding
                #     metric = db_config.get('metric', 'cosine')
                #     pinecone.create_index(index_name, dimension=dimension, metric=metric)
                #     logging.info(f"Created Pinecone index '{index_name}'.")
                # else:
                #     return False
                return False # Fail if index doesn't exist and creation isn't enabled

            index = pinecone.Index(index_name)
            batch_size = db_config.get('batch_size', 100) # Pinecone recommends batching

            vectors_to_upsert = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create a unique ID for each vector chunk
                vector_id = f"{file_metadata.get('id', 'unknown')}_chunk_{i}"
                # Prepare metadata payload - ensure values are compatible with the DB
                chunk_metadata = {
                    'text': chunk[:db_config.get('max_metadata_text_length', 1000)], # Store truncated chunk
                    'source': file_metadata.get('source'),
                    'source_id': file_metadata.get('id'),
                    'source_type': file_metadata.get('type'),
                    'chunk_index': i,
                    **(file_metadata.get('metadata', {})) # Add original file metadata
                }
                # Sanitize metadata: Pinecone accepts str, bool, float, list[str]
                sanitized_metadata = {k: v for k, v in chunk_metadata.items() if isinstance(v, (str, int, float, bool, list))}
                # Convert lists to list[str] if needed, handle nested dicts if supported/needed
                for k, v in sanitized_metadata.items():
                    if isinstance(v, list) and not all(isinstance(item, str) for item in v):
                         sanitized_metadata[k] = [str(item) for item in v] # Example conversion

                vectors_to_upsert.append({'id': vector_id, 'values': embedding, 'metadata': sanitized_metadata})

                # Upsert in batches
                if len(vectors_to_upsert) >= batch_size:
                    logging.debug(f"Upserting batch of {len(vectors_to_upsert)} vectors to Pinecone...")
                    upsert_response = index.upsert(vectors=vectors_to_upsert)
                    logging.debug(f"Pinecone batch upsert response: {upsert_response}")
                    vectors_to_upsert = [] # Reset batch

            # Upsert any remaining vectors
            if vectors_to_upsert:
                logging.debug(f"Upserting final batch of {len(vectors_to_upsert)} vectors to Pinecone...")
                upsert_response = index.upsert(vectors=vectors_to_upsert)
                logging.debug(f"Pinecone final batch upsert response: {upsert_response}")

            logging.debug(f"Finished upserting vectors to Pinecone index '{index_name}'.")
            return True

        except ImportError:
             logging.error("Pinecone client library not installed.")
             return False
        except Exception as e:
            # Catch specific Pinecone API errors if possible
            logging.error(f"Error upserting to Pinecone: {e}", exc_info=True)
            return False

    # Add elif blocks for other DB types (weaviate, chroma, qdrant) following similar patterns
    # elif db_type == 'weaviate': ...
    # elif db_type == 'chroma': ...

    else:
        logging.error(f"Vector DB type '{db_type}' upsert logic not implemented.")
        return False
    # === END PLACEHOLDER === 