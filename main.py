from pathlib import Path

from scraper.data_collector import TickerScraper
from scraper.ticker_extractor import TickerExtractor

import time


def main():
    ticker_scraper = TickerScraper(
        url="https://efdsearch.senate.gov",
        start_page=6,
        sleep_interval=15,
        final_path=Path("data/scraped_trades_final.csv"),
        headless=False,
    )
    # ten seconds to click what you need
    time.sleep(10)
    ticker_scraper.start_scraping()
    ticket_extractor = TickerExtractor(ticker_scraper.final_path)
    ticket_extractor.get_ticker_info()


if __name__ == "__main__":
    main()
