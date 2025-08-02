from selenium.webdriver.support import expected_conditions as EC
from gather_path.gather_all_issues import gather_contents
from selenium.webdriver.support.ui import WebDriverWait
from scrapers.container_scraper import get_containers
from configs.template_csv_data import assign_csv_line
from gather_path.gather_issue import gather_content
from selenium.webdriver.common.by import By
from configs.config import program_state
from web_requests import get_website
import configs.config as config
from Email import email_output
from datetime import datetime
import db.storage as storage
from openai import OpenAI
import logging
import globals
import getopt
import csv
import yaml
import sys

import os
import shutil

# tracking times for logging purposes
start = datetime.now()
# selenium webdriver
driver = config.selenium_config()

# try calling the function again
if driver == None:
    driver = config.selenium_config()

# exit program call if driver cannot be initiated
if driver == None:
    sys.exit(2)

config.log_config()

with open("./configs/db_config.yml", "r") as yml_file:
    yml_config = yaml.load(yml_file, Loader=yaml.FullLoader)

db_data = {}

db_data["yml_config"] = yml_config

# sql database connection
db_data["database"] = config.db_config(yml_config)

agency_cursor = db_data["database"].cursor()

query: str = config.query_config(yml_config, program_state["lede_filter"])
agency_cursor.execute(query)

db_data["filenames"] = {}
db_data["ledes"] = {}
unames = {}
for f in agency_cursor:
    db_data["filenames"][str(f[0])] = f[1]
    db_data["ledes"][str(f[0])] = str(f[2])
    unames[str(f[0])] = str(f[3])

# closing connection until insertion is necessary
db_data["database"].close()

# insert statement that takes: headline, date, body text, article id, box status, filename, headline 2, uname
db_data[
    "SQL_INSERT"
] = """
INSERT INTO tns.press_release (headline,content_date,body_txt,a_id,status,create_date,last_action,filename,headline2, orig_txt) VALUES ( %s, %s, %s, %s, %s, SYSDATE(),SYSDATE(),%s, %s, %s)
"""

OPEN_API_KEY = ""

with open ("key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)

csvFileName = "WebsiteData.csv"

# Parse command line arguments
def parse_arguments():
    filter_id = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:Gm:P", ["id=", "gpt", "Production"])
        for opt, arg in opts:
            if opt in ("-i"):
                filter_id = arg
            if opt in ("-G"):
                program_state["chatGPT"] = True
            if opt == "-m":
                program_state["amount_of_months"] = arg
            if opt == "-P":
                program_state["production_run"] = True

    except getopt.GetoptError:
        print("Usage: python Journals.py -i <id> [-G]")
        print("  -i <id>: Filter by journal ID")
        print("  -G: Enable GPT processing")
        print("  -m <amount_of_months>: Amount of months to gather data for")
        print("  -P: Production run")
        sys.exit(2)
    return filter_id


def clear_folders():
    logging.info("Clearing Folders")
    if os.path.exists("./journal_output"):
        shutil.rmtree("./journal_output/")
    os.mkdir("./journal_output")

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


# Get the filter ID from command line arguments and set allowGPT if -G is provided
filter_id = parse_arguments()
clear_folders()
logging.info(
    f"Filter ID: {filter_id if filter_id else 'None - processing all journals'}"
)
if program_state["chatGPT"]:
    gpt_enabled_str = "Enabled"
else:
    gpt_enabled_str = "Disabled"
logging.info(f"GPT Processing: {gpt_enabled_str}")

with open(csvFileName, "r", newline="", encoding="utf-8") as journal_data:
    journal_reader = csv.reader(journal_data)
    counter = 0
    # Skip the title row
    next(journal_reader)
    for journal_row in journal_reader:
        #     # Skip this row if filter_id is specified and doesn't match the current journal ID
        if filter_id and journal_row[0] != filter_id:
            continue

        # THINGS that will be unique to the line
        # id, name and url, if things need to be permanently unique to a line they are added here before default
        # ... csv is added
        JOURNAL_INFO = {
            "JOURNAL_ID": journal_row[0],
            "JOURNAL_NAME": journal_row[1],
            "URL_FIELD": journal_row[2],
        }

        url_field_split = JOURNAL_INFO["URL_FIELD"].split("|")
        JOURNAL_INFO["FULL_URL"] = url_field_split[0]
        JOURNAL_INFO["URL_PRE"] = "" if len(url_field_split) < 2 else url_field_split[1]

        assign_row = assign_csv_line(JOURNAL_INFO['URL_FIELD'])
        if assign_row != None:
            journal_row = assign_row

        globals.url_count += 1
        JOURNAL_INFO.update(
            {
                "JOURNAL_CONTAINERS": journal_row[3],
                "LANDING_PAGE_GATHERING": journal_row[4],
                "LINK_DATA": journal_row[5],
                "HEADLINE_DATA": journal_row[6],
                "HEADLINE_FORMATTING_DATA": journal_row[7],
                "DATE_DATA": journal_row[8],
                "DATE_FORMATTING_DATA": journal_row[9],
                "JOURNAL_INFO_DATA": journal_row[10],
                "JOURNAL_INFO_FORMATTING": journal_row[11],
                "LOAD_TIME": journal_row[12],
                "BYPASS": journal_row[13],
                "STATUS": journal_row[14],
            }
        )
        logging.info(JOURNAL_INFO["STATUS"])

        # handling url data
        JOURNAL_INFO["LANDING_PAGE_GATHERING"] = (
            True if JOURNAL_INFO["LANDING_PAGE_GATHERING"] == "True" else False
        )

        # if find_all is in one of the fields, we need to use a different path
        single_gather = (
            True if "find_all" in JOURNAL_INFO["JOURNAL_CONTAINERS"] else False
        )

        # getting landing page html
        webpage_html = get_website(JOURNAL_INFO["FULL_URL"], driver, JOURNAL_INFO)
        if webpage_html is None:
            logging.error(f"html is None")
            globals.landing_page_html_is_none.append(f"{JOURNAL_INFO['JOURNAL_ID']}: {JOURNAL_INFO['FULL_URL']}")
            continue

        # parsing through article containers
        issue_container_html = get_containers(
            JOURNAL_INFO["JOURNAL_CONTAINERS"], webpage_html
        )
        if issue_container_html is None or len(issue_container_html) == 0:
            logging.error("landing page getting containers html is none")
            globals.landing_page_containers_html_is_none.append(f"{JOURNAL_INFO['JOURNAL_ID']}: {JOURNAL_INFO['FULL_URL']}")
            continue

        # journal data will exculsively be stored in this dict
        journal_contents = {}
        # not actually used for some reason it wasnt working
        journal_contents["gpt"] = openai_client

        if single_gather:

            invalid_counter = 0

            for issue_html in issue_container_html:

                if invalid_counter > 3:
                    break

                journal_contents = gather_content(JOURNAL_INFO, issue_html, driver)
                if journal_contents is None:
                    continue

                # incrementing the invalid counter when date isn't recent
                if journal_contents == "INVALID":
                    invalid_counter += 1
                    continue

                storage.db_insert(db_data, journal_contents, program_state["chatGPT"], openai_client, JOURNAL_INFO['JOURNAL_NAME'])

        else:
            journal_contents = gather_contents(
                JOURNAL_INFO, issue_container_html, driver, db_data, program_state["chatGPT"]
            )

end_time = datetime.now()
total_time = end_time - start
email_output(program_state["chatGPT"],program_state["amount_of_months"], start, end_time, total_time, program_state["production_run"] )
driver.quit()
