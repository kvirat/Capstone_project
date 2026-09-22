import sqlite3
from typing import Dict, List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas.testing import assert_frame_equal
from urllib.parse import urljoin

BASE_URL = "https://books.toscrape.com/"
INR_RATE = 105.50
DB_PATH = "books.db"


def scrape_book(book_url: str) -> dict:
    """Fetch and extract the key metadata fields from a single book page."""
    response = requests.get(book_url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1").text.strip()
    price = soup.find("p", class_="price_color").text.strip()
    availability = soup.find("p", class_="availability").get_text(" ", strip=True)
    rating_element = soup.find("p", class_="star-rating")
    star_rating = rating_element["class"][1]
    breadcrumb = soup.select("ul.breadcrumb li a")
    category = breadcrumb[-1].text.strip()

    return {
        "title": title,
        "price": price,
        "star_rating": star_rating,
        "availability": availability,
        "category": category,
    }


def build_dataframe() -> pd.DataFrame:
    """Scrape all catalog pages, clean the fields, and return a typed DataFrame."""
    all_books: List[dict] = []

    for page in range(1, 6):
        page_url = f"{BASE_URL}catalogue/page-{page}.html"
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        books = soup.find_all("article", class_="product_pod")

        for book in books:
            relative_url = book.h3.a["href"]
            book_url = urljoin(page_url, relative_url)
            all_books.append(scrape_book(book_url))

    df = pd.DataFrame(all_books)

    # Numeric column: use median for malformed values instead of crashing the whole pipeline.
    df["price_gbp"] = (
        df["price"]
        .astype(str)
        .str.strip()
        .str.replace("Â", "", regex=False)
        .str.replace("£", "", regex=False)
        .str.replace(",", "", regex=False)
        .apply(pd.to_numeric, errors="coerce")
    )
    median_price = df["price_gbp"].median()
    df["price_gbp"] = df["price_gbp"].fillna(median_price)

    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    df["rating"] = df["star_rating"].map(rating_map)
    median_rating = df["rating"].median()
    df["rating"] = df["rating"].fillna(median_rating).astype(int)

    df["in_stock"] = (
        df["availability"]
        .fillna("")
        .astype(str)
        .str.contains("In stock", case=False, na=False)
    )

    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["category"] = df["category"].fillna("").astype(str).str.strip()
    df = df[(df["title"] != "") & (df["category"] != "")].reset_index(drop=True)

    df["price_inr"] = (df["price_gbp"].astype(float) * INR_RATE).round(2)
    df = df.drop(columns=["price", "star_rating", "availability"])

    return df


def create_database(df: pd.DataFrame) -> None:
    """Write the cleaned book data into the SQLite database with categories and books tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.execute("DROP TABLE IF EXISTS books")
    conn.execute("DROP TABLE IF EXISTS categories")

    conn.execute(
        """
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL UNIQUE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price_gbp REAL,
            price_inr REAL,
            rating INTEGER,
            in_stock INTEGER,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
        """
    )

    category_series = (
        df["category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
    )

    category_df = pd.DataFrame(
        {
            "category_id": range(1, len(category_series) + 1),
            "category_name": category_series.tolist(),
        }
    )

    category_df.to_sql("categories", conn, index=False, if_exists="append")
    category_lookup = dict(zip(category_df["category_name"], category_df["category_id"]))

    book_rows = []
    for row in df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]].itertuples(index=False):
        title = str(row.title).strip()
        price_gbp = float(row.price_gbp)
        price_inr = float(row.price_inr)
        rating = int(row.rating)
        in_stock = int(bool(row.in_stock))
        category_name = str(row.category).strip()
        category_id = int(category_lookup.get(category_name, 0))
        book_rows.append((title, price_gbp, price_inr, rating, in_stock, category_id))

    conn.executemany(
        """
        INSERT INTO books (title, price_gbp, price_inr, rating, in_stock, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        book_rows,
    )
    conn.commit()
    conn.close()


def run_queries() -> Dict[str, pd.DataFrame]:
    """Execute the required SQL queries, print their results, and validate the SQL join against pandas."""
    conn = sqlite3.connect(DB_PATH)

    queries = {
        "select_where": """
            SELECT title, price_inr, rating
            FROM books
            WHERE in_stock = 1 AND rating >= 4
            ORDER BY price_inr DESC
            LIMIT 10
        """,
        "order_by": """
            SELECT title, price_inr
            FROM books
            ORDER BY price_inr DESC
            LIMIT 10
        """,
        "limit": """
            SELECT title, rating
            FROM books
            ORDER BY rating DESC, title ASC
            LIMIT 5
        """,
        "distinct": """
            SELECT DISTINCT category_id
            FROM books
            ORDER BY category_id
        """,
        "between": """
            SELECT title, price_inr, rating
            FROM books
            WHERE price_inr BETWEEN 4000 AND 6000
            ORDER BY price_inr ASC
            LIMIT 10
        """,
        "join": """
            SELECT c.category_name, b.title, b.rating
            FROM books b
            JOIN categories c ON c.category_id = b.category_id
            ORDER BY c.category_name ASC, b.rating DESC, b.title ASC
            LIMIT 10
        """,
    }

    outputs: Dict[str, pd.DataFrame] = {}
    for name, query in queries.items():
        df_q = pd.read_sql(query, conn)
        outputs[name] = df_q
        print(f"\n--- {name.upper()} ---")
        print(query.strip())
        print(df_q.head(10).to_string(index=False))

    books_df_in_memory = pd.read_sql(
        "SELECT book_id, title, price_gbp, price_inr, rating, in_stock, category_id FROM books ORDER BY book_id",
        conn,
    )
    categories_df_in_memory = pd.read_sql(
        "SELECT category_id, category_name FROM categories ORDER BY category_id",
        conn,
    )

    df_join_merge = (
        books_df_in_memory
        .merge(categories_df_in_memory, on="category_id", how="left")
        .loc[:, ["title", "category_name", "rating"]]
        .sort_values(["category_name", "rating", "title"], ascending=[True, False, True])
        .head(10)
        .reset_index(drop=True)
    )

    print("\nJOIN via SQL:")
    print(outputs["join"].to_string(index=False))
    print("\nJOIN via pd.merge:")
    print(df_join_merge.to_string(index=False))

    df_join_sql = outputs["join"].loc[:, ["category_name", "title", "rating"]].reset_index(drop=True)
    df_join_merge = df_join_merge.loc[:, ["category_name", "title", "rating"]].reset_index(drop=True)
    assert_frame_equal(df_join_sql, df_join_merge)
    conn.close()

    return outputs


def main() -> None:
    """Run the end-to-end scraping, validation, database loading, and SQL verification pipeline."""
    df = build_dataframe()
    print(f"\nRows scraped: {len(df)}")
    print(f"Categories: {df['category'].nunique()}")
    print(df.dtypes)
    print(df.head(5).to_string(index=False))

    assert len(df) >= 60, f"Expected at least 60 rows, got {len(df)}"
    assert df["category"].nunique() >= 3, f"Expected at least 3 categories, got {df['category'].nunique()}"
    assert {"price_gbp", "rating", "in_stock", "price_inr"}.issubset(df.columns)
    assert pd.api.types.is_float_dtype(df["price_gbp"])
    assert pd.api.types.is_integer_dtype(df["rating"])
    assert pd.api.types.is_bool_dtype(df["in_stock"])
    assert pd.api.types.is_float_dtype(df["price_inr"])

    create_database(df)
    run_queries()


if __name__ == "__main__":
    main()
