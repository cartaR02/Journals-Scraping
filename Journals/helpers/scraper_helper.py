from typeguard import typechecked
import logging
from datetime import datetime, timedelta
from configs.config import program_state
import datefinder
import dateparser
import bs4.element
from dateutil import parser
from dateutil.parser import ParserError
import re


# data_finder parses html based on csv arguments provided
# @typechecked
def data_finder(
    IS_ELEM: bool,
    FIND_ALL: bool,
    HTML_ATTRIBUTE: str,
    CONTAINER_NAME: str,
    slicer: slice,
    html: bs4.BeautifulSoup | bs4.element.Tag,
):

    if not IS_ELEM:
        attribute = {HTML_ATTRIBUTE: CONTAINER_NAME}
        data = (
            html.find_all(attrs=attribute)[slicer]
            if FIND_ALL
            else html.find(attrs=attribute)
        )
    else:
        data = (
            html.find_all(CONTAINER_NAME)[slicer]
            if FIND_ALL
            else html.find(CONTAINER_NAME)
        )
    if data is None or data == -1:
        return None

    return data  # type: ignore


# taking the strings from the csv and converting them to an int
# not converting to int if None is found
@typechecked
def format_slice(SLICING_DATA):
    SLICING = []
    try:
        for data in SLICING_DATA:
            if "None" in data:
                SLICING.append(None)
            else:
                SLICING.append(int(data))
    except ValueError as err:
        logging.debug(err)
        return None

    return SLICING


# date_cleaner extracting date from text if needed and checks validity
def date_handler(DATE_FORMATTING_DATA, date):

    extracted_date = ""

    date = date.lower()

    date = re.sub("\s\s*", " ", date)

    # datefinder struggles with understanding 'Sept' for September dates
    if "sept" in date and "september" not in date:
        date = date.replace("sept", "sep")

    date_form_data = DATE_FORMATTING_DATA.split("~")

    date = clean_date(date)

    for data in date_form_data:
        if data == "swap":
            try:
                extracted_date = parser.parse(date)
            except ParserError as err:
                logging.error(f"Date Parser Failed: {date} - {err}")
                return None

        # handles keyword replacing in csv field
        elif data != "":
            date = date.replace(data, "")
            extracted_date = next(datefinder.find_dates(date), None)
            if extracted_date is None:
                logging.error(f"Date Extraction failed: {date}")
                return None

        else:
            extracted_date = next(datefinder.find_dates(date), None)
            if extracted_date is None:
                logging.error(f"Date Extraction failed: {date}")
                return None

    # TODO: figure out how to interpret the months and what to return

    if extracted_date.month <= datetime.now().month - int(program_state["amount_of_months"]):
        return extracted_date.strftime("%Y-%m-%d")
    else:
        logging.info(
            f"invalid month: {extracted_date.strftime('%B')}"
        )
        return "INVALID"


def clean_date(date):
    # get rid of parenthesis
    # date = re.sub(r'^\((.*)\)$', r'\1', date)

    month_map = {
        "(jan)": "january",
        "(feb)": "february",
        "(mar)": "march",
        "(apr)": "april",
        "(may)": "may",
        "(jun)": "june",
        "(jul)": "july",
        "(aug)": "august",
        "(sep)": "september",
        "(oct)": "october",
        "(nov)": "november",
        "(dec)": "december",
    }

    for abrev, full_name in month_map.items():
        date = date.replace(abrev, full_name)

    return date

# function will take a sequence like find|class|title~find|class|artile|4
# allowign for ~ multiple times or just ones
# will permit for a big list of example above with optional indexing like above
# a 4th item in the x|x|x|x indicates indexing a list where also expects find_all call on specific find
# returns singular item
def dedicated_find_html(csv_search_line, journal_contents_html):
    # seperate the articles and filter by keywords
    # allows for multiple iterations if smaller scope is needed
    journals_to_search = csv_search_line.split("~")

    # search through list of classes for built in smaller scope and then on last item in list get find all
    # hoping that last call is not a find_all with no index except for journals list
    html = journal_contents_html
    logging.debug(f"Type of html before find_all: {type(html)}")
    # TODO PRINT THIS
    logging.debug(f"HTML: {html}")
    for finding_sequence in journals_to_search:
        contents = finding_sequence.split("|")

        # hopes for number specific indexing with find_all TODO error check
        if len(contents) == 4:
            # unwrap for cleanner naming
            finding, html_type, container_name, index = contents
            logging.info(f"Searching for {finding} in {container_name} with index {index}")
            if finding == "find_all":
                html = finding_all(html_type, container_name, html)
            html = html[int(index)]
        else:
            # no fourth option index
            finding, html_type, container_name = contents
            logging.info(f"Searching for {finding} in {container_name}")
            if finding == "find_all":
                html = finding_all(html_type, container_name, html)
            else:
                html = finding_single(html_type, container_name, html)
    if html is None:
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
def find_abstracts_containers(individual_journal, JOURNAL_INFO):
    phrase_list = ["research", "articles", "papers"]
    phrase = dedicated_find_html(JOURNAL_INFO["phrase_tag"], individual_journal)
    if phrase.text.lower() in phrase_list:
        logging.info("Phrase Found, gathering Abstract")
        # possibly get tittles but at the moment get abstract
        abstract = dedicated_find_html(JOURNAL_INFO["abstract"], individual_journal)
        logging.info("Abstract Found")
        return abstract
    logging.info("Phrase Not Found, skipping")
    return None
# TODO get proper text in abstract and allow for going into article to get actual abstract
# returns list of abstracts
# pure html so then after in a different function we will go in and gather abstracts
def create_abstract_lists(JOURNAL_INFO, journal_contents):
    # expects a state of the journal to be the smallest container of ALL the individual articles of the journal
    # it will further subdivide the inidiviual articles and gather the contents from them

    journal_list = dedicated_find_html(JOURNAL_INFO["JOURNAL_ARTICLES"], journal_contents)
    if journal_list is None:
        return None

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
def get_abstract_text(JOURNAL_INFO, abstract_lists):

    for container in abstract_lists:
        link = dedicated_find_html(JOURNAL_INFO["ABSTRACT_LINK"], container).get("href")
        if link is None:
            logging.error("Unable to get Abstract link")
            continue

        logging,info(f"Abstract Link Found: {link}")