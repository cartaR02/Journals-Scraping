import csv
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
import logging
import time
import requests
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import getopt

# At the beginning of your script, before setting up your own logging:
import logging

# Disable Selenium's debug logging
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)

with open ("key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)
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

csvFileName = "WebsiteData.csv"

# Global variable to control GPT usage
allowGPT = False

# Parse command line arguments
def parse_arguments():
    global allowGPT
    filter_id = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:G", ["id=", "gpt"])
        for opt, arg in opts:
            if opt in ("-i"):
                filter_id = arg
            elif opt in ("-G"):
                allowGPT = True
    except getopt.GetoptError:
        print('Usage: python Journals.py -i <id> [-G]')
        print('  -i <id>: Filter by journal ID')
        print('  -G: Enable GPT processing')
        sys.exit(2)
    return filter_id

def accept_cookies(driver):
    # List of common cookie accept button identifiers
    cookie_button_identifiers = [
        # Common class names
        (By.CLASS_NAME, "accept-cookies"),
        (By.CLASS_NAME, "accept-cookie"),
        (By.CLASS_NAME, "cookie-accept"),
        (By.CLASS_NAME, "cookie-consent-accept"),
        # Common IDs
        (By.ID, "onetrust-accept-btn-handler"),
        (By.ID, "accept-cookies"),
        (By.ID, "accept-cookie-consent"),
        # Common button text
        (By.XPATH, "//button[contains(text(), 'Accept')]"),
        (By.XPATH, "//button[contains(text(), 'Accept All')]"),
        (By.XPATH, "//button[contains(text(), 'Accept Cookies')]"),
        # For the specific APA website
        (By.XPATH, "//button[contains(@class, 'cookie-notification__accept')]"),
        (By.XPATH, "//button[contains(@class, 'cookie-notification')]//span[contains(text(), 'Accept')]/..")
    ]

    for by, identifier in cookie_button_identifiers:
        try:
            # Wait for a short time for each possible button
            button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((by, identifier))
            )
            button.click()
            logging.info("Successfully clicked cookie consent button")
            return True
        except:
            continue

    logging.info("No cookie consent button found or needed")
    return False

# Then modify your retrieve_site_html function to include this:
def retrieve_site_html(URL):
    try:
        driver.get(URL)

        # Add a small delay to let the cookie popup appear
        time.sleep(2)

        # Try to accept cookies
        accept_cookies(driver)

        # Continue with the rest of your code...
        time.sleep(5)
    except Exception as e:
        logging.error(f"{URL} Failed to access: {e}")
        return None

    page_source = driver.page_source
    return BeautifulSoup(page_source, "html.parser")

def gather_landing_page_containers(LANDING_PAGE_CONTAINERS, HTML):
    """
    LANDING_PAGE_CONTAINERS expects a string using a tilde (~) to separate lookup instructions.
    Each lookup instruction is pipe (|) delimited.
    The first value is the method ("find" or "find_all").
    The second value indicates whether it is an element tag ("elem") or an attribute key.
    The third value is the tag name (if element lookup) or the attribute value.

    For example:
      "find|elem|article" or "find_all|class|container"
    """
    find_list = LANDING_PAGE_CONTAINERS.split("~")
    html_to_return = HTML
    for finds in find_list:
        identifier_list = finds.split("|")
        # If the instruction doesn't have three parts, default the name to the second token.
        if len(identifier_list) < 3:
            find_operation, key_or_elem = identifier_list
            name = key_or_elem
        else:
            find_operation, key_or_elem, name = identifier_list

        FIND_ALL: bool = find_operation == "find_all"
        IS_ELEM: bool = key_or_elem == "elem"
        #logging.info("Processing lookup: " + finds)
        if IS_ELEM:
            if FIND_ALL:
                html_to_return = html_to_return.find_all(name)  # type: ignore
                #logging.info("find_all on tag: " + name)
            else:
                html_to_return = html_to_return.find(name)  # type: ignore
                logging.info("find on tag: " + name)
        else:
            attributes = {key_or_elem: name}
            if FIND_ALL:
                html_to_return = html_to_return.find_all(attrs=attributes)  # type: ignore
                logging.info("find_all on attribute: " + str(attributes))
            else:
                html_to_return = html_to_return.find(attrs=attributes)  # type: ignore
                logging.info("find on attribute: " + str(attributes))
        if html_to_return is None or (isinstance(html_to_return, list) and not html_to_return):
            logging.error("Lookup failed at step: " + finds)
            return None
    return html_to_return

def extract_article_tags(HTML):
    """
    Extracts all <article> tags from the provided BeautifulSoup HTML.
    Returns a list of article tags.
    """
    if HTML is None:
        return []
    # If HTML is a list of elements, search each one for articles
    articles = []
    if isinstance(HTML, list):
        for item in HTML:
            articles.extend(item.find_all("article"))
    else:
        articles = HTML.find_all("article")
    return articles

def ask_chat_gpt(journal_headline,Site_html):
    prompt = (
        f"Create a 500-word news story, with a headline, for this text focused on\n"
        "Using two key research project, but mentioning others below it."
        "Including the date and title of the journal."
        "Make sure the date is not in the future"
        "Use the journal headline for some context " + journal_headline
    )
    try:
        response = openai_client.chat.completions.create( model="gpt-4o-mini", messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": Site_html[:8000]}])
        msg = response.choices[0].message.content
        logging.info(msg)
    except Exception as e:
        logging.error(f"Error: {e}")


# Get the filter ID from command line arguments and set allowGPT if -G is provided
filter_id = parse_arguments()
logging.info(f"Filter ID: {filter_id if filter_id else 'None - processing all journals'}")
logging.info(f"GPT Processing: {'Enabled' if allowGPT else 'Disabled'}")

with open(csvFileName, "r", newline='', encoding='utf-8') as journal_data:
    journal_reader = csv.reader(journal_data)
    counter = 0
    for journal_row in journal_reader:
        # Skip this row if filter_id is specified and doesn't match the current journal ID
        if filter_id and journal_row[0] != filter_id:
            continue

        counter += 1
        URLS = journal_row[1]
        URL, Pre_url = URLS.split("|")
        JOURNAL_INFO = {
            "JOURNAL_ID": journal_row[0],
            "URL": URL,
            "PRE_URL": Pre_url,
            "LINK_CLASS": journal_row[2],
            "HEADLINE_CONTAINER": journal_row[3],
            "DOC_CONTAINER": journal_row[4],
        }

        html = retrieve_site_html(JOURNAL_INFO["URL"])
        if html is None:
            logging.error("HTML LENGTH: " + str(len(html)) ) # type: ignore
            print("HTML LENGTH: " + str(html) )
            logging.error("Failed to retrieve HTML for: " + JOURNAL_INFO["URL"])
            continue


        logging.info("HTML GATHERED")
        url_list = html.find_all(class_=JOURNAL_INFO["LINK_CLASS"])

        for link in url_list:
            logging.info("LINK GATHERED")
            href = link.get('href')
            logging.info(href)
            full_url = JOURNAL_INFO["PRE_URL"] + href
            site_html = retrieve_site_html(full_url)
            journal_head = site_html.find(class_=JOURNAL_INFO["HEADLINE_CONTAINER"])
            logging.info(journal_head.get_text())
            site_html = site_html.find(class_=JOURNAL_INFO["DOC_CONTAINER"])

            if site_html is None:
                logging.error("Failed to retrieve HTML for: " + full_url)
                continue
            if allowGPT:
                ask_chat_gpt(journal_head.get_text(), str(site_html))
            else:
                logging.info("GPT disabled not processing data")

driver.quit()
