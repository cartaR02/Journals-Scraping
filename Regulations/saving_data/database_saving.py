import datetime

import yaml
import mysql.connector
import logging


def create_filename(id):
    return "$H-PUBCOM-" + id

def get_db_connection():
    with open("./db_config.yml", "r") as yml_file:
        db_config = yaml.load(yml_file, Loader=yaml.FullLoader)
    return mysql.connector.connect(
        host=db_config["dbhost"],
        port=db_config["dbport"],
        user=db_config["dbuser"],
        passwd=db_config["dbpasswd"],
    )


def check_if_exists(filename):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM story WHERE filename = %s", (filename,))
    if cursor.fetchone()[0] > 0:
        logging.info("Skipping duplicate before gpt call")
        connection.close()
        return True
    return False

def insert_into_db(filename):
    connection = get_db_connection()
    cursor = connection.cursor()
    source_id = 98

    insert_sql = """ INSERT INTO story (filename, uname, source, by_line, headline, story_txt, editor, invoice_tag,date_sent, sent_to, wire_to, nexis_sent, factiva_sent, status, content_date, last_action) VALUES (%s, %s, %s, %s, %s, %s, ",",NOW(), ",", NULL, NULL, %s, %s, SYSDATE()) """

    today_str = datetime.now.strftime("%Y-%m-%d")
    cursor.exectue(insert_sql, (filename, "C-PUBCOM", source_id, "Carter Struck", headline, body, 'D', today_str))