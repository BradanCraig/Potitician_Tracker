import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time
from selenium.webdriver.support import expected_conditions as EC
from scipy.stats import norm

base_url = "https://efdsearch.senate.gov"


def sleep():
    time.sleep(int(norm.rvs(loc=15, scale=4, size=1)[0]))
    return 1


def get_information(link_element, driver, name, df):
    link_element.click()
    sleep()
    # Switch to the new tab (because target="_blank")
    driver.switch_to.window(driver.window_handles[-1])
    sleep()
    sleep()  # Sometimes needed in order for load times
    date_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[2]")
    date = date_cell.text.strip()

    ticker_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[4]")
    ticker = ticker_cell.text.strip()

    amount_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[8]")
    amount = amount_cell.text.strip()

    type_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[7]")
    type = type_cell.text.strip()

    if ticker == "--":
        print("No ticker (value is '--')")
    else:
        print(f"{ticker} was {type} for {amount} on {date}")
        df.loc[len(df)] = [date, name, ticker, amount, type]
    # Then close tab and return to results page
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return df


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    driver.get("https://efdsearch.senate.gov/search/home/")

    df = pd.DataFrame(columns=["date", "name", "ticker", "amount", "type"])
    time.sleep(12)  # Line needed to check the box to move on

    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) < 5:
                continue  # skip malformed rows

            name = cols[2].text.strip()

            # The <a> tag inside <td>
            link_element = driver.find_element(
                By.XPATH,
                "//a[@href='/search/view/ptr/61380aec-bd2b-4331-bc7c-bf00e7438280/']",
            )
            sleep()

            df = get_information(
                link_element=link_element, driver=driver, name=name, df=df
            )
            df.to_csv("data/information_checkpoint.csv")
            sleep()
        break


if __name__ == "__main__":
    main()
