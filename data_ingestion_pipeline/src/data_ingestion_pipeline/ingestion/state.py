import os
import logging
import shutil # For moving files

def find_unprocessed_files(config):
    """
    Finds files in output directories that haven't been processed.
    Simple implementation: checks existence in output dirs.
    Needs improvement for robust state tracking (e.g., log file, DB).
    """
    output_config = config.get('output', {})
    ingestion_config = config.get('ingestion', {})
    text_dir = output_config.get('text_output_dir', 'output/text')
    pdf_dir = output_config.get('pdf_output_dir', 'output/pdf')
    archive_dir = ingestion_config.get('archive_directory') # Check archive too if needed

    unprocessed = []
    processed_files_set = set() # In a real scenario, load this from a state file/DB

    # Optional: Load state from a simple log file
    state_file = ingestion_config.get('state_file', 'ingestion_state.log')
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                processed_files_set = set(line.strip() for line in f if line.strip())
            logging.debug(f"Loaded {len(processed_files_set)} processed files from state file.")
        except IOError as e:
            logging.error(f"Error reading state file {state_file}: {e}")

    for dir_path in [text_dir, pdf_dir]:
        if os.path.exists(dir_path):
            logging.debug(f"Scanning for unprocessed files in: {dir_path}")
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.lower().endswith(('.txt', '.pdf')):
                        filepath = os.path.join(root, file)
                        # Check if file is already marked as processed
                        if filepath not in processed_files_set:
                            unprocessed.append(filepath)
                        # else:
                        #    logging.debug(f"Skipping already processed file: {filepath}")
        else:
            logging.warning(f"Output directory not found: {dir_path}")

    logging.info(f"Found {len(unprocessed)} potential files for ingestion.")
    return unprocessed

def mark_file_as_processed(filepath, config):
    """
    Marks a file as processed, e.g., by moving it or logging its path.
    Implements basic state management (FR5.5).
    """
    ingestion_config = config.get('ingestion', {})
    archive_dir = ingestion_config.get('archive_directory')
    state_file = ingestion_config.get('state_file', 'ingestion_state.log')
    success = False

    # 1. Move to archive directory if configured
    if archive_dir:
        try:
            # Recreate source structure within archive dir
            relative_path = os.path.relpath(os.path.dirname(filepath), config.get('output', {}).get('base_output_dir', 'output'))
            archive_target_dir = os.path.join(archive_dir, relative_path)
            os.makedirs(archive_target_dir, exist_ok=True)
            archive_filepath = os.path.join(archive_target_dir, os.path.basename(filepath))

            shutil.move(filepath, archive_filepath)
            logging.debug(f"Moved processed file to archive: {archive_filepath}")
            success = True # Mark success if move works
        except OSError as e:
            logging.error(f"Failed to move processed file {filepath} to archive: {e}")
        except Exception as e:
             logging.error(f"Unexpected error archiving file {filepath}: {e}", exc_info=True)

    # 2. Log to state file (do this even if move fails, to prevent reprocessing attempts)
    if state_file:
        try:
            with open(state_file, 'a') as f:
                f.write(filepath + '\n')
            logging.debug(f"Marked file as processed in state file: {filepath}")
            success = True # Mark success if log works
        except IOError as e:
            logging.error(f"Failed to write to state file {state_file}: {e}")

    if not archive_dir and not state_file:
         logging.warning("No archive directory or state file configured. Cannot mark file as processed.")

    return success 