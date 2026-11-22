import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from scipy.stats import norm

VALID_REPORT_TYPES = [
    "Periodic Transaction Report",
    "Annual Report",
    "Candidate Report",
]


class TickerScraper:
    def __init__(
        self,
        url: str,
        final_path: Path,
        start_page: int = 0,
        sleep_interval: float = 0,
        *,
        headless: bool = False,
        check_point: Path | None = None,
    ):
        self.url = url
        self.data_frame = (
            pd.read_csv(check_point) if check_point else self.build_dataframe()
        )
        self.final_path = Path(final_path)

        self.current_page = 1
        self.page_num = start_page
        self.sleep_interval = sleep_interval
        self.headless = headless

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--ignore-certificate-errors"],
        )

        self.context = self.browser.new_context(ignore_https_errors=True)
        self.page = self.context.new_page()
        self.page.goto(self.url, wait_until="domcontentloaded")

    def sleep(self):
        delay = abs(int(norm.rvs(loc=self.sleep_interval, scale=4, size=1)[0]))
        time.sleep(delay)

    def build_dataframe(self):
        return pd.DataFrame(columns=["date", "name", "ticker", "amount", "type"])

    def add_trade(self, trade, politician_name: str):
        columns = trade.locator("td")

        date = columns.nth(1).inner_text().strip()
        ticker = columns.nth(3).inner_text().strip()
        amount = columns.nth(7).inner_text().strip()
        ttype = columns.nth(6).inner_text().strip()

        # Skip trades without a ticker
        if ticker == "--" or ticker == "":
            return

        self.data_frame.loc[len(self.data_frame)] = [
            date,
            politician_name,
            ticker,
            amount,
            ttype,
        ]

    def add_trade_from_report(self, politician_name: str):
        # Get each trade from the report
        self.sleep()
        self.page.locator("tbody tr").evaluate_all("(rows) => rows.length")
        sub_rows = self.page.locator("tbody tr")

        for i in range(sub_rows.count()):
            self.add_trade(sub_rows.nth(i), politician_name)

    def next_page(self) -> bool:
        try:
            next_button = self.page.locator("#filedReports_next")
            next_button.wait_for(state="visible", timeout=10000)

            # Check if the button is disabled
            if (
                "disabled" in (next_button.get_attribute("class") or "")
                or next_button.get_attribute("aria-disabled") == "true"
            ):
                print(f"Ending on page {self.current_page}")
                return False

            next_button.click()

            self.current_page += 1
            self.sleep()

            print(f"Moving to page {self.current_page}")
            return True

        except PlaywrightTimeoutError as e:
            print(e)
            print(f"Ending on page {self.current_page}")
            return False

    def start_scraping(self, save_check_points: bool = False):

        # Navigate to the requested starting page
        for _ in range(self.page_num):
            if not self.next_page():
                print("Could not reach requested starting page.")
                return

        while True:
            # Get the number of reports on the current page
            rows_of_trades = self.page.locator("tbody tr")
            row_count = rows_of_trades.count()

            for i in range(row_count):
                # Re-query the row each iteration
                row = self.page.locator("tbody tr").nth(i)
                cols = row.locator("td")

                first_name = cols.nth(0).inner_text().strip()
                last_name = cols.nth(1).inner_text().strip()

                name = f"{first_name} {last_name}"

                print(f"Clicking report for {name}")

                link_element = cols.nth(3).locator("a")
                report_type = link_element.text_content()

                # Check if the type of report will actually contain stock trade information
                if report_type in VALID_REPORT_TYPES:
                    # Click the report and wait for its new tab
                    try:
                        with self.context.expect_page(timeout=15000) as new_page_info:
                            link_element.evaluate("(element) => element.click()")

                        report_page = new_page_info.value

                        # Wait for report content to load
                        report_page.wait_for_load_state("domcontentloaded")

                        # Temporarily switch to the report page
                        original_page = self.page
                        self.page = report_page
                        if report_type == "Periodic Transaction Report":
                            self.add_trade_from_report(politician_name=name)
                        else:
                            if "Amendment" in report_type:
                                # The amendments are only ever images
                                pass
                            else:
                                assets_section = self.page.locator(
                                    "section.card.mb-2"
                                ).filter(has_text="Assets | Transactions")
                                assets_section

                        # Close report and return to original page
                        report_page.close()
                        self.page = original_page

                    except PlaywrightTimeoutError:
                        print(f"Report did not open for {name}")
                else:
                    continue

            # Save checkpoint
            if save_check_points:
                self.data_frame.to_csv(
                    "data/trades_checkpoint.csv",
                    index=False,
                )

            self.sleep()

            # Move to next page
            if not self.next_page():
                print("There is no next page")
                break

        # Save final results
        self.final_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data_frame.to_csv(
            self.final_path,
            index=False,
        )

        print(f"Scraping complete. Saved to {self.final_path}")

    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
