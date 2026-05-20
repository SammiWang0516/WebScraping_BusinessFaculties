"""
Debug script: probe MIT Sloan faculty directory.
Run: python debug_mit.py
"""
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

URL = "https://mitsloan.mit.edu/faculty/faculty-search"

# --- Try static first ---
print("=== Static request ===")
resp = requests.get(URL, headers=HEADERS, timeout=15)
print(f"Status: {resp.status_code}")
soup_static = BeautifulSoup(resp.text, "html.parser")

# Common card patterns
for sel in ["div.faculty-search-result", "div.faculty-card", "li.faculty",
            "article.faculty", "div.profile", "div.person", "div[class*='faculty']"]:
    found = soup_static.select(sel)
    if found:
        print(f"  Static: found {len(found)} '{sel}'")

# --- Try Selenium ---
print("\n=== Selenium ===")
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)
try:
    driver.get(URL)
    time.sleep(4)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    for sel in ["div.faculty-search-result", "div.faculty-card", "li.faculty",
                "article", "div.profile", "div[class*='faculty']",
                "div.tile", "div.person-tile", "ul.faculty-list li"]:
        found = soup.select(sel)
        if found:
            print(f"  Selenium: found {len(found)} '{sel}'")

    # Print a snippet of first result
    # Look for any element with a name-like heading
    for tag in ["h2", "h3", "h4"]:
        tags = soup.find_all(tag)
        if tags:
            print(f"\n  First 5 <{tag}> texts:")
            for t in tags[:5]:
                print(f"    {t.get_text(strip=True)[:80]}")
            break

    # Check page title and URL
    print(f"\n  Page title: {driver.title}")
    print(f"  Final URL:  {driver.current_url}")

    # Check for pagination or load-more
    for txt in ["load more", "next", "pagination", "page"]:
        els = [e for e in soup.find_all(True) if txt in e.get_text(strip=True).lower()
               and len(e.get_text(strip=True)) < 30]
        if els:
            print(f"\n  '{txt}' elements found: {len(els)}")
            for e in els[:3]:
                print(f"    <{e.name} class='{e.get('class','')}'>: {e.get_text(strip=True)[:60]}")

    # Print raw snippet around 'faculty' in HTML
    src = driver.page_source
    idx = src.lower().find("faculty-search-result")
    if idx > 0:
        print(f"\n  Snippet around 'faculty-search-result':")
        print(src[max(0,idx-50):idx+300])

finally:
    driver.quit()

print("\nDone.")
