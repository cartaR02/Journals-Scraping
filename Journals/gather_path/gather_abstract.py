import logging
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from web_requests import get_website
from configs.config import selenium_config
from selenium.webdriver.common.by import By

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
        (
            By.XPATH,
            "//button[contains(@class, 'cookie-notification')]//span[contains(text(), 'Accept')]/..",
        ),
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

# function will take a sequence like find|class|title~find|class|artile|4
# allowign for ~ multiple times or just ones
# will permit for a big list of example above with optional indexing like above
# a 4th item in the x|x|x|x indicates indexing a list where also expects find_all call on specific find
# returns singular item
def dedicated_find_html(csv_search_line, journal_contents_html):
    # seperate the articles and filter by keywords
    # allows for multiple iterations if smaller scope is needed
    journals_to_search = csv_search_line.split("~")
    logging.debug(f"Journals to search: {journals_to_search}")
    # search through list of classes for built in smaller scope and then on last item in list get find all
    # hoping that last call is not a find_all with no index except for journals list
    html = journal_contents_html
    #logging.debug(f"Type of html before find_all: {type(html)}")
    # TODO PRINT THIS
    #logging.debug(f"HTML: {html}")
    for finding_sequence in journals_to_search:
        contents = finding_sequence.split("|")
        if html is None:
            logging.error("Html is none in dedicated_find_html function")
            return None
        # hopes for number specific indexing with find_all TODO error check
        if len(contents) == 4:
            # unwrap for cleanner naming
            finding, html_type, container_name, index = contents
            #logging.debug(f"Searching for {finding} in {container_name} with index {index}")
            if finding == "find_all":
                html = finding_all(html_type, container_name, html)
            html = html[int(index)]
        else:
            # no fourth option index
            finding, html_type, container_name = contents
            #logging.debug(f"Searching for {finding} in {container_name}")
            if finding == "find_all":
                html = finding_all(html_type, container_name, html)
            else:
                html = finding_single(html_type, container_name, html)
    if html is None:
        logging.error("Html is none in dedicated_find_html function")
        return None
    return html
def finding_all(html_type, container_name, html):
    if html_type == "elem":
        return html.find_all(container_name)
    return html.find_all(class_=container_name)

def finding_single(html_type, container_name, html):
    if html_type == "elem":
        return html.find(container_name)
    return html.find(class_=container_name)

# just want to return the containers that hold the links that we want and will have another function handle going into link
def find_abstracts_containers(individual_journal, JOURNAL_INFO):
    phrase_list = ["research", "articles", "papers", "research article", "special article"]
    # clean-up phrase
    phrase = dedicated_find_html(JOURNAL_INFO["PHRASE_TAG"], individual_journal).text.strip().lower()

    logging.debug(f"Searching for phrase: {phrase}")
    if phrase in phrase_list:

        logging.info("Phrase Found, return html")

        return individual_journal
    logging.info("Phrase Not Found, skipping")
    return None


# TODO get proper text in abstract and allow for going into article to get actual abstract
# returns list of abstracts
# pure html so then after in a different function we will go in and gather abstracts
def create_abstract_lists(JOURNAL_INFO, journal_contents):
    # expects a state of the journal to be the smallest container of ALL the individual articles of the journal
    # it will further subdivide the inidiviual articles and gather the contents from them

    journal_list = dedicated_find_html(JOURNAL_INFO["JOURNAL_ARTICLES"], journal_contents)
    if journal_list is None or  len(journal_list) == 0:
        logging.error("Journal List is None")
        return None
    logging.debug(f"Journal List: {len(journal_list)}")
    accepted_individual_journals = []

    for journal in journal_list:
        # make the 3 a variable eventually
        if len(accepted_individual_journals)== 3:
            break
        found_abstract = find_abstracts_containers(journal, JOURNAL_INFO)


        if found_abstract is not None:
            logging.info(f"Abstract Found adding to list")
            accepted_individual_journals.append(found_abstract)

    # returns unclean html
    return accepted_individual_journals


# takes list of html surround each journals and gets link to go in and take the text
def get_abstract_text(JOURNAL_INFO, abstract_lists, driver):
    abstract_text_list = []
    for container in abstract_lists:
        link = dedicated_find_html(JOURNAL_INFO["ABSTRACT_LINK"], container).get("href")
        if link is None:
            logging.error("Unable to get Abstract link")
            continue

        logging.info(f"Abstract Link Found: {link}")
        # TODO do better way of handling the abstract link not needing a pre url
        if "lww" in link:
            url_pre = ""
        else:
            url_pre = JOURNAL_INFO["URL_PRE"]
        full_link = url_pre + link

        if JOURNAL_INFO["BYPASS"]:
            driver = selenium_config()
            abstract_html = get_website(
                full_link, driver, JOURNAL_INFO
            )

            if abstract_html is None:
                return None
        else:
            abstract_html = get_website(
                full_link, driver, JOURNAL_INFO
            )
            if abstract_html is None:
                return None
        accept_cookies(driver)
        time.sleep(1)

        if abstract_html is None:
            logging.error("Unable to get Abstract HTML")
            continue

        abstract_text = dedicated_find_html(JOURNAL_INFO["ABSTRACT_TEXT"], abstract_html)

        if abstract_text is None:
            logging.error("Unable to get Abstract Text")
            continue
        logging.info(f"Abstract Text Found")
        abstract_text_list.append(abstract_text.text.strip())

    return abstract_text_list