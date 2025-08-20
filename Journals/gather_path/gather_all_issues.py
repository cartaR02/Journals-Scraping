import scrapers.content_scraper as content_scraper
import scrapers.container_scraper as container_scraper
from configs.config import selenium_config
import db.storage as storage
from scrapers.container_scraper import get_containers
from helpers import format_element
from helpers.scraper_helper import date_handler
from unidecode import unidecode
import web_requests
import logging


""" Gathers contents for all articles.

Takes JOURNAL_INFO dict, issue_html tags, webdriver, db_data.

This function has two paths depending if 'Landing Page Gather' is True or False.
Unlike the other gather_contents function, this transfers data right into the database
and doesn't return unless there is a failure.

"""


def gather_contents(JOURNAL_INFO, issue_html, driver, db_data, allowGPT):
    journal_contents = {}

    # checking if data should be gathered before traversing article link
    if not JOURNAL_INFO["LANDING_PAGE_GATHERING"]:

        # gathering all links on landing page
        landing_page_link = content_scraper.scrape_content(
            JOURNAL_INFO["LINK_DATA"], issue_html, JOURNAL_INFO["JOURNAL_ID"], "LINK"
        )

        invalid_counter = 0
        if landing_page_link is None:
            # globals.link_is_none.append(f"None Link: {JOURNAL_INFO['JOURNAL_ID']}")
            return None
        # parsing through each link
        for link in landing_page_link:

            if invalid_counter > 3:
                break

            # !Bug Potential
            # TODO create a error handler that skips if href isn't found
            # Will only work if first <a> under container class if the correct href
            if link.get("href") is None:
                link = link.find("a")

            try:
                issue_link = JOURNAL_INFO["URL_PRE"] + link.get("href").strip()
            except TypeError:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {JOURNAL_INFO['JOURNAL_ID']}"
                )
                return None

            issue_webpage_html = ""

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

            issue_heads = content_scraper.scrape_content(
                JOURNAL_INFO["HEADLINE_DATA"],
                issue_webpage_html,
                JOURNAL_INFO["JOURNAL_ID"],
                "TITLE",
            )

            issue_heads = format_element.format_title(
                issue_heads,
                JOURNAL_INFO["HEADLINE_FORMATTING_DATA"],
                JOURNAL_INFO["JOURNAL_ID"],
            )

            if issue_heads is None:
                # globals.title_is_none.append(f"None Title: {JOURNAL_INFO['JOURNAL_ID']}")
                return None

            issue_dates = content_scraper.scrape_content(
                JOURNAL_INFO["DATE_DATA"],
                issue_webpage_html,
                JOURNAL_INFO["JOURNAL_ID"],
                "DATE",
            )

            # extracting and formatting date, returns INVALID if date is not recent
            if issue_dates is not None:
                issue_dates = date_handler(
                    JOURNAL_INFO["DATE_FORMATTING_DATA"], JOURNAL_INFO["FULL_URL"], issue_dates.text
                )
                if issue_dates is None:
                    continue
                elif issue_dates == "INVALID":
                    invalid_counter += 1
                    continue

            # inserting data into dict
            journal_contents["head"] = unidecode(issue_heads)
            journal_contents["date"] = issue_dates
            journal_contents["a_id"] = JOURNAL_INFO["JOURNAL_ID"]
            journal_contents["url"] = issue_link

            # returns true if duplicate found so we skip it here
            # sets article data before doing description to avoid excess computation
            if storage.skip_duplicates(db_data, journal_contents):
                return None

            journal_data = gather_journal_data(JOURNAL_INFO, issue_webpage_html)
            if journal_data is not None:
                journal_data = format_element.issue_formatter(journal_data, JOURNAL_INFO)

            journal_contents["jdata"] = journal_data
            # checking to see if nothing was scraped for any elements
            for key in journal_contents:
                if journal_contents[key] is None:
                    return None



            logging.debug(f"Titles: {journal_contents['head']}")
            logging.debug(f"Dates: {journal_contents['date']}")
            #logging.debug(f"Desc: {journal_contents['jdata']}")
            logging.debug(f"Journal_id {journal_contents['a_id']}")
            logging.debug(f"Article Link: {journal_contents['url']}")

            # inserting data into the db
            storage.db_insert(db_data, journal_contents, allowGPT)

    else:

        issue_heads = content_scraper.scrape_content(
            JOURNAL_INFO["HEADLINE_DATA"],
            issue_html,
            JOURNAL_INFO["JOURNAL_ID"],
            "TITLE",
        )
        if issue_heads is None:
            # globals.title_is_none.append(f"None Title: {JOURNAL_INFO['JOURNAL_ID']}")
            return None

        issue_dates = content_scraper.scrape_content(
            JOURNAL_INFO["DATE_DATA"],
            issue_html,
            JOURNAL_INFO["JOURNAL_ID"],
            "DATE",
        )
        if issue_dates is None:
            # globals.date_is_none.append(f"None Date: {JOURNAL_INFO['JOURNAL_ID']}")
            return None

        landing_page_link = content_scraper.scrape_content(
            JOURNAL_INFO["LINK_DATA"], issue_html, JOURNAL_INFO["JOURNAL_ID"], "LINK"
        )
        if landing_page_link is None:
            # globals.link_is_none.append(f"None Link: {JOURNAL_INFO['JOURNAL_ID']}")
            return None

        # handles case if the number of elements selected aren't the same
        if not len(issue_heads) == len(issue_dates) == len(landing_page_link):  # type: ignore
            logging.error("SKIP GATHER: Number of article elements need to be the same")
            logging_string = f"Titles: {len(issue_heads)} Dates: {len(issue_dates)} Links: {len(landing_page_link)}"  # type: ignore
            logging.error(logging_string)
            globals.unequal_titles_dates_links_counts.append(
                f"{JOURNAL_INFO['JOURNAL_ID']}: {logging_string}"
            )
            return None

        # keeps track of the amount of invalid dates a website has
        invalid_counter = 0

        # parsing each title, date, and link at once
        for title, date, link in zip(issue_heads, issue_dates, landing_page_link):

            if invalid_counter > 3:
                break

            if link.get("href") is None:
                link = link.find("a")

            try:
                issue_link = JOURNAL_INFO["URL_PRE"] + link.get("href").strip()
            except TypeError:
                logging.error(
                    f"SKIP: landing_page_link.get('href') is giving a 'None' value: {JOURNAL_INFO['JOURNAL_ID']}"
                )
                return None

            title = format_element.format_title(
                title,
                JOURNAL_INFO["HEADLINE_FORMATTING_DATA"],
                JOURNAL_INFO["JOURNAL_ID"],
            )

            # extracting and formatting date, returns INVALID if date is not recent
            if issue_dates is not None:
                date = date_handler(JOURNAL_INFO["DATE_FORMATTING_DATA"], JOURNAL_INFO["FULL_URL"], date.text)
                if date is None:
                    continue
                elif date == "INVALID":
                    invalid_counter += 1
                    continue

            issue_webpage_html = ""

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

            # inserting data into dict before doing description
            journal_contents["title"] = unidecode(title)
            journal_contents["date"] = date
            journal_contents["a_id"] = JOURNAL_INFO["JOURNAL_ID"]
            journal_contents["url"] = issue_link

            # returns true when duplicate is found
            if storage.skip_duplicates(db_data, journal_contents):
                return None

            journal_data = gather_journal_data(JOURNAL_INFO, issue_webpage_html)
            if journal_data is not None:
                journal_data = format_element.issue_formatter(journal_data, JOURNAL_INFO)

            journal_contents["jdata"] = journal_data
            # checking to see if nothing was scraped for any elements
            for key in journal_contents:
                if journal_contents[key] is None:
                    return None

            logging.debug(f"Titles: {journal_contents['head']}")
            logging.debug(f"Dates: {journal_contents['date']}")
            #logging.debug(f"Desc: {journal_contents['jdata']}")
            logging.debug(f"Journal_id {journal_contents['a_id']}")
            logging.debug(f"Article Link: {journal_contents['url']}")

            # inserting data into the db
            storage.db_insert(db_data, journal_contents, allowGPT)

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
