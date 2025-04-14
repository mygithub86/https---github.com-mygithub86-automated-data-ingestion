import logging
from ..extractors.base import BaseExtractor # For type hinting if needed
# Import specific extractors dynamically based on config
from ..extractors import jira, confluence, bitbucket, servicenow, html
from ..processing import cleaning, pii_filter
from ..formatting import output
from ..ingestion import reader, chunker, embedder, uploader, state
import os # Added import for os module

# Mapping from config key to extractor class
EXTRACTOR_MAP = {
    'jira': jira.JiraExtractor,
    'confluence': confluence.ConfluenceExtractor,
    'bitbucket': bitbucket.BitbucketExtractor,
    'servicenow': servicenow.ServiceNowExtractor,
    'html': html.HtmlExtractor,
}

def run_extraction(config):
    """Runs the extraction process for all configured and enabled sources."""
    logging.info("=== Starting Extraction Phase ===")
    all_extracted_data = []
    extractors_config = config.get('extractors', {})

    for source_name, source_config in extractors_config.items():
        if not isinstance(source_config, dict):
            logging.warning(f"Invalid configuration format for extractor '{source_name}'. Skipping.")
            continue

        if not source_config.get('enabled', False):
            logging.info(f"Skipping disabled extractor: {source_name}")
            continue

        logging.info(f"Running extractor: {source_name}")
        ExtractorClass = EXTRACTOR_MAP.get(source_name)
        if not ExtractorClass:
            logging.warning(f"Unknown extractor type configured: {source_name}. Skipping.")
            continue

        try:
            extractor = ExtractorClass(source_config, config)
            extracted_items = extractor.extract() # This might raise errors (e.g., auth)
            if extracted_items:
                # Basic validation of extracted items
                valid_items = [item for item in extracted_items if isinstance(item, dict) and 'id' in item and 'content' in item]
                if len(valid_items) != len(extracted_items):
                     logging.warning(f"Some items extracted from '{source_name}' had invalid format.")
                all_extracted_data.extend(valid_items)
            logging.info(f"Extractor '{source_name}' finished. Found {len(extracted_items or [])} raw items.")

        except ValueError as ve: # Catch config errors from extractor init
             logging.error(f"Configuration error for extractor '{source_name}': {ve}")
        except ConnectionError as ce: # Catch auth errors from require_auth
             logging.error(f"Authentication error for extractor '{source_name}': {ce}")
        except Exception as e:
            logging.error(f"Critical error running extractor '{source_name}': {e}", exc_info=True) # Log traceback

    logging.info(f"=== Extraction Phase Complete. Total valid items extracted: {len(all_extracted_data)} ===")
    return all_extracted_data

def process_data_item(data_item, config):
    """
    Helper function to apply cleaning and PII filtering to a single data item.
    """
    content = data_item.get('content', '')
    source = data_item.get('source', 'unknown')
    # Determine if content is likely HTML (adjust logic as needed)
    is_html_content = source in ['confluence', 'html']

    # Apply cleaning
    cleaned_content = cleaning.clean_text(content, is_html=is_html_content)

    # Apply PII filtering
    pii_config = config.get('pii_filtering', {})
    pii_filtered_content = pii_filter.filter_pii(cleaned_content, pii_config)

    # Store processed content back in the item
    data_item['processed_content'] = pii_filtered_content
    return data_item


def run_processing_and_output(extracted_data, config):
    """Runs cleaning, PII filtering, and output generation for extracted data."""
    logging.info("=== Starting Processing & Output Phase ===")
    processed_files = {'text': [], 'pdf': []}
    output_config = config.get('output', {})

    total_items = len(extracted_data)
    for i, item in enumerate(extracted_data):
        item_id = item.get('id', 'unknown')
        item_source = item.get('source', 'unknown')
        logging.debug(f"Processing item {i+1}/{total_items}: {item_source} - {item_id}")
        try:
            # Process (Clean + PII Filter)
            processed_item = process_data_item(item, config)

            # Save to Text (FR4.1)
            if output_config.get('save_text', True):
                txt_path = output.save_to_text(processed_item, output_config)
                if txt_path:
                    processed_files['text'].append(txt_path)

            # Save to PDF (FR4.2)
            if output_config.get('save_pdf', True):
                pdf_path = output.save_to_pdf(processed_item, output_config)
                if pdf_path:
                    processed_files['pdf'].append(pdf_path)

        except Exception as e:
            logging.error(f"Error during processing/output for item {item_id} from {item_source}: {e}", exc_info=True)

    logging.info(f"=== Processing & Output Phase Complete. Files created: {len(processed_files['text'])} text, {len(processed_files['pdf'])} pdf ===")
    return processed_files

