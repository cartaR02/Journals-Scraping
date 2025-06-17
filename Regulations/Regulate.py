import csv
from datetime import datetime, date
from bs4 import BeautifulSoup, NavigableString
import logging
import time
import requests
import pdfplumber
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os
import shutil
import sys
import getopt

from Email import email_output
from date_handler import is_within_days_back
import webdriver_config
import chatgpt
import saving_data.save_txt
import saving_data.database_saving
import global_info
import cleanup_text
# At the beginning of your script, before setting up your own logging:
import logging
start_time = time.time()
print("Running from: ", sys.executable)

def clear_folders():
    logging.info("Clearing Folders")
    if os.path.exists("./pdf_downloads"):
        shutil.rmtree("./pdf_downloads/")
    if os.path.exists("./pdf_text"):
        shutil.rmtree("./pdf_text/")
    if os.path.exists("./ai_response"):
        shutil.rmtree("./ai_response/")
    os.mkdir("./pdf_downloads")
    os.mkdir("./pdf_text")
    os.mkdir("./ai_response")
# Disable Selenium's debug logging
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)
logging.getLogger("pdfminer.six").setLevel(logging.CRITICAL)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.CRITICAL)
logging.getLogger("pdfminer").setLevel(logging.CRITICAL)



allowGPT = False
production_run = False

# Global variable for number of days back (default 0)
days_back = 0
doc_limit = 0

def parse_arguments():
    global allowGPT, days_back, production_run, doc_limit
    filter_id = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "Gd:l:P", ["gpt", "days=", "limit=", "production"])
        for opt, arg in opts:
            if opt == "-G" or opt == "--gpt":
                allowGPT = True
                logging.info("GPT Processing: Enabled")
            elif opt == "-d" or opt == "--days":
                try:
                    days_back = int(arg)
                except ValueError:
                    print("Error: -d (or --days) argument requires an integer!")
                    sys.exit(2)
            elif opt == "-l":
                try:
                    doc_limit = int(arg)
                except ValueError:
                    logging.error("Error: -l argument requires an integer!")
                    sys.exit(2)
            elif opt == "-P" or opt == "--production":
                production_run = True
    except getopt.GetoptError:
        print('Usage: python Regulate.py -G [-d N] [-l N]')
        print('  -G: Enable GPT processing')
        print('  -d N: Set number of days back (default 0)')
        print('  -l N: Set document limit (default 0, no limit)')
        sys.exit(2)

    logging.info(f"GPT Enabled: {'Yes' if allowGPT else 'No'}")
    logging.info(f"Days Back: {days_back}")
    logging.info(f"Document Limit: {doc_limit if doc_limit > 0 else 'No limit'}")
    logging.info(f"Production Run: {'Yes' if production_run else 'No'}")

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

driver = webdriver_config.selenium_config()


def retrieve_site_html(URL):
    try:
        driver.get(URL)

        # Add a small delay to let the cookie popup appear
        time.sleep(2)

    except Exception as e:
        logging.error(f"{URL} Failed to access: {e}")
        return None


    return driver.page_source

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

def go_to_next_page(driver, url, timeout=10):
    """
    Goes to a given URL, then clicks the 'Next' button to go to the next page.
    Returns new page URL, or False on failure.
    """

    # stops from continuing infity
    if "pageNumber=40" in url:
        logging.info("Reached end of page")
        return False
    try:
        driver.get(url)
        logging.info("{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        logging.info(f"Navigated to {url}")
        # Wait for the page to load before searching for the button
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Go to next page"]'))
        )
        next_btn = driver.find_element(By.XPATH, '//button[@aria-label="Go to next page"]')
        next_btn.click()
        logging.info("Successfully clicked 'Next' to go to the next page.")
        time.sleep(15)
        new_url = driver.current_url
        logging.info(f"Current URL: {new_url}")
        return new_url
    except Exception as e:
        logging.error(f"Could not click 'Next' button: {e}")
        return False



