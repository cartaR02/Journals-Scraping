from helpers.format_element import format_title, issue_formatter
import scrapers.content_scraper as content_scraper
from scrapers.container_scraper import get_containers
from configs.config import selenium_config
from helpers.scraper_helper import date_handler
import web_requests
import logging
from unidecode import unidecode

from helpers.scraper_helper import create_abstract_lists

""" Gathers contents for a single article.

Takes AGENCY_DATA dict, article_html tags, webdriver.

This function has two paths depending if 'Landing Page Gather' is True or False.
Unlike the other gather_contents function, this returns the dictionary that contains
the data for the db.

"""


def gather_content(JOURNAL_INFO, issue_html, driver):

    journal_contents: dict = {}

    landing_page_link = content_scraper.scrape_content(
        JOURNAL_INFO["LINK_DATA"], issue_html, JOURNAL_INFO["JOURNAL_ID"], "LINK"
    )

    try:
        if isinstance(landing_page_link, list):
            landing_page_link = landing_page_link[0]

        if landing_page_link.get("href") is None:

            landing_page_link = landing_page_link.find("a")
            if landing_page_link is None:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {JOURNAL_INFO['JOURNAL_ID']}"
                )
                return None

        issue_link = JOURNAL_INFO["URL_PRE"] + landing_page_link.get("href").strip()

    except (TypeError, AttributeError) as err:
        globals.article_link_href_typeerror_none.append(
            f"{JOURNAL_INFO['JOURNAL_ID']} {JOURNAL_INFO['LINK_DATA']}"
        )
        logging.error(
            f"SKIP: landing_page_link.get('href') is giving a 'None' value: {JOURNAL_INFO['JOURNAL_ID']}\n{err}"
        )
        return None

    issue_webpage_html = ""

    # navigating into the article
    if not JOURNAL_INFO["LANDING_PAGE_GATHERING"]:

        if JOURNAL_INFO["BYPASS"]:
            issue_driver = selenium_config()
            issue_webpage_html = web_requests.get_website(
                issue_link, issue_driver, JOURNAL_INFO
            )
            issue_driver.quit()
            if issue_webpage_html is None:
                return None
        else:
            issue_webpage_html = web_requests.get_website(
                issue_link, driver, JOURNAL_INFO
            )
            if issue_webpage_html is None:
                return None

    html = (
        issue_html if JOURNAL_INFO["LANDING_PAGE_GATHERING"] else issue_webpage_html
    )

    issue_head = content_scraper.scrape_content(
        JOURNAL_INFO["HEADLINE_DATA"], html, JOURNAL_INFO["JOURNAL_ID"], "TITLE"
    )
    if issue_head is None:
        return None


    # TODO make sure headlines and dates are the same thing for journals

    issue_head = format_title(
        issue_head, JOURNAL_INFO["HEADLINE_FORMATTING_DATA"], JOURNAL_INFO["JOURNAL_ID"]
    )

    # if AGENCY_DATA["TITLE_REMOVE"] != "" and AGENCY_DATA["TITLE_REMOVE"] in webpage_titles.text:
    #     logging.info(f"SKIP: {JOURNAL_INFO['TITLE_REMOVE']} found in title")
    #     return None

    issue_dates = content_scraper.scrape_content(
        JOURNAL_INFO["DATE_DATA"], html, JOURNAL_INFO["JOURNAL_ID"], "DATE"
    )

    if issue_dates is not None:
        # extracting and formatting date, returns INVALID if date is not recent
        if isinstance(issue_dates, list):
            issue_dates = issue_dates[0]
        issue_dates = date_handler( JOURNAL_INFO["DATE_FORMATTING_DATA"], issue_dates.text)
        if issue_dates is None:
            # globals.date_is_none.append(f"Date is None: {AGENCY_DATA['AGENCY_ID']}")
            return None
        elif issue_dates == "INVALID":
            return str("INVALID")

    # code duplication to save runtime
    # don't want to enter the article if date is invalid
    if JOURNAL_INFO["LANDING_PAGE_GATHERING"]:

        if JOURNAL_INFO["BYPASS"]:
            issue_driver = selenium_config()
            issue_webpage_html = web_requests.get_website(
                issue_link, issue_driver, JOURNAL_INFO
            )
            issue_driver.quit()
            if issue_webpage_html is None:
                return None
        else:
            issue_webpage_html = web_requests.get_website(
                issue_link, driver, JOURNAL_INFO
            )
            if issue_webpage_html is None:
                return None

    raw_journal_data = gather_journal_data(JOURNAL_INFO, issue_webpage_html)

    abstract_lists = create_abstract_lists(JOURNAL_INFO, raw_journal_data)

    abstract_text = get_abstract_text(JOURNAL_INFO, abstract_lists)

    if raw_journal_data is not None:
        journal_data = issue_formatter(
            raw_journal_data, JOURNAL_INFO
        )
    else:
        # article description is none
        return None

    #furthuer subdivide base information

    journal_contents["head"] = unidecode(issue_head)
    journal_contents["date"] = issue_dates
    journal_contents["jdata"] = journal_data
    journal_contents["abstract_lists"] = abstract_lists
    journal_contents["a_id"] = JOURNAL_INFO["JOURNAL_ID"]
    journal_contents["url"] = issue_link

    for key in journal_contents:
        if journal_contents[key] is None:
            return None

    # used for debugging the outputs
    logging.debug(f"Titles: {journal_contents['head']}")
    logging.debug(f"Dates: {journal_contents['date']}")
    #logging.debug(f"Desc: {journal_contents['jdata']}")
    logging.debug(f"Journal_id {journal_contents['a_id']}")
    logging.debug(f"Article Link: {journal_contents['url']}")
    logging.debug(f"Abstracts: {journal_contents['abstract_lists']}")

    return journal_contents


# gather_description handles the description gathering for the different gather branches
def gather_journal_data(JOURNAL_INFO, issue_webpage_html):

    alternate_journal_data = JOURNAL_INFO["JOURNAL_INFO_DATA"].split("<>")
    # preventing local unbound error
    journal_data = None

    for issue in alternate_journal_data:
        issue_split_data = issue.split("~")

        # making this expecting the max to be 2
        if len(issue_split_data) == 2:
            # finding a container for description
            issue_webpage_html = get_containers(
                issue_split_data[0], issue_webpage_html
            )
            issue = issue_split_data[1]
            if issue_webpage_html == None:
                continue

        journal_data = content_scraper.scrape_content(
            issue,
            issue_webpage_html,
            JOURNAL_INFO["JOURNAL_ID"],
            "DESC",
        )
        if journal_data != None:
            break

    return journal_data
