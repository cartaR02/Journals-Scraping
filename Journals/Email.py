import smtplib
import ssl
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from validate_email import validate_email
import logging

import globals



def my_mail(from_addr, to_addr, subject, msg_txt, html_msg="", cc_addr=""):
    smtp_server = "mail2.targetednews.com"
    port = 587  # For starttls
    sender_email = "kmeek@targetednews.com"
    password = "jsfL6Hqa"

    to_array = re.split("[,;]", to_addr.replace(" ", ""))
    for e in to_array:
        is_valid = validate_email(e)
        if not is_valid:
            return "Invalid Email" + str(e)

    to_string = ", ".join(to_array)

    cc_array = re.split("[,;]", cc_addr.replace(" ", ""))
    for e in cc_array:
        is_valid = validate_email(e)
        if not is_valid:
            return "Invalid Email" + str(e)

    cc_string = ", ".join(cc_array)

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        # server.ehlo() # Can be omitted
        server.starttls(context=context)  # Secure the connection
        # server.ehlo() # Can be omitted
        server.login(sender_email, password)
        # TODO: Send email here

        msg = MIMEMultipart("alternative")
        msg["From"] = from_addr
        msg["To"] = to_string
        if len(cc_string.strip()) > 0:
            msg["Cc"] = cc_string
            to_array = to_array + cc_array

        msg["Subject"] = subject
        msg.attach(MIMEText(msg_txt, "plain"))

        if len(html_msg.strip()) > 0:
            msg.attach(MIMEText(html_msg, "html"))

        text = msg.as_string()
        # server.set_debuglevel(1)
        server.sendmail(from_addr, to_array, text)
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()


# does not check for production run that gets checked before even calling this function
def email_output(gpt, months_back, start_time, end_time, total_time, production):
    summary_msg = f"""
Load Version 1.0.0 06/16/2025
    Docs Loaded {len(globals.successfully_added_doc)}
    URLS processed: {globals.url_count}
    Duplicates Skipped {len(globals.duplicate_docs)}
    No Ledes found: {len(globals.no_lead_found)}

Passed Parameters:
    ChatGPT Enabled: {gpt}
    Number of months back: {months_back}
    Start Time: {start_time}
    End Time: {end_time}
    Elapsed Time: {total_time}

Errors:"""

    for errors_list, errors_string in zip(globals.error_list_wrapper, globals.error_list_string_wrapper):
        if len(errors_list) > 0:
            summary_msg = (
                summary_msg
                + "\n\t" + errors_string + "\n\t\t"
                + "\n\t\t".join(map(str, errors_list))
            )

    summary_msg = summary_msg + "\nDocs:"

    for doc_list, doc_string in zip(globals.doc_list_wrapper, globals.doc_list_string_wrapper):
        if len(doc_list) > 0:
            summary_msg = (
                summary_msg
                + "\n\t" + doc_string + "\n\t\t"
                + "\n\t\t".join(map(str, doc_list))
            )

    logging.info(summary_msg)
    if production:
        my_mail(
            "kmeek@targetednews.com",
            "kmeek@targetednews.com",
            "Journals Scrape"
            + start_time.strftime("%Y-%m-%d %H:%M:%S"),
            summary_msg,
            "",
            "struckvail@aol.com;camhakenson@gmail.com,carterstruck02@gmail.com,marlynvitin@yahoo.com",
        )
