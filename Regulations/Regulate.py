import csv
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
import logging
import time
import requests
import pdfplumber
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import sys
import getopt

# At the beginning of your script, before setting up your own logging:
import logging
print("Running from: ", sys.executable)
# Disable Selenium's debug logging
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)

OPEN_API_KEY = ""

with open ("../key", "r") as f:
    OPEN_API_KEY = f.read().strip()

openai_client = OpenAI(api_key=OPEN_API_KEY)
allowGPT = True
def parse_arguments():
    global allowGPT
    filter_id = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "G", ["gpt"])
        for opt, arg in opts:
            print(opt)
            if opt == ("-G"):
                allowGPT = True
                logging.info("GPT Processing: Enabled")
    except getopt.GetoptError:
        print('Usage: python Regulate.py -G')
        print('  -G: Enable GPT processing')
        sys.exit(2)
    return filter_id
# Then your existing logging setup
logfile = "./logs/scrape_log.{}.log".format(
    datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
)
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    filename=logfile,
                    filemode="w")

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

def selenium_config() -> webdriver:
    options: Options = Options()
    # Uncomment the next line for headless testing
    # options.add_argument("--headless")
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 1)
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options)  # type: ignore
    return driver

driver = selenium_config()

def ask_chat_gpt(PDF_Text, current_id):
    prompt = (
 # waiting on prompt
        """Create a 400-word news story, with a news headline, from this text of a letter to a named federal agency that is used in the first paragraph. Create stand-alone paragraphs where there are direct quotes attributed to a named letter writer.
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
        save_pdf_to_text("./ai_response/" + current_id, msg)
    except Exception as e:
        logging.error(f"Error: {e}")



def retrieve_site_html(URL):
    try:
        driver.get(URL)

        # Add a small delay to let the cookie popup appear
        time.sleep(2)

    except Exception as e:
        logging.error(f"{URL} Failed to access: {e}")
        return None

    
    return driver.page_source

def click_filter(filter_text: str) -> bool:
    """Clicks a filter link (like 'Last 7 Days') if it exists on the page."""
    try:
        logging.info(f"Attempting to click filter: {filter_text}")
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//a[contains(text(), "{filter_text}")]'))
        )
        element.click()
        time.sleep(3)  # Allow any content refresh after click
        return True
    except Exception as e:
        logging.warning(f"Could not click filter '{filter_text}': {e}")
        return False

def type_search_query(query: str) -> bool:
    """Types a search query into the typeahead input."""
    try:
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"][placeholder="Search"]'))
        )
        input_field.clear()
        input_field.send_keys(query)
        input_field.send_keys(Keys.RETURN)  # Optional: press Enter
        time.sleep(3)  # Let search results load
        return True
    except Exception as e:
        logging.error(f"Failed to type into search input: {e}")
        return False

def save_pdf_to_text(pdf_path, pdf_text):

    pdf_path = f"{pdf_path}.txt"

    with open(pdf_path, "w") as f:
        f.write(pdf_text)

    logging.info(f"Saved PDF to {pdf_path}")



def click_search_button() -> bool:
    """Clicks the search button (with class 'btn btn-primary-alt')."""
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn.btn-primary-alt[type="submit"]'))
        )
        button.click()
        time.sleep(3)
        return True
    except Exception as e:
        logging.error(f"Failed to click search button: {e}")
        return False




# Main start
if __name__ == "__main__":
    url = "https://www.regulations.gov/search/comment?filter=Attach&sortBy=postedDate&sortDirection=desc"

    html = retrieve_site_html(url)

    if not html:
        logging.info("Site did not search properly")
        sys.exit()
    

    logging.info("Initial Page loaded")

    soup_html = BeautifulSoup(html, "html.parser")
    time.sleep(2)
    
    container = soup_html.find(class_="results-container")
    # here is the wrapper container of the things we need
    attachments_list = container.find_all(class_="card card-type-comment ember-view")
    
    logging.info("Attatchment docs found")
    logging.info("Truncating List")
    logging.info(len(attachments_list))
    attachments_list = attachments_list[:5]
    logging.info(len(attachments_list))

    for article in attachments_list:

        current_link = article.find("a")

        if not current_link:
            logging.error("Link not found")
            continue

        current_link = "https://www.regulations.gov" + current_link.get("href")
        logging.info(f"Link: {current_link}")
        ids_container = article.find(class_="card-metadata")
        current_id = ""

        for li in ids_container.find_all("li"):
            if li.strong and li.strong.text.strip() == "ID":
                logging.info("ID found")
                current_id = li.get_text().replace("ID", "").strip()
                logging.info(f"ID: {current_id}")
                break

        if current_id == "":
            logging.error("ID not found")
            continue

        logging.info("Article Complete!")
        # this state is id is good and link

        comment_html = retrieve_site_html(current_link)
        
        if not comment_html:
            logging.error("Comment Page did not load")
            continue

        parse_comment = BeautifulSoup(comment_html, "html.parser")

        pdf_download = parse_comment.find(class_="btn btn-default btn-block")
        try:
            pdf_download_link = pdf_download.get("href")
        except:
            for pdf in parse_comment.find_all("a"):
                if pdf.get("href").endswith(".pdf"):
                    pdf_download_link = pdf.get("href")

            if pdf_download_link == "":
                logging.error("PDF not found")
                continue
        logging.info(f"pdf download link: {pdf_download_link}")


        try:
            response = requests.get(pdf_download_link)
            response.raise_for_status()

            pdf_path = f"./pdf_downloads/{current_id}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            logging.info(f"Saved pdf to {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                PDF_TEXT = ""
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        PDF_TEXT += text + "\n"
                    else:
                        logging.info("No text found on page")

                logging.info("---------FINISHED PDF PAGE ---\n")
                logging.info(f"PDF TEXT: {len(PDF_TEXT)}")

                if len(PDF_TEXT) < 100:
                    logging.error("PDF TEXT is too short")
                    continue

                if allowGPT:
                    logging.info("GPT proccessing")
                    ask_chat_gpt(PDF_TEXT, current_id)
                else:
                    logging.info("GPT disabled")
                    logging.info("Skipping GPT")
                save_pdf_to_text("./pdf_text/" + current_id, PDF_TEXT)

        except Exception as e:
            logging.error(f"Failed to process PDF for {current_link}::: {e}")
            continue
driver.quit()