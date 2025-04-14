# Automated Data Ingestion & Vectorization Pipeline

This project implements a Python pipeline to extract data from various sources
(Jira, Confluence, Bitbucket, ServiceNow, HTML), clean it, filter PII,
format it (Text/PDF), and ingest it into a vector database using OpenAI embeddings.

## Project Structure

```
data_ingestion_pipeline/
├── src/
│   └── data_ingestion_pipeline/  # Main package
│       ├── __init__.py
│       ├── auth/                 # Authentication logic
│       │   ├── __init__.py
│       │   └── handler.py
│       ├── config/               # Configuration loading
│       │   ├── __init__.py
│       │   └── loader.py
│       ├── extractors/           # Data source extractors
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── jira.py
│       │   ├── confluence.py
│       │   ├── bitbucket.py
│       │   ├── servicenow.py
│       │   └── html.py
│       ├── processing/           # Data cleaning and PII filtering
│       │   ├── __init__.py
│       │   ├── cleaning.py
│       │   └── pii_filter.py
│       ├── formatting/           # Output formatting (Text/PDF)
│       │   ├── __init__.py
│       │   └── output.py
│       ├── ingestion/            # Vector DB ingestion steps
│       │   ├── __init__.py
│       │   ├── reader.py
│       │   ├── chunker.py
│       │   ├── embedder.py
│       │   ├── uploader.py
│       │   └── state.py          # State management (finding files, archiving)
│       ├── pipeline/             # Pipeline orchestration logic
│       │   ├── __init__.py
│       │   └── orchestrator.py
│       ├── utils/                # Utility functions
│       │   ├── __init__.py
│       │   └── logging_setup.py
│       └── main.py               # Main entry point
├── config/
│   └── config.yaml             # Example configuration file
├── .env                        # Environment variables (user managed, add to .gitignore)
├── requirements.txt            # Project dependencies
└── README.md                   # This file
```

## Setup

1.  **Clone the repository.**
2.  **Create a virtual environment:** `python -m venv venv`
3.  **Activate the environment:** `source venv/bin/activate` (Linux/macOS) or `.\venv\Scripts\activate` (Windows)
4.  **Install dependencies:** `pip install -r requirements.txt`
5.  **Configure:**
    * Copy `config/config.yaml` and customize it with your settings (endpoints, queries, etc.).
    * Create a `.env` file in the project root and add your secrets (API keys, client IDs/secrets) as defined in `config.yaml` (e.g., `OAUTH_CLIENT_ID=...`, `OPENAI_API_KEY=...`). **Ensure `.env` is added to your `.gitignore` file.**
6.  **(Optional) Download NLP models:** If using `spacy` or `presidio` for PII filtering, download necessary models (e.g., `python -m spacy download en_core_web_sm`).

## Usage

Run the pipeline from the project root directory:

```bash
# Run the full pipeline (extract, process, output, ingest)
python -m src.data_ingestion_pipeline.main --config config/config.yaml --run-mode all

# Run only extraction and processing/output
python -m src.data_ingestion_pipeline.main --config config/config.yaml --run-mode process

# Run only ingestion
python -m src.data_ingestion_pipeline.main --config config/config.yaml --run-mode ingest
``` 