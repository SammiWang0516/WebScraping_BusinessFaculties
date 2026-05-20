"""
Debug script: probe USC Marshall main faculty directory.
Run: python debug_usc.py
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.marshall.usc.edu/faculty-research/faculty-directory"

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)

try:
    print(f"Loading {URL} ...")
    driver.get(URL)

    # Wait for faculty cards
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.person-list-item"))
        )
        print("Cards found — waiting 3s for full render...")
        time.sleep(3)
    except Exception as e:
        print(f"Timeout waiting for cards: {e}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("li.person-list-item")
    print(f"\nTotal li.person-list-item on page: {len(cards)}")

    # Check pagination / load-more buttons
    load_more = soup.find("a", string=lambda t: t and "load more" in t.lower())
    pagination = soup.select("ul.pager li") or soup.select("nav.pager")
    print(f"Load-more link: {load_more}")
    print(f"Pagination elements: {len(pagination)}")

    # Check for any 'next page' indicators
    for tag in soup.find_all(True):
        txt = tag.get_text(strip=True).lower()
        if "load more" in txt or "next page" in txt or "show more" in txt:
            print(f"  Possible paginator: <{tag.name} class='{tag.get('class','')}'>: {txt[:80]}")

    # Inspect first 5 cards
    print("\n--- First 5 cards ---")
    for i, card in enumerate(cards[:5]):
        name_tag = card.select_one("h3.title")
        title_tags = card.select("ul.position-list li")
        name = name_tag.get_text(strip=True) if name_tag else "NO NAME"
        titles = [t.get_text(strip=True) for t in title_tags]
        print(f"  [{i+1}] {name}")
        for t in titles:
            print(f"       title: {t}")

    # Check dept filter select options
    print("\n--- Department filter options ---")
    selects = soup.find_all("select")
    for sel in selects:
        print(f"  <select name='{sel.get('name')}' id='{sel.get('id')}'>")
        for opt in sel.find_all("option"):
            print(f"    value='{opt.get('value','')}' → {opt.get_text(strip=True)}")

    # Check for AJAX/fetch params in page source
    src = driver.page_source
    if "department" in src.lower():
        # Find relevant snippets
        idx = src.lower().find("department")
        print(f"\nFound 'department' at index {idx}:")
        print(src[max(0,idx-100):idx+200])

finally:
    driver.quit()
    print("\nDone.")
