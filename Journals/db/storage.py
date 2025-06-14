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
def db_insert(
    db_data: dict,
    article_contents: dict,
):
    # id and title is enough to describe what we need
    logging_str: str = f"{article_contents['a_id']}: {article_contents['title']}"
    globals_logging_str_link: str = (
        f"{article_contents['a_id']}: {article_contents['url']}"
    )
    description = article_contents["desc"]
    headline = article_contents["title"]

    lede: str | None = get_lede(article_contents, db_data["ledes"])
    if lede is None:
        return

    lede = format_lede(lede, article_contents)

    # checking if the description didn't load properly
    if description is None or len(description) == 0:
        logging.info(f"** SKIPPING description is None: {article_contents['a_id']}")
        globals.article_description_is_none.append(logging_str)
        return

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
            f"Skipping, article length is too small: {article_contents['a_id']} body size {description_length}"
        )
        globals.article_description_too_short.append(
            f"{globals_logging_str_link} Description Length: {description_length}"
        )
        return
    
    # removing headline in description before adding it our selves
    description = description.replace(headline, "")

    article_body = f"{lede}\n\n* * *\n\n{headline}\n*\n{description}\n\n***\n\nOriginal text here: {article_contents['url']}"

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

    filename = get_filename(db_data["filenames"], article_contents)
    if filename is None:
        globals.filename_is_none.append(f"{article_contents['a_id']}")
        logging.error(f"Filename is none: [{article_contents['a_id']}]")
        return

    # opening db connection to prepare for insertion
    db_data["database"] = db_config(db_data["yml_config"])
    db_data["press_release_cursor"] = db_data["database"].cursor()

    # newlines at each end for readability
    logging.info(
        f"\nADDING: FILENAME: [{filename}] TITLE: [{article_contents['title']}] DATE: [{article_contents['date']}] ID [{article_contents['a_id']}]\n"
    )

    try:
        db_data["press_release_cursor"].execute(
            db_data["SQL_INSERT"],
            (
                article_contents["title"][:254],
                article_contents["date"],
                article_body,
                int(article_contents["a_id"]),
                "D",
                filename,
                "",
                db_data["uname"],
            ),
        )
        globals.successfully_added_doc.append(f"{logging_str}")
        db_data["database"].commit()
        db_data["database"].close()

    except mysql.connector.IntegrityError as err:
        globals.duplicate_docs.append(f"{logging_str}")
        logging.error(f"{article_contents['a_id']} dupe: {err}")
        db_data["database"].close()

    except mysql.connector.errors.DataError as err:
        globals.rejected_docs.append(logging_str)
        logging.error(f"{article_contents['a_id']} rejected: {err}")
        db_data["database"].close()
    except mysql.connector.errors.DatabaseError as err:
        logging.error(f"Insert Error {err}")
        globals.sql_insert_error.append(f"{article_contents['a_id']} Insert Error: {err}")
        db_data["database"].close()



def skip_duplicates(db_data: dict, article_contents: dict):
    """
    Take filename to be checked before heavy loading of going into site and gathering data is """


    try: 
        db_data["database"] = db_config(db_data["yml_config"])
        db_data["press_release_cursor"] = db_data["database"].cursor()

        filename = get_filename(db_data["filenames"], article_contents)

        query = "SELECT COUNT(*) FROM press_release WHERE filename = %s"
        db_data["press_release_cursor"].execute(query, (filename,))

        count = db_data["press_release_cursor"].fetchone()[0]
        logging_str: str = f"{article_contents['a_id']}: {article_contents['title']}"
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