def process_current_page(url):
    html = retrieve_site_html(url)
    global doc_limit


    if not html:
        logging.info("Site did not search properly")
        sys.exit()

    logging.info("Initial Page loaded")

    soup_html = BeautifulSoup(html, "html.parser")
    time.sleep(3)

    container = soup_html.find(class_="results-container")
    # here is the wrapper container of the things we need
    attachments_list = container.find_all(class_="card card-type-comment ember-view")

    truncate = False

    logging.info("Attatchment docs found")

    if truncate:
        logging.info("Truncating List")
        attachments_list = attachments_list[:5]

    logging.info(f"List length: {len(attachments_list)}")

    for article in attachments_list:
        if doc_limit != 0 and global_info.docs_looked_at >= doc_limit:
            logging.info("Reached doc limit")
            # arbitrary number just for outer loop to stop when this returned
            return 100
        global_info.docs_looked_at += 1
        logging.info(f"Starting article number {global_info.docs_looked_at} out of {doc_limit}")
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
            elif li.strong and li.strong.text.strip() == "Posted":
                logging.info("Date found")
                current_date = li.get_text().replace("Posted", "").strip()
                logging.info(f"Date: {current_date}")
                if not is_within_days_back(current_date, days_back):
                    logging.info("Date not within days back exiting program")
                    # returns none so the outer function can find that return value and exit the program
                    # fake error code that checks if its 100 above to see why the program exited
                    return 100

        if current_id == "":
            logging.error("ID not found")
            continue


        # this state is id is good and link

        comment_html = retrieve_site_html(current_link)

        if not comment_html:
            logging.error("Comment Page did not load")
            global_info.no_comment_page.append(current_id)
            continue

        parse_comment = BeautifulSoup(comment_html, "html.parser")

        pdf_download = parse_comment.find(class_="btn btn-default btn-block")
        pdf_download_link = ""
        try:
            pdf_download_link = pdf_download.get("href")
        except:
            logging.error("Link not found trying again with different method")
            for pdf in parse_comment.find_all("a"):

                if pdf.get("href").endswith(".pdf"):
                    pdf_download_link = pdf.get("href")

            if pdf_download_link == "":
                logging.error("PDF not found")
                global_info.no_pdf_found.append(current_id)
                continue
        logging.info(f"pdf download link: {pdf_download_link}")

        try:
            response = requests.get(pdf_download_link)
            response.raise_for_status()

            pdf_path = f"./pdf_downloads/Input_{current_id}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            logging.info(f"Saved pdf to {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                logging.info("Opening with PDF plumber")
                PDF_TEXT = ""
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        PDF_TEXT += text + "\n"
                    else:
                        logging.info("No text found on page")


                if len(PDF_TEXT) < 100:
                    logging.error("PDF TEXT is too short")
                    global_info.no_pdf_text.append(current_link)
                    continue

                # create file name and checking if exists
                filename = saving_data.database_saving.create_filename(current_id)
                logging.info(f"Filename: {filename}")

                if saving_data.database_saving.check_if_exists(filename):
                   continue
                cleaned_pdf = cleanup_text.cleanup_text(PDF_TEXT)
                if allowGPT:
                    logging.info("GPT proccessing")
                    chatgpt.ask_chat_gpt(cleaned_pdf, current_id, current_link, filename)
                else:
                    logging.info("GPT disabled")
                    logging.info("Skipping GPT")
                #saving_data.save_txt.save_pdf_to_text("./pdf_text/" + current_id, PDF_TEXT)

        except Exception as e:
            logging.error(f"Failed to process PDF for {current_link}::: {e}")
            continue
        logging.info("Article Complete!")
    return None


def process_all_pages(driver, base_url):
    curr_url = base_url
    while True:
        result_code = process_current_page(curr_url)
        if result_code == 100:
            break


        success = go_to_next_page(driver, curr_url)
        if not success:
            logging.info("No more pages to process")
            break
        else:
            curr_url = success
            logging.info(f"Moving to next page: {curr_url}")
        time.sleep(2)

# Main start
if __name__ == "__main__":
    parse_arguments()
    url = "https://www.regulations.gov/search/comment?filter=Attach&sortBy=postedDate&sortDirection=desc"
    driver.get(url)
    clear_folders()
    process_all_pages(driver, url)
    global allowGPT, days_back, doc_limit

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"Total time: {total_time}")
    logging.info("Finished")

    logging.info("Duplicates")
    logging.info(global_info.duplicate_files)
    logging.info(f"Doc Count {global_info.docs_looked_at}")

    if production_run:
        email_output(allowGPT, days_back, start_time, end_time, total_time)

driver.quit()
