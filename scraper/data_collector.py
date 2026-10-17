import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time
from selenium.webdriver.support import expected_conditions as EC
from scipy.stats import norm


class TickerScraper:
    def __init__(
        self,
        url: str,
        start_page: int = 0,
        sleep_interval: float = 0,
        *,
        headless: bool = False,
    ):
        self.url = url
        self.data_frame = self.build_dataframe()
        # TODO: check if this is right
        self.sleep = (
            time.sleep(abs(int(norm.rvs(loc=sleep_interval, scale=4, size=1)[0])))
            if sleep_interval
            else None
        )
        self.page_num: int = start_page

        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.url)

    def build_dataframe(self):
        return pd.DataFrame(columns=["date", "name", "ticker", "amount", "type"])

    def add_trade(self, trade, politician_name: str):
        columns = trade.find_elements(By.TAG_NAME, "td")
        date = columns[1].text.strip()
        ticker = columns[3].text.strip()
        amount = columns[7].text.strip()
        ttype = columns[6].text.strip()

        # ticker doesn't exist so pass
        if ticker == "--" or ticker == "":
            return

        self.df.loc[len(self.df)] = [date, politician_name, ticker, amount, ttype]

    def add_trade_from_report(self, politician_name: str):
        # Switch to the new tab that was spawned from clicking the row
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.sleep()
        # Get each trade from report

        sub_rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        [self.add_trade(trade) for trade in sub_rows]

        # Close tab and return to list page
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def next_page(self) -> bool:
        try:
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "filedReports_next"))
            )
            next_button.click()

            self.page += 1
            self.sleep()
            print(f"Moving to page {self.page_num}")
            return 1

        except:
            print(f"Ending on page {self.page_num}")
            return 0

    def start_scraping(self, save_check_points: bool = False):
        # Go to start page
        for i in range(self.page_num):
            self.next_page()

        while True:
            # get number of rows of trades per page
            rows_of_trades = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")

            for i in range(len(rows_of_trades)):
                row = rows_of_trades[i]
                cols = row.find_elements(By.TAG_NAME, "td")

                first_name = cols[0].text.strip()
                last_name = cols[1].text.strip()
                name = f"{first_name} {last_name}"

                # Select the specific report
                print(f"Clicking report for {first_name} {last_name}")
                link_element = cols[3].find_element(By.TAG_NAME, "a")
                self.driver.execute_script("arguments[0].click();", link_element)
                self.add_trade_from_report(name)

            if save_check_points:
                self.data_frame.to_csv("data/trades_checkpoint.csv")

            self.sleep()
            result = self.next_page()
            if result:
                self.data_frame.to_csv("data/scraped_trades_final.csv")
                break
