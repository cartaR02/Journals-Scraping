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
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 2)
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options)  # type: ignore
    return driver

driver = selenium_config()

csvFileName = "WebsiteData.csv"

def retrieve_site_html(URL):
    try:
        driver.get(URL)
        # Wait up to 30 seconds for a <journalhome> element to be present.
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "journalhome"))
        )
    except Exception as e:
        logging.error(f"{URL} Failed to access: {e}")
        return None
    # Get page source after the dynamic content is loaded
    page_source = driver.page_source
    site_html = BeautifulSoup(page_source, "html.parser")

    return site_html

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

def ask_chat_gpt(Site_html):
    prompt = (
        f"Create a 500-word news story, with a headline, for this text focused on\n"
        "Using two key research project, but mentioning others below it."
        "Including the date and title of the journal."
    )
    try:
        response = openai_client.chat.completions.create( model="gpt-4", messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": site_html}])
        msg = response.choices[0].message.content
        print(msg)
    except Exception as e:
        logging.error(f"Error: {e}")


with open(csvFileName, "r", newline='', encoding='utf-8') as journal_data:
    journal_reader = csv.reader(journal_data)
    counter = 0
    for journal_row in journal_reader:
        counter += 1
        JOURNAL_INFO = {
            "JOURNAL_ID": journal_row[0],
            "URL": journal_row[1],
            "CONTAINER_IDENTIFIERS": journal_row[2]
        }

        html = retrieve_site_html(JOURNAL_INFO["URL"])
        if html is None:
            logging.error("Failed to retrieve HTML for: " + JOURNAL_INFO["URL"])
            continue


        logging.info("Complete")
        url_list = html.find_all(class_="article-title")
        logging.info(url_list)

        for link in url_list:
            href = link.get('href')

            full_url = "https://psycnet.apa.org" + href
            site_html = retrieve_site_html(full_url)
            site_html = site_html.find(class_="record-details row")
            logging.info(site_html.prettify())
            print("Link gatherd")

driver.quit()