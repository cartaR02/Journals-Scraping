import csv
from bs4 import BeautifulSoup, NavigableString
import requests
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def selenium_config() -> webdriver: # type: ignore
    options: Options = Options()
    #options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 2)
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options) # type: ignore
    return driver

driver = selenium_config()

csvFileName = "WebsiteData.csv"

def retrieve_site_html(URL):
    try:
        driver.get(URL)
    except:
        print(URL + " Failed to access")
        return None
    request_info = driver.page_source
    time.sleep(2)
    site_html = BeautifulSoup(request_info, "html.parser")
    return site_html

def gather_landing_page_containers(LANDING_PAGE_CONTAINERS, HTML):
    # example
    # class|container~class|title~elem|article
    #dereferce the information
    # allow multiple finds ~
    
    find_list = LANDING_PAGE_CONTAINERS.split("~")
    print(find_list)
    html_to_return = HTML
    for finds in find_list:

        # exammple
        # class|titles
        identifier_list = finds.split("|")
        # find or find_all
        find, element, name = identifier_list

        FIND_ALL: bool = find == "find_all"
        IS_ELEM: bool = element == "elem"

        if IS_ELEM:
            
            if FIND_ALL:
                html_to_return = html_to_return.find_all(name)
                print("find_all hit")
            else:
                print("find hti")
                html_to_return = html_to_return.find(name)

        else:
            attributes = {element: name}
            if FIND_ALL:
                html_to_return = html_to_return.find_all(attrs=attributes)
            else:
                html_to_return = html_to_return.find(attrs=attributes)
        if html_to_return is None:
            print("Where it broke: " + finds)
            print("It broke")
            return

    return html_to_return

with open(csvFileName, "r") as journal_data:
    journal_reader = csv.reader(journal_data)

    counter = 0

    for journal_row in journal_reader:
        counter += 1

        JOURNAL_INFO = {
            "JOURNAL_ID": journal_row[0],
            "URL": journal_row[1],
            "CONTAINER_IDENTIFIERS": journal_row[2]
        }

        html = retrieve_site_html(JOURNAL_INFO["URL"])

        if html is None:
            next(journal_reader)
        print("HTML GATHERED")
        # in the find assume find all for links, if one is gathered nothing matters
        containers = gather_landing_page_containers(JOURNAL_INFO["CONTAINER_IDENTIFIERS"], html)
        print(containers)



driver.quit()