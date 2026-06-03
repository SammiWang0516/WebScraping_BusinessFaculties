"""
Debug script: probe NYU Stern faculty directory.
Run: python debug_nyu.py
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

CANDIDATES = [
    "https://www.stern.nyu.edu/faculty/faculty-directory",
    "https://www.stern.nyu.edu/faculty",
    "https://www.stern.nyu.edu/faculty-research/faculty-directory",
    "https://www.stern.nyu.edu/about/faculty-research/faculty-directory",
]

# --- Static requests ---
print("=== Static requests ===")
working_url = None
for u in CANDIDATES:
    resp = requests.get(u, headers=HEADERS, timeout=15)
    print(f"  {resp.status_code}  {u}")
    if resp.status_code == 200 and not working_url:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Quick check for faculty cards
        for sel in ["div.faculty-card", "li.faculty", "div.profile", "article",
                    "div[class*='faculty']", "div[class*='person']"]:
            found = soup.select(sel)
            if found:
                print(f"    Static hit: {len(found)} '{sel}'")
                working_url = u

# --- Crawl homepage for faculty links ---
print("\n=== Faculty-related links on homepage ===")
resp = requests.get("https://www.stern.nyu.edu", headers=HEADERS, timeout=15)
soup_home = BeautifulSoup(resp.text, "html.parser")
seen = set()
for a in soup_home.find_all("a", href=True):
    href = a["href"]
    if "faculty" in href.lower():
        full = href if href.startswith("http") else "https://www.stern.nyu.edu" + href
        if full not in seen:
            seen.add(full)
            print(f"  {full}")

# --- Selenium: wait for AJAX results ---
BASE_URL = "https://www.stern.nyu.edu/faculty"
print(f"\n=== Selenium (waiting for AJAX) ===")
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)
try:
    driver.get(BASE_URL)

    # Wait up to 20s for actual results to appear — try common Drupal Views selectors
    result_sel = None
    for sel in ["div.views-row", "article.views-row", "li.views-row",
                "div.faculty-result", "div.search-result",
                "div[class*='result']", "article"]:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            found = soup.select(sel)
            if len(found) > 3:  # more than 3 means real results, not form elements
                result_sel = sel
                print(f"  Results found with '{sel}': {len(found)} items")
                break
        except Exception:
            pass

    if not result_sel:
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Try Tailwind card selector from prior run
        cards = soup.select("div.shadow-share")
        print(f"\n  div.shadow-share: {len(cards)} found")
        if cards:
            result_sel = "div.shadow-share"
            print(f"\n  First card HTML:")
            print(str(cards[0])[:800])
            print(f"\n  All tags inside first card:")
            for tag in cards[0].find_all(True):
                cls = " ".join(tag.get("class", []))[:70]
                txt = tag.get_text(strip=True)[:60]
                if txt:
                    print(f"    <{tag.name} class='{cls}'>: {txt}")
            # Check pagination
            last_page = None
            for a in soup.find_all("a", href=True):
                if "page=" in a.get("href", ""):
                    try:
                        p = int(a["href"].split("page=")[-1].split("&")[0])
                        if last_page is None or p > last_page:
                            last_page = p
                    except ValueError:
                        pass
            print(f"\n  Last page: {last_page}  (~{(last_page+1)*len(cards)} total faculty)")
        else:
            print("  No cards found with div.shadow-share either.")
    else:
        # Show first card and its structure
        cards = soup.select(result_sel)
        print(f"\n  First card HTML:")
        print(str(cards[0])[:600])

        # Find name, title, dept selectors inside card
        print(f"\n  All tag/class inside first card:")
        for tag in cards[0].find_all(True):
            cls = " ".join(tag.get("class", []))
            txt = tag.get_text(strip=True)[:60]
            print(f"    <{tag.name} class='{cls}'>: {txt}")

        # Check pagination
        last_page = None
        for a in soup.find_all("a", href=True):
            if "page=" in a.get("href", ""):
                try:
                    p = int(a["href"].split("page=")[-1].split("&")[0])
                    if last_page is None or p > last_page:
                        last_page = p
                except ValueError:
                    pass
        print(f"\n  Last page number in pagination: {last_page}")
        print(f"  Estimated total faculty: ~{(last_page+1) * len(cards) if last_page else '?'}")

finally:
    driver.quit()

print("\nDone.")
