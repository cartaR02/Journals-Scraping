from helpers.lede_formatting import format_lede
from configs.config import db_config
from helpers.format_element import replace_defaults
from helpers.helpers import get_lede, get_filename
import globals
import mysql.connector
from unidecode import unidecode
import logging
import re


# db_insert inserts gathered data into the tns db
# @typechecked
def db_insert(db_data, journal_contents, allowGPT):
    # id and head is enough to describe what we need
    logging_str = f"{journal_contents['a_id']}: {journal_contents['head']}"
    globals_logging_str_link = f"{journal_contents['a_id']}: {journal_contents['url']}"
    description = journal_contents["jdata"]
    headline = journal_contents["head"]

    # don't think we need ledes
    # lede = get_lede(journal_contents, db_data["ledes"])
    # if lede is None:
    #     return

    # lede = format_lede(lede, journal_contents)

    # checking if the description didn't load properly
    if description is None or len(description) == 0:
        logging.info(f"** SKIPPING description is None: {journal_contents['a_id']}")
        globals.article_description_is_none.append(logging_str)
        return

    if allowGPT:
        description = ask_chat_gpt(
            journal_contents["head"], description, journal_contents["gpt"]
        )

    description = unidecode(description)

    description = replace_defaults(description)

    for word in globals.keyword_skips:
        if word in description:
            logging.error(f"Skipping, found keyword {word} in description")
            globals.article_skipped_keyword_found.append(
                f"{globals_logging_str_link} Word: {word}"
            )
            return

    description_length = len(description)
    if description_length <= globals.char_limit_to_skip:
        logging.error(
            f"Skipping, article length is too small: {journal_contents['a_id']} body size {description_length}"
        )
        globals.article_description_too_short.append(
            f"{globals_logging_str_link} Description Length: {description_length}"
        )
        return

    # removing headline in description before adding it our selves
    description = description.replace(headline, "")

    article_body = f"\n{headline}\n*\n{description}\n\n***\n\nOriginal text here: {journal_contents['url']}"

    article_body = re.sub(r"\n\s*\n", "\n\n", article_body)
    article_body = re.sub(r"(\r\n|\r|\n)+", "\n\n", article_body)

    # make sure just one space after period
    article_body = re.sub(r"\.[^\S\n]+", ". ", article_body)

    # getting rid of leading whitespace from puncuation
    article_body = re.sub(r"\s*\.", ".", article_body)
    article_body = re.sub(r"\s*,", ",", article_body)

    # handles the case where htmltotext module double spaces around link
    article_body = re.sub(r"  ", " ", article_body)

    # make sure just one space after period even with quote
    article_body = re.sub(r'\."[^\S\n]+', '." ', article_body)

    filename = get_filename(db_data["filenames"], journal_contents)
    if filename is None:
        globals.filename_is_none.append(f"{journal_contents['a_id']}")
        logging.error(f"Filename is none: [{journal_contents['a_id']}]")
        return

    # opening db connection to prepare for insertion
    db_data["database"] = db_config(db_data["yml_config"])
    db_data["press_release_cursor"] = db_data["database"].cursor()

    # newlines at each end for readability
    logging.info(
        f"\nADDING: FILENAME: [{filename}] head: [{journal_contents['head']}] DATE: [{journal_contents['date']}] ID [{journal_contents['a_id']}]\n"
    )

    try:
        db_data["press_release_cursor"].execute(
            db_data["SQL_INSERT"],
            (
                journal_contents["head"][:254],
                journal_contents["date"],
                article_body,
                int(journal_contents["a_id"]),
                "D",
                filename,
                "",
            ),
        )
        globals.successfully_added_doc.append(f"{logging_str}")
        db_data["database"].commit()
        db_data["database"].close()

    except mysql.connector.IntegrityError as err:
        globals.duplicate_docs.append(f"{logging_str}")
        logging.error(f"{journal_contents['a_id']} dupe: {err}")
        db_data["database"].close()

    except mysql.connector.errors.DataError as err:
        globals.rejected_docs.append(logging_str)
        logging.error(f"{journal_contents['a_id']} rejected: {err}")
        db_data["database"].close()
    except mysql.connector.errors.DatabaseError as err:
        logging.error(f"Insert Error {err}")
        globals.sql_insert_error.append(
            f"{journal_contents['a_id']} Insert Error: {err}"
        )
        db_data["database"].close()


def skip_duplicates(db_data: dict, journal_contents: dict):
    """
    Take filename to be checked before heavy loading of going into site and gathering data is
    """

    try:
        db_data["database"] = db_config(db_data["yml_config"])
        db_data["press_release_cursor"] = db_data["database"].cursor()

        filename = get_filename(db_data["filenames"], journal_contents)

        query = "SELECT COUNT(*) FROM press_release WHERE filename = %s"
        db_data["press_release_cursor"].execute(query, (filename,))

        count = db_data["press_release_cursor"].fetchone()[0]
        logging_str = f"{journal_contents['a_id']}: {journal_contents['head']}"
        if count > 0:
            logging.info(f"Duplicate found before insertion '{filename}'. Skipping:: ")
            globals.duplicate_docs.append(f"Pre-check: {logging_str}")
            return True
        else:
            return False

    except mysql.connector.Error as err:
        logging.error(f"Database error while checking for duplicates: {err}")
        # Return True to be safe, preventing potential duplicate entries on error
        return True

    finally:
        if db_data["database"] and db_data["database"].is_connected:
            db_data["press_release_cursor"].close()
            db_data["database"].close()


def ask_chat_gpt(journal_headline, Site_html, openai_client):
    prompt = (
        f"Create a 500-word news story, with a headline, for this text focused on\n"
        "Using two key research project, but mentioning others below it."
        "Including the date and title of the journal."
        "Make sure the date is not in the future"
        "Use the journal headline for some context " + journal_headline
    )
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": Site_html[:8000]},
            ],
        )
        msg = response.choices[0].message.content
        return msg
    except Exception as e:
        logging.error(f"Error: {e}")
