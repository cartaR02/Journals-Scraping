from datetime import datetime, date
from openai import OpenAI
from saving_data import database_saving
import logging
import cleanup_text

OPEN_API_KEY = ""

with open ("../key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)

def ask_chat_gpt(PDF_Text, current_id, comments_link, filename, title):
    today_str = datetime.today().strftime("%B, %-d")

    prompt = (f"""Prompt for Generating a News Story from a Letter

Objective: Generate a 400-word news story based on the provided text of a letter to a U.S. federal agency. Adhere strictly to the following formatting and content rules.
Input: Text from a letter addressed to a federal agency.
Formatting and Content Instructions:

Headline:
Create a headline in Title Case that summarizes the core issue of the letter.
The headline must be on its own line.
Do not place a period or any other punctuation at the end of the headline.

Article Structure:
Place a single line break between the headline and the first paragraph of the story.
The first paragraph must begin with the following text exactly: WASHINGTON, {today_str} --
The total word count should be up to 400 words.

Agency and Organization Names:
In the first paragraph, focus on the company or entity that issued the public comment letter to the federal agency, which should also be named. Use the full name of the federal agency that received the letter. If the agency is a department, prefix it with "U.S." instead of spelling out "United States" (e.g., "U.S. Department of Justice").
In first reference, use public comment letter
In all subsequent paragraphs, refer to that agency using only an appropriate acronym or a synonym (e.g., "the agency," "the commission").
In all instances, use only straight quotes, not curly or slanted quotes.

Quoted Material:
Avoid using direct quotes in quotation marks from the letter, but attribute material to the organization/entity sending the letter.
Avoid using the names of people.

Style and Word Choice:
Always refer to the District of Columbia as "D.C."
Do not use any of the following words in the story: Mr., Ms., Hon., Dr., new, recently, honorable, significant, forthcoming, extensive, formal, formally, detailed, thereof.
Execute these instructions without relying on any text OUTSIDE of this document.
Follow all previous directions exactly with no deviation""")
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

        current_box = 'D'
        # even if these are blanks just put in comments field but if not empty then adjust signer phrase sentence
        post_signer_txt, signer_phrase = cleanup_text.check_for_signers(PDF_Text)

        signer_phrase_comment = ''
        if post_signer_txt is not None:
            signer_phrase_comment = f"Signer phrase found: {signer_phrase}\nPost Signer Text:\n\n{post_signer_txt}"
            current_box = 'W'

        if "coalition" in body:
            current_box = 'W'

        # combine the things to go into original text: PFD_Text and prompt
        original = PDF_Text[:62000] + "\n\n *** Prompt Below *** \n\n" + prompt
        database_saving.insert_into_db(headline, body, original, filename, title, comments_link, signer_phrase_comment, current_box)
    except Exception as e:
        logging.error(f"Error: {e}")
