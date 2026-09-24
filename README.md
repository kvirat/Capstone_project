# Project Modules

This workspace contains three main module areas, followed by the Docker/runtime files used to run the app locally.

## data_pipeline

The data pipeline module contains the notebook-based ETL and validation workflow.

- `data_pipeline/data_pipeline.ipynb` — main notebook for scraping, transforming, and validating the data pipeline
- `data_pipeline/README.md` — notes specific to the data pipeline workflow
- `data_pipeline/requirements.txt` — dependencies for the pipeline module
- Example usage: open `data_pipeline/data_pipeline.ipynb` to run the extraction, cleaning, and SQL/pandas validation steps

## analytics

The analytics module contains notebook-based exploratory analysis and model experimentation.

- `analytics/01_eda.ipynb` — exploratory data analysis and visual investigation
- `analytics/02_modeling.ipynb` — modeling and predictive workflow examples
- `analytics/README.md` — analytics-specific notes and usage information
- `analytics/requirements.txt` — dependencies for the analytics notebooks
- `analytics/titanic.csv` — sample dataset used in the analysis workflow
- `analytics/titanic_best_pipeline.pkl` — serialized trained pipeline artifact
- Example usage: open `analytics/01_eda.ipynb` for the initial analysis, then use `analytics/02_modeling.ipynb` for modeling

## support_assistant

The support assistant module contains the RAG assistant and policy-document retrieval pipeline.

- `support_assistant/ai_support_assistant.ipynb` — main notebook for ingestion, ChromaDB indexing, retrieval, and LangGraph routing
- `support_assistant/README.md` — architecture notes and mock-vs-real-LLM behavior for the RAG flow
- `support_assistant/docs/` — source policy documents used as the knowledge base
- Example usage: run the notebook in `support_assistant/ai_support_assistant.ipynb` to load the documents, query ChromaDB, and test the support assistant pipeline

## Docker and runtime files

- `Dockerfile` — container definition for the FastAPI application
- `requirements.txt` — root project dependencies used by the runtime and app setup
- `main.py` — FastAPI entry point for the local support assistant service
- Example usage: build and run the app locally using the Docker instructions in `support_assistant/README.md` or the project Docker setup
