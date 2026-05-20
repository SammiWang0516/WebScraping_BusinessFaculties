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

URL = "https://mitsloan.mit.edu/faculty/faculty-directory"

print(f"=== Selenium: {URL} ===")
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)
try:
    driver.get(URL)
    print("Waiting for page to load...")
    time.sleep(6)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    print(f"  Page title: {driver.title}")
    print(f"  Final URL:  {driver.current_url}")

    # Try all common card selectors
    print("\n--- Card selector counts ---")
    for sel in ["div.faculty-card", "div.faculty-search-result", "li.faculty",
                "article", "div.profile-card", "div.person-card",
                "div[class*='faculty']", "div[class*='person']", "div[class*='card']",
                "div[class*='tile']", "li[class*='faculty']", "ul.faculty-list li",
                "div.views-row", "div.view-row"]:
        found = soup.select(sel)
        if found:
            print(f"  {len(found):>4}  '{sel}'")

    # Print all unique class names containing 'faculty'/'person'/'card'
    print("\n--- Unique classes with 'faculty'/'person'/'profile' ---")
    classes = set()
    for tag in soup.find_all(True):
        for c in tag.get("class", []):
            if any(kw in c.lower() for kw in ["faculty", "person", "profile", "card", "tile"]):
                classes.add(c)
    for c in sorted(classes):
        print(f"  .{c}")

    # Show academic group filters
    print("\n--- Academic group filters ---")
    for li in soup.select("li.directory__filters-list-item-group"):
        a = li.find("a")
        print(f"  '{a.get_text(strip=True) if a else li.get_text(strip=True)}'  href={a['href'] if a and a.get('href') else ''}")

    # Show first 10 dt/dd pairs (name + academic group)
    print("\n--- First 10 faculty (dt/dd pairs) ---")
    dts = soup.select("dt.directory--item-title")
    print(f"  Total dt elements: {len(dts)}")
    for dt in dts[:10]:
        a = dt.find("a")
        name = a.get_text(strip=True) if a else dt.get_text(strip=True)
        href = a["href"] if a and a.get("href") else ""
        dd = dt.find_next_sibling("dd")
        group = dd.get_text(strip=True) if dd else ""
        print(f"  {name}")
        print(f"    group: {group}")
        print(f"    href:  {href}")

    # Check if static request works on the correct URL
    print("\n--- Static request to correct URL ---")
    resp2 = requests.get("https://mitsloan.mit.edu/faculty/faculty-directory", headers=HEADERS, timeout=15)
    print(f"  Status: {resp2.status_code}")
    if resp2.status_code == 200:
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        dts2 = soup2.select("dt.directory--item-title")
        print(f"  dt elements in static response: {len(dts2)}")

finally:
    driver.quit()

print("\nDone.")
