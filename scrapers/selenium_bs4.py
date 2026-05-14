import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


class SeleniumBS4Scraper(BaseScraper):
    """
    For universities whose faculty pages require JavaScript rendering.
    Loads a single URL with headless Chrome, waits for cards to appear,
    then parses with BeautifulSoup.
    Department is inferred by matching known department names against
    each faculty's title string.
    """

    def scrape(self) -> list[dict]:
        sel = self.config["selectors"]
        skip_keywords = [kw.lower() for kw in sel.get("skip_title_keywords", [])]
        dept_list = self.config["departments"]
        url = self.config["url"]

        print(f"  Loading: {url}")
        driver = make_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel["faculty_card"]))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
        finally:
            driver.quit()

        cards = soup.select(sel["faculty_card"])
        print(f"  {len(cards)} cards found on page")

        results = []
        seen_names = set()

        for card in cards:
            # Name
            name_tag = card.select_one(sel["name"])
            if not name_tag:
                continue
            name = " ".join(name_tag.get_text(strip=True).split())  # collapse whitespace
            if not name:
                continue

            # Title
            title_tag = card.select_one(sel["title"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Email
            email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

            # Skip unwanted roles
            if any(kw in title.lower() for kw in skip_keywords):
                continue

            rank = self.parse_rank(title)
            if rank == "Other":
                continue

            # Department: find which known dept name appears in the title
            dept_name, area = "", ""
            for dept in dept_list:
                if dept["name"].lower() in title.lower():
                    dept_name = dept["name"]
                    area = dept["area"]
                    break

            first, last = self.parse_name(name)

            # Dedup: same person in multiple depts → merge
            if name in seen_names:
                for r in results:
                    if r["name"] == name:
                        if dept_name and dept_name not in r["department"]:
                            r["department"] += ", " + dept_name
                        if area and area not in r["area"]:
                            r["area"] += ", " + area
                continue

            seen_names.add(name)
            results.append({
                "name": name,
                "first_name": first,
                "last_name": last,
                "original_title": title,
                "department": dept_name,
                "area": area,
                "university": self.config["full_name"],
                "email": email,
                "rank": rank,
            })

        print(f"  → {len(results)} faculty kept after filtering")
        return results
