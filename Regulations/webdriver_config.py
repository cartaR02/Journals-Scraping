from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def selenium_config() -> webdriver:
    options: Options = Options()
    # Uncomment the next line for headless testing
    # options.add_argument("--headless")
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("permissions.default.image", 1)
    options.profile = firefox_profile
    driver: webdriver = webdriver.Firefox(options=options)  # type: ignore
    return driver