def ingest_file(filepath, config):
    """Reads, chunks, embeds, and upserts a single file. Returns True on success."""
    logging.info(f"Starting ingestion process for file: {filepath}")
    file_metadata = {} # To store metadata derived from file/path

    try:
        # 1. Read File Content (FR5.1)
        content = None
        if filepath.lower().endswith('.txt'):
            content = reader.read_text_file(filepath)
        elif filepath.lower().endswith('.pdf'):
            content = reader.read_pdf_file(filepath)
        else:
            logging.warning(f"Skipping ingestion of unsupported file type: {filepath}")
            return False # Not a failure of ingestion itself, just skipping

        if content is None: # Check for read errors
            logging.error(f"Failed to read content from {filepath}. Skipping ingestion.")
            return False
        if not content.strip():
             logging.warning(f"File {filepath} is empty or contains only whitespace. Skipping.")
             return False # Treat as skippable, not failure

        # 2. Extract Metadata from Path (basic example)
        try:
            parts = filepath.split(os.sep)
            filename = parts[-1]
            source = parts[-2] # Assumes structure like output/{type}/{source}/{id}.{ext}
            item_id = os.path.splitext(filename)[0]
            file_metadata = {'source': source, 'id': item_id, 'type': 'file', 'metadata': {'original_filepath': filepath}}
        except IndexError:
            logging.warning(f"Could not parse standard metadata from filepath: {filepath}. Using basic info.")
            file_metadata = {'source': 'unknown', 'id': os.path.basename(filepath), 'type': 'file', 'metadata': {'original_filepath': filepath}}

        # 3. Chunk Text (FR5.2)
        chunk_config = config.get('chunking', {})
        chunks = chunker.chunk_text(
            content,
            strategy=chunk_config.get('strategy', 'fixed'),
            chunk_size=chunk_config.get('size', 1000),
            chunk_overlap=chunk_config.get('overlap', 100)
        )
        if not chunks:
            logging.warning(f"No chunks generated for {filepath}. Skipping.")
            return False # Treat as skippable

        logging.debug(f"Generated {len(chunks)} chunks for {filepath}.")

        # 4. Generate Embeddings (FR5.3)
        embeddings = embedder.get_openai_embeddings(chunks, config)
        if not embeddings or len(embeddings) != len(chunks):
            logging.error(f"Failed to generate embeddings for {filepath}. Aborting ingestion for this file.")
            # This is a definite failure for this file
            return False

        # 5. Upsert to Vector DB (FR5.4)
        success = uploader.upsert_to_vector_db(chunks, embeddings, file_metadata, config)

        # 6. Mark as Processed (State Management - FR5.5) - only if upsert was successful
        if success:
            state.mark_file_as_processed(filepath, config)
            logging.info(f"Successfully completed ingestion for file: {filepath}")
            return True
        else:
            logging.error(f"Failed to upsert vectors for file: {filepath}. File not marked as processed.")
            return False # Upsert failed

    except ValueError as ve: # Catch config errors (e.g., missing OpenAI key)
        logging.error(f"Configuration error during ingestion of {filepath}: {ve}")
        return False
    except ConnectionError as ce: # Catch connection errors (e.g., OpenAI, VectorDB)
        logging.error(f"Connection error during ingestion of {filepath}: {ce}")
        return False
    except Exception as e:
        logging.critical(f"Unexpected critical error during ingestion of {filepath}: {e}", exc_info=True)
        return False # Treat unexpected errors as failure

def run_ingestion(config):
    """Finds unprocessed files and runs the ingestion process for each."""
    logging.info("=== Starting Ingestion Phase ===")
    try:
        files_to_ingest = state.find_unprocessed_files(config)
        successful_ingestions = 0
        failed_ingestions = 0
        skipped_files = 0

        if not files_to_ingest:
            logging.info("No new files found to ingest.")
            logging.info("=== Ingestion Phase Complete. Successful: 0, Failed: 0, Skipped: 0 ===")
            return

        total_files = len(files_to_ingest)
        logging.info(f"Attempting to ingest {total_files} files...")

        for i, filepath in enumerate(files_to_ingest):
            logging.info(f"--- Processing file {i+1}/{total_files}: {filepath} ---")
            # ingest_file handles its own detailed logging and exceptions
            ingestion_successful = ingest_file(filepath, config)

            if ingestion_successful is True:
                successful_ingestions += 1
            elif ingestion_successful is False:
                # Check if it was a failure or just skippable (e.g., empty, unsupported type)
                # This distinction is hard without more context from ingest_file, assume False means failure for now
                 failed_ingestions += 1
            # We could add a third return state like 'skipped' from ingest_file
            # else: # Skipped
            #    skipped_files += 1

        logging.info(f"=== Ingestion Phase Complete. Successful: {successful_ingestions}, Failed: {failed_ingestions}, Skipped: {skipped_files} (approx) ===")

    except Exception as e:
         logging.critical(f"An unhandled error occurred during the ingestion phase setup or file finding: {e}", exc_info=True) 