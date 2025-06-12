import datetime
import os
import global_info
import yaml
import mysql.connector
import logging


def create_filename(id):
    return "$H-PUBCOM-" + id

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


def check_if_exists(filename):
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
            global_info.duplicate_files.append(filename)
            connection.close()
            return True
        else:
            logging.info("No Duplicate Found")
        connection.close()
        return False
    except Exception as e:
        logging.error(f"Error while checking filename: {e}")

def insert_into_db(headline, body, original_txt, filename):
    connection = get_db_connection()
    cursor = connection.cursor()
    source_id = 98

    insert_sql = """ INSERT INTO story (filename, uname, source, by_line, headline, story_txt, editor,invoice_tag, date_sent, sent_to, wire_to, nexis_sent, factiva_sent, status, content_date, last_action, orig_txt) VALUES (%s, %s, %s, %s, %s, %s, '', '', NOW(), '', '', NULL, NULL, %s, %s, SYSDATE(), %s) """

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute(insert_sql, (filename, "C-PUBCOM", source_id, "Carter Struck", headline, body, 'D', today_str, original_txt))
        global_info.docs_added.append(filename)
        connection.commit()
        connection.close()
    except mysql.connector.Error as error:

        logging.error(f"Failed to insert into database duplicate: {error}")
