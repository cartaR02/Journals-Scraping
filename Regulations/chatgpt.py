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
    prompt = (
 # waiting on prompt
        f"""Create a 400-word news story, with a news headline on a separate line without a period above the opening of the text, from this text of a letter to a named federal agency. Use the name of that agency in the first paragraph in full only; and subsequently use a synonym or acronym. Create stand-alone paragraphs where there are direct quotes attributed to a named letter writer. Use the persons first and last name only in the first instance.
          All docs should start with a headline a line break and then the body paragraphs.  The first body paragraph starts with "WASHINGTON, {today_str} --"
          Headline should be based on the text and in title case
          DO not under any circumstances return an answer without beginning with a title and then the body paragraphs without the rules stated above.
        If the agency is a department, use U.S. in front of it instead of United States spelled out.
If there are mutiple signers for the letter, create a paragraph that lists all of them.
If using a person's title after their name, the letters are lowercase.
If using District of Columbia, always refer to it as D.C.
In text, do not include these words: Mr., Ms., Hon., Dr., new, recently, honorable, significant, forthcoming, extensive, formal, formally, detailed, thereof.
The last paragraph should only say when the letter was sent to the government agency and the named individuals who are recipients of the letter, if available. Do not repeat the name or organization of the signer in full as it was used above."""
    )
    try:
        response = openai_client.chat.completions.create( model="gpt-4o-mini", messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": PDF_Text}])
        msg = cleanup_text.cleanup_text(response.choices[0].message.content)
        split_body = msg.split("\n", 1)
        headline = split_body[0]
        msg = split_body[1] + "\n\n***\n\nView Original Submission: " + comments_link
        ## TODO ADD DOCKET END OF TEXT

        database_saving.insert_into_db(headline, msg, PDF_Text, filename)
    except Exception as e:
        logging.error(f"Error: {e}")
