import argparse
import sys
import logging
import os

# Use relative imports for modules within the package
from .config.loader import load_configuration, get_config
from .utils.logging_setup import setup_logging
from .pipeline.orchestrator import run_extraction, run_processing_and_output, run_ingestion

def main():
    """Main entry point for the data ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Automated Data Ingestion Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml", # Default config path relative to execution dir
        help="Path to the configuration YAML file.",
    )
    parser.add_argument(
        "--run-mode",
        choices=["all", "extract", "process", "ingest"],
        default="all",
        help="Pipeline stages to run ('extract' implies process, 'process' runs extract+process, 'all' runs everything).",
    )
    args = parser.parse_args()

    # --- 1. Load Configuration ---
    try:
        # Ensure config path is absolute or relative to CWD
        config_path = os.path.abspath(args.config)
        config = load_configuration(config_path)
    except Exception as e:
        # Basic logging before full setup
        print(f"CRITICAL: Failed to load configuration from {args.config}. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Setup Logging ---
    # Logging setup now uses the loaded config
    try:
        setup_logging(config)
    except Exception as e:
        print(f"CRITICAL: Failed to setup logging. Error: {e}", file=sys.stderr)
        # Continue without full logging if needed, or exit
        sys.exit(1)

    logging.info(f"Starting Data Ingestion Pipeline (Run Mode: {args.run_mode})")
    logging.info(f"Using configuration file: {config_path}")

    # --- 3. Run Pipeline Stages ---
    try:
        extracted_data = None
        # Determine which stages to run based on run_mode
        should_extract = args.run_mode in ["all", "extract", "process"]
        should_process_output = args.run_mode in ["all", "process"] # 'extract' only extracts
        should_ingest = args.run_mode in ["all", "ingest"]

        if should_extract:
            extracted_data = run_extraction(config)

        if should_process_output:
            if extracted_data is not None: # Only run if extraction happened and returned data
                 run_processing_and_output(extracted_data, config)
            elif args.run_mode == "process": # If explicitly asked to process, but extraction failed/yielded nothing
                 logging.warning("Extraction yielded no data. Skipping processing and output.")

        if should_ingest:
            run_ingestion(config)

        logging.info("Data Ingestion Pipeline finished successfully.")
        sys.exit(0)

    except ValueError as ve:
        logging.critical(f"Configuration error during pipeline execution: {ve}", exc_info=True)
        sys.exit(1)
    except ConnectionError as ce:
         logging.critical(f"Connection error during pipeline execution: {ce}", exc_info=True)
         sys.exit(1)
    except Exception as e:
        logging.critical(f"An unhandled error occurred in the main pipeline: {e}", exc_info=True)
        sys.exit(1)

# Make the script executable
if __name__ == "__main__":
    main() 