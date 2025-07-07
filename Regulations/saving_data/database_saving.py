import datetime
import os
import global_info
import yaml
import mysql.connector
import logging


def create_filename(id, pdf_title):
    begining_id = id.split('-')[0]
    return "$H-PUBCOM-" + begining_id + pdf_title[:85]

def get_db_connection():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Join it with the filename to get the full path
    config_path = os.path.join(current_dir, "db_config.yml")

    with open(config_path, "r") as yml_file:
        db_config = yaml.load(yml_file, Loader=yaml.FullLoader)
    return mysql.connector.connect(
        host=db_config["dbhost"],
        port=db_config["dbport"],
        user=db_config["dbuser"],
        passwd=db_config["dbpasswd"],
        database="tns",
    )


def check_if_exists(filename, link):
    logging.info("Checking filename")

    try:
        connection = get_db_connection()
        logging.info("Connected to db")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM story WHERE filename = %s", (filename,))
        logging.info("Executed sql")
        found_filename = cursor.fetchone()
        if found_filename:
            logging.info("Skipping duplicate before gpt call")
            global_info.duplicate_files.append(filename + " " + link)
            connection.close()
            return True
        else:
            logging.info("No Duplicate Found")
        connection.close()
        return False
    except Exception as e:
        global_info.duplication_checking_error.append(f"{filename}: {link}")
        logging.error(f"Error while checking filename: {e}")

def insert_into_db(headline, body, original_prompt, filename, original_title, link):
    connection = get_db_connection()
    cursor = connection.cursor()
    source_id = 98
    insert_sql = """ INSERT INTO story (filename, uname, source, by_line, headline, story_txt, editor,invoice_tag, date_sent, sent_to, wire_to, nexis_sent, factiva_sent, status, content_date, last_action, orig_txt) VALUES (%s, %s, %s, %s, %s, %s, '', '', NOW(), '', '', NULL, NULL, %s, %s, SYSDATE(), %s) """
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute(insert_sql, (filename, "C-PUBCOM", source_id, "Carter Struck", headline, body, 'D', today_str, original_prompt))
        # used for email checking when the id is not useful to quickly look through
        global_info.docs_added.append(original_title)
        connection.commit()
        connection.close()
    except mysql.connector.Error as error:
        global_info.database_insertion_error.append(link)
        logging.error(f"Failed to insert into database duplicate: {error}")
