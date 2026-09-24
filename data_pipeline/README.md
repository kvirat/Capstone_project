# Data Pipeline Notebook

This folder contains the notebook that builds the book data pipeline.

## What it does

- scrapes product pages from Books to Scrape
- normalizes the scraped data
- converts GBP values into INR
- loads the cleaned data into SQLite
- validates SQL query results against pandas merge logic

## Run the notebook

Open the notebook in VS Code or Jupyter and run all cells in order.

```bash
jupyter notebook data_pipeline.ipynb
```

## Files

- `data_pipeline.ipynb` — full pipeline notebook
- `books.db` — SQLite database created after running the notebook
