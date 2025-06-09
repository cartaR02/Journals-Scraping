from datetime import datetime, date
from openai import OpenAI
from saving_data import database_saving
import logging

OPEN_API_KEY = ""

with open ("../key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)

def ask_chat_gpt(PDF_Text, current_id, comments_link, filename):
    today_str = datetime.today().strftime("%B, %-d")
    prompt = (
 # waiting on prompt
        f"""Create a 400-word news story, with a news headline, from this text of a letter to a named federal agency that is used in the first paragraph. Create stand-alone paragraphs where there are direct quotes attributed to a named letter writer. At the begining of the letter start with the text like this exactly how I type it: WASHINGTON, {today_str} --\n
If the agency is a department, use U.S. in front of it instead of United States spelled out.
Do not use a dateline and avoid unnecessary acronyms.
The last paragraph should say when the letter was sent to the government agency and if available the named individuals who are recipients of the letter.
If any entities in the doc are from a government agency or a college, do not add additional geography of where it is located. If it is any other type of entity, include the geography of where it is located using a comma and then the city, state where it is located.
All letters have to have one or more signers, and all signers and their affiliations and job titles, if available, should be mentioned in text somehow...
If using District of Columbia, always refer to it as D.C.
In text, do not include these words: honorable, significant, forthcoming, extensive, formal, formally, detailed.
For 2nd references to entities, use synonyms.
If using a person's title after their name, the letters are lowercase.
Second references to people should be last name.
If there are mutiple signers for the letter, create a paragraph that lists all of them."""
    )
    try:
        response = openai_client.chat.completions.create( model="gpt-4o-mini", messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": PDF_Text}])
        msg = response.choices[0].message.content
        msg = msg + "\n\n-----------------------------------\n\nView Original Submission: " + comments_link
        headline = 'THis IS a test'
        ## TODO ADD DOCKET END OF TEXT

        database_saving.insert_into_db(headline, msg, PDF_Text, filename)
    except Exception as e:
        logging.error(f"Error: {e}")
