from datetime import datetime, date
from openai import OpenAI
from saving_data import database_saving
import logging
import cleanup_text

OPEN_API_KEY = ""

with open ("../key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)

def ask_chat_gpt(PDF_Text, current_id, comments_link, filename):
    today_str = datetime.today().strftime("%B, %-d")

    prompt = (f""" Goal: Create a 400-word news story based on a public comment letter to a federal agency.

Output Format:

Headline: Title case, no period, on a separate line above the opening text.

First Paragraph Start: "WASHINGTON, {today_str} --"

Paragraphs: Stand-alone paragraphs for direct quotes attributed to a named letter writer.

Word Count: Approximately 400 words.

Content Requirements:

Federal Agency:

Full name in the first paragraph only.

Subsequent mentions use a synonym or acronym.

If a department, use "U.S." instead of "United States" (e.g., U.S. Department of Health and Human Services).

Named Letter Writer:

First and last name used only in the first instance.

If multiple signers, list all in a dedicated paragraph.

Titles after names should be lowercase (e.g., John Smith, chief executive officer).

Place: Refer to "District of Columbia" as "D.C."

Forbidden Words (do not use): Mr., Ms., Hon., Dr., new, recently, honorable, significant, forthcoming, extensive, formal, formally, detailed, thereof.

Term Usage: Refer to the 'letter' as a 'public comment letter.'"""
    )
    try:
        response = openai_client.chat.completions.create( model="gpt-4o-mini", messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": PDF_Text}])
        msg = response.choices[0].message.content
        # setting up body
        cleaned = cleanup_text.cleanup_text(msg)
        split_body = cleaned.split("\n", 1)
        headline = split_body[0]
        body = split_body[1].lstrip() + "\n\n***\n\nRead full text of letter here: " + comments_link

        database_saving.insert_into_db(headline, body, prompt, filename)
    except Exception as e:
        logging.error(f"Error: {e}")
