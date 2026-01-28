"""
Cocktail data pipeline entry point.

This script orchestrates the data pipeline:
1. Scrape Wikipedia for IBA cocktails
2. Parse the raw text files
3. Store data in SQLite database

For the web app, run: python app.py
For the desktop GUI, run: python gui.py
"""

from scraper import get_all_raw_text
from parser import parse_all_raw_text
from database import store_all_data


def run_full_pipeline():
    """Run the complete data pipeline from scraping to database storage."""
    print("Step 1: Scraping Wikipedia...")
    get_all_raw_text()

    print("Step 2: Parsing raw text...")
    all_cocktails_data, all_ingredients = parse_all_raw_text()

    print("Step 3: Storing in database...")
    store_all_data(all_cocktails_data, all_ingredients)

    print("Done!")


if __name__ == "__main__":
    # Uncomment to run the full pipeline:
    # run_full_pipeline()

    # Or run individual steps:
    # get_all_raw_text()
    # all_cocktails_data, all_ingredients = parse_all_raw_text()
    # store_all_data(all_cocktails_data, all_ingredients)

    print("See cocktails.py for pipeline functions.")
    print("Run 'python app.py' for web app or 'python gui.py' for desktop GUI.")
