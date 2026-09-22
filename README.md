# Books To Scrape Data Pipeline

This project scrapes book metadata from the Books to Scrape site, cleans and validates the values, stores them in SQLite, and demonstrates SQL queries against the resulting database.

## Requirements

- Python 3.10+
- Internet access to reach `https://books.toscrape.com/`

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install requests pandas beautifulsoup4
```

## Run the pipeline

```bash
python generate_books_db.py
```

This script will:

1. Scrape the first 5 pages of the catalogue.
2. Clean fields into typed columns.
3. Use median imputation for malformed numeric values.
4. Drop rows with blank/unusable text identity fields.
5. Store the result in `books.db` using a two-table SQLite schema (`categories` and `books`).
6. Run at least 5 SQL queries and print their results.

## Required fixed conversion

The project uses a fixed baseline conversion rate of `1 GBP = 105.50 INR`, with no date-based reference.

```python
INR_RATE = 105.50
```

## Parsing and cleaning decisions

- `price_gbp`: remove the `£` symbol and commas, convert to numeric, and if parsing still fails, fill with the median price for the column.
- `rating`: map `One` through `Five` to integers `1` through `5`, and fill any malformed entries with the median rating value.
- `in_stock`: convert availability text to a boolean. If the text is ambiguous or malformed, default to `False` instead of crashing the pipeline.
- Blank or unusable `title` and `category` values are dropped because they are not safely recoverable and imputing dummy text would corrupt the data.

## SQLite schema

```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    price_gbp REAL,
    price_inr REAL,
    rating INTEGER,
    in_stock INTEGER,
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
```

## Acceptance notes

The pipeline is designed to be resilient to messy rows, so it avoids crashing on bad text or malformed values while preserving as much usable data as possible.
