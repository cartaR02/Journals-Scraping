import scrapers.content_scraper as content_scraper
from helpers import format_element
from configs.config import selenium_config
from helpers.scraper_helper import date_handler
import web_requests
import logging


""" Gathers contents for a single article.

Takes AGENCY_DATA dict, article_html tags, webdriver.

This function has two paths depending if 'Landing Page Gather' is True or False.
Unlike the other gather_contents function, this returns the dictionary that contains
the data for the db.

"""


def gather_contents(JOURNAL_INFO, issue_html, driver):

    article_contents: dict = {}

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
        JOURNAL_INFO["HEADLINE_DATA"], html, JOURNAL_INFO["AGENCY_ID"], "TITLE"
    )
    if issue_head is None:
        return None


    # TODO make sure headlines and dates are the same thing for journals

    # issue_head = format_element.format_title(
    #     issue_head, JOURNAL_INFO["HEADLINE_FORMATTING_DATA"], JOURNAL_INFO["JOURNAL_ID"]
    # )

    # if AGENCY_DATA["TITLE_REMOVE"] != "" and AGENCY_DATA["TITLE_REMOVE"] in webpage_titles.text:
    #     logging.info(f"SKIP: {JOURNAL_INFO['TITLE_REMOVE']} found in title")
    #     return None

    # issue_dates = content_scraper.scrape_content(
    #     JOURNAL_INFO["DATE_DATA"], html, JOURNAL_INFO["AGENCY_ID"], "DATE"
    # )

    if issue_head is not None:
        # extracting and formatting date, returns INVALID if date is not recent
        if isinstance(issue_head, list):
            issue_head = issue_head[0]
        issue_head = date_handler( JOURNAL_INFO["HEADLINE_FORMATTING_DATA"], issue_head.text)
        if issue_head is None:
            # globals.date_is_none.append(f"Date is None: {AGENCY_DATA['AGENCY_ID']}")
            return None
        elif issue_head == "INVALID":
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
                issue_driver, driver, issue_driver
            )
            if issue_webpage_html is None:
                return None

    article_description = gather_description(AGENCY_DATA, article_webpage_html)
    if article_description is not None:
        article_description = format_element.desc_formatter(
            article_description, AGENCY_DATA
        )
    else:
        # article description is none
        return None

    article_contents["title"] = unidecode(webpage_titles)
    article_contents["date"] = webpage_dates
    article_contents["desc"] = article_description
    article_contents["a_id"] = AGENCY_DATA["AGENCY_ID"]
    article_contents["url"] = article_link

    for key in article_contents:
        if article_contents[key] is None:
            return None

    # used for debugging the outputs
    if program_state["test_run"]:
        logging.debug(f"Titles: {article_contents['title']}")
        logging.debug(f"Dates: {article_contents['date']}")
        logging.debug(f"Desc: {article_contents['desc']}")
        logging.debug(f"Agency_id {article_contents['a_id']}")
        logging.debug(f"Article Link: {article_contents['url']}")

    return article_contents
