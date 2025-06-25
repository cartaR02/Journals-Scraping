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
