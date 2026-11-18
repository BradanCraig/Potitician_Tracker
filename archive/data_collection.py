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
page=0

def sleep():
    time.sleep(abs(int(norm.rvs(loc=7.5, scale=4, size=1)[0])))
    return 1


def get_information(driver, name, df):
    # Switch to the new tab (because target="_blank")
    driver.switch_to.window(driver.window_handles[-1])
    sleep()
    sleep()  # Sometimes needed in order for load times
    rows = driver.find_elements(By.XPATH, "//tbody/tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")

        date   = cols[1].text.strip()
        ticker = cols[3].text.strip()
        amount = cols[7].text.strip()
        ttype  = cols[6].text.strip()

        if ticker == "--" or ticker == "":
            print(f"ticker is {ticker} from {date}")
            continue

        print(f"{ticker} was {ttype} for {amount} on {date}")

        df.loc[len(df)] = [date, name, ticker, amount, ttype]

    # Close tab and return to list page
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return df

def click_sort(driver):
    header = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//th[normalize-space()='Date Received/Filed']"))
    )

    # Click the header using JavaScript to ensure it registers
    driver.execute_script("arguments[0].click();", header)
    sleep()

def click_next(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "filedReports_next"))
            )
        next_button.click()
        global page
        page+=1
        sleep()
        return 1
    except:
        return 0

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    driver.get("https://efdsearch.senate.gov/search/home/")

    df = pd.DataFrame(columns=["date", "name", "ticker", "amount", "type"])
    time.sleep(12)  # Line needed to check the box to move on
    
    # for i in range(17):
    #     click_next(driver)
    
    while True:
        num_rows = len(driver.find_elements(By.CSS_SELECTOR, "tbody tr"))

        for i in range(num_rows):
            # Re-find rows each time
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            row = rows[i]

            cols = row.find_elements(By.TAG_NAME, "td")
            first_name = cols[0].text.strip()
            last_name = cols[1].text.strip()
            name = " ".join([first_name, last_name])
            link_element = cols[3].find_element(By.TAG_NAME, "a")

            print(f"Clicking report for {first_name} {last_name}")

            # Click the report link
            driver.execute_script("arguments[0].click();", link_element)

            df = get_information(
                driver=driver, name=name, df=df
            )
            df.to_csv("data/information_checkpoint_top.csv")
            sleep()
        
        result = click_next(driver=driver)
        
        if result:
            print("moving onto page:", page)
            pass
        else:
            print("ended on page", page)
            break




if __name__ == "__main__":
    main()
