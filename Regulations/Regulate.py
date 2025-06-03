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
    """Clicks the search button (with class 'btn btn-primary-alt')."""
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn.btn-primary-alt[type="submit"]'))
        )
        button.click()
        time.sleep(3)
        return True
    except Exception as e:
        logging.error(f"Failed to click search button: {e}")
        return False




# Main start
if __name__ == "__main__":
    url = "https://www.regulations.gov/search/comment?filter=Attach&sortBy=postedDate&sortDirection=desc"

    html = retrieve_site_html(url)

    if not html:
        logging.info("Site did not search properly")
        sys.exit()
    

    logging.info("Initial Page loaded")

    soup_html = BeautifulSoup(html, "html.parser")
    time.sleep(2)
    
    container = soup_html.find(class_="results-container")
    # here is the wrapper container of the things we need
    attachments_list = container.find_all(class_="card card-type-comment ember-view")
    
    logging.info("Attatchment docs found")
    logging.info("Truncating List")
    logging.info(len(attachments_list))
    attachments_list = attachments_list[:5]
    logging.info(len(attachments_list))

    for article in attachments_list:

        current_link = article.find("a")

        if not current_link:
            logging.error("Link not found")
            continue

        current_link = "https://www.regulations.gov" + current_link.get("href")
        logging.info(f"Link: {current_link}")
        ids_container = article.find(class_="card-metadata")
        current_id = ""

        for li in ids_container.find_all("li"):
            if li.strong and li.strong.text.strip() == "ID":
                logging.info("ID found")
                current_id = li.get_text().replace("ID", "").strip()
                logging.info(f"ID: {current_id}")
                break

        if current_id == "":
            logging.error("ID not found")
            continue

        logging.info("Article Complete!")
        # this state is id is good and link

        comment_html = retrieve_site_html(current_link)
        
        if not comment_html:
            logging.error("Comment Page did not load")
            continue

        parse_comment = BeautifulSoup(comment_html, "html.parser")

        pdf_download = parse_comment.find(class_="btn btn-default btn-block")
        pdf_download_link = pdf_download.get("href")
        logging.info(f"pdf download link: {pdf_download_link}")


