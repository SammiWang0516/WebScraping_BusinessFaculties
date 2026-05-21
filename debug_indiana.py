"""
Debug script: probe Indiana Kelley faculty directory.
Run: python debug_indiana.py
"""
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://kelley.iu.edu/faculty-research/faculty-directory/index.html"

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)

try:
    print(f"Loading: {URL}")
    driver.get(URL)

    # Wait for initial page load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except Exception:
        pass
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # --- Check for status-all button ---
    all_btn = soup.find("button", id="status-all")
    print(f"\n'status-all' button found: {all_btn is not None}")

    # --- Check for department select dropdown ---
    select_el = soup.find("select")
    if select_el:
        options_list = [o.get_text(strip=True) for o in select_el.find_all("option")]
        print(f"\nDropdown options ({len(options_list)}):")
        for o in options_list:
            print(f"  {o}")
    else:
        print("\nNo <select> dropdown found.")

    # --- Check for A-Z letter nav ---
    letters = soup.find_all("a", class_=lambda c: c and "char-select" in c)
    print(f"\nA-Z letter links found: {len(letters)}")

    # --- Try clicking status-all and loading all faculty ---
    print("\n--- Clicking status-all button ---")
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "status-all"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
    except Exception as e:
        print(f"  status-all click failed: {e}")

    # --- Check for faculty card selectors after click ---
    soup2 = BeautifulSoup(driver.page_source, "html.parser")
    for sel in [
        "div.faculty-directory",
        "div[class*='faculty-directory']",
        "div[class*='faculty']",
        "div.grid",
        "div[class*='grid']",
        "li.faculty",
        "article",
    ]:
        found = soup2.select(sel)
        if found:
            print(f"  {sel}: {len(found)} found")

    # --- Find "All" letter or first letter and click it ---
    print("\n--- Looking for letter navigation after status-all ---")
    try:
        letter_els = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@class,"char-select")]'))
        )
        print(f"  {len(letter_els)} letter links found")
        # Click first letter
        driver.execute_script("arguments[0].click();", letter_els[0])
        time.sleep(2)
        soup3 = BeautifulSoup(driver.page_source, "html.parser")

        # Probe card selectors
        for sel in [
            "div.faculty-directory.grid.thirds",
            "div[class*='faculty-directory']",
            "div[class*='thirds']",
            "div[class*='grid']",
            "div.text",
        ]:
            found = soup3.select(sel)
            if found:
                print(f"  After letter click — {sel}: {len(found)}")

        # Show first card structure
        cards = soup3.select("div[class*='faculty-directory']")
        if not cards:
            cards = soup3.select("div[class*='thirds']")
        if cards:
            print(f"\n  First card HTML (first 800 chars):")
            print(str(cards[0])[:800])
            print(f"\n  All tags in first card:")
            for tag in cards[0].find_all(True):
                cls = " ".join(tag.get("class", []))[:60]
                txt = tag.get_text(strip=True)[:60]
                if txt:
                    print(f"    <{tag.name} class='{cls}'>: {txt}")

    except Exception as e:
        print(f"  Letter nav failed: {e}")

    # --- Check for department select and its options ---
    print("\n--- Department dropdown options (current state) ---")
    try:
        sel_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//select"))
        )
        sel_obj = Select(sel_el)
        print(f"  Options: {[o.text for o in sel_obj.options]}")
    except Exception as e:
        print(f"  Dropdown check failed: {e}")

finally:
    driver.quit()

print("\nDone.")
