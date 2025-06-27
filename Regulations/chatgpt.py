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

    prompt = (f"""
Write a 300-word news article summarizing a public comment letter submitted to a federal agency. Follow these instructions:
Headline
- Craft a headline in Title Case, without a period.
- The headline should succinctly summarize the essence of the letter.

Article Structure
- Begin the first paragraph with: ‘WASHINGTON, {today_str} --’
- Write 4-5 standalone paragraphs.
- Use at least one quote attributed directly to the organization that submitted the letter.
- In the first mention, refer to the correspondence as a ‘public comment letter.’
- Use the author’s first and last name, with title, only the first time they appear; for subsequent references, use a suitable synonym or acronym as appropriate.
- If referring to a department, use “U.S.” (e.g., U.S. Department of Agriculture).

Attribution and Eligibility
- Only process letters that specify an organization. If there is no organization, do not proceed.
- If the letter does not mention a federal agency, reply only with “REJECTED”.

Style & Restrictions
- Do not use: Mr., Ms., Hon., Dr., new, recently, honorable, significant, forthcoming, extensive, formal, formally, detailed, thereof.
- If referencing a place, write “D.C.” instead of “District of Columbia.”

Additional Guidance
- The letter author typically appears after the letter text, including their name and title.
- Make the summary engaging, clear, and informative, focusing on the content and implications as presented.
"""
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
