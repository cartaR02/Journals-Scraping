import csv
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
import logging
import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import sys
import getopt

# At the beginning of your script, before setting up your own logging:
import logging

# Disable Selenium's debug logging
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)


# Then your existing logging setup
logfile = "./logs/scrape_log.{}.log".format(
    datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
)
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    filename=logfile,
                    filemode="w")

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

def selenium_config() -> webdriver:
    options: Options = Options()
    # Uncomment the next line for headless testing
    # options.add_argument("--headless")
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 1)
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options)  # type: ignore
    return driver

driver = selenium_config()


def retrieve_site_html(URL):
    try:
        driver.get(URL)

        # Add a small delay to let the cookie popup appear
        time.sleep(2)

    except Exception as e:
        logging.error(f"{URL} Failed to access: {e}")
        return None

    
    return driver.page_source

def click_filter(filter_text: str) -> bool:
    """Clicks a filter link (like 'Last 7 Days') if it exists on the page."""
    try:
        logging.info(f"Attempting to click filter: {filter_text}")
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//a[contains(text(), "{filter_text}")]'))
        )
        element.click()
        time.sleep(3)  # Allow any content refresh after click
        return True
    except Exception as e:
        logging.warning(f"Could not click filter '{filter_text}': {e}")
        return False

def type_search_query(query: str) -> bool:
    """Types a search query into the typeahead input."""
    try:
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"][placeholder="Search"]'))
        )
        input_field.clear()
        input_field.send_keys(query)
        input_field.send_keys(Keys.RETURN)  # Optional: press Enter
        time.sleep(3)  # Let search results load
        return True
    except Exception as e:
        logging.error(f"Failed to type into search input: {e}")
        return False

def click_search_button() -> bool:
    """Clicks the search button (magnifying glass) after typing a query."""
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Search"]'))
        )
        button.click()
        time.sleep(3)
        return True
    except Exception as e:
        logging.error(f"Failed to click search button: {e}")
        return False



# Main start
if __name__ == "__main__":
    url = "https://www.regulations.gov/search/comment?sortBy=postedDate&sortDirection=desc"

    html = retrieve_site_html(url)

    if html:
        logging.info("Initial Page loaded")

        if click_filter("Last 7 Days"):
            html_after_click = driver.page_source
            logging.info("Last 7 days clicked")
            if type_search_query("Attach"):
                logging.info("Attach - searched")
                click_search_button()
            else: 
                logging.info("Site did not search properly")


