"""
One-off debug script — opens the Columbia Accounting page with undetected-chromedriver
and prints the first faculty card's HTML so we can verify the correct CSS selectors.
Run once, then delete.
"""

import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://business.columbia.edu/directory/departments/accounting"

options = uc.ChromeOptions()
options.add_argument("--window-size=1920,1080")
driver = uc.Chrome(options=options)

try:
    print(f"Opening: {URL}")
    driver.get(URL)
    time.sleep(5)  # wait for page to settle

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Try known selector
    cards = soup.select("div.m-listing-faculty")
    print(f"\ndiv.m-listing-faculty → {len(cards)} found")

    if cards:
        print("\n--- First card HTML ---")
        print(cards[0].prettify()[:2000])
    else:
        print("\n--- Selector not found. Showing all div classes on page ---")
        divs = soup.find_all("div", class_=True)
        classes = set()
        for d in divs:
            for c in d.get("class", []):
                classes.add(c)
        for c in sorted(classes):
            print(f"  {c}")

finally:
    input("\nPress Enter to close browser...")
    driver.quit()
