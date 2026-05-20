import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import BaseScraper


def make_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    return uc.Chrome(options=options)


class SeleniumStealthScraper(BaseScraper):
    """
    For universities whose pages are protected by Cloudflare or other bot detection.
    Uses undetected-chromedriver to bypass fingerprinting.
    Loops over per-department URLs defined in the config (each dept must have a "url" key).
    """

    def scrape(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]

        results = []
        seen_names = set()

        driver = make_driver()
        try:
            for dept in dept_list:
                url = dept.get("url")
                if not url:
                    print(f"  Skipping {dept['name']} — no URL in config")
                    continue

                print(f"  Fetching: {dept['name']} — {url}")
                driver.get(url)

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel["faculty_card"]))
                    )
                except Exception:
                    print(f"    Timed out or blocked — skipping {dept['name']}")
                    continue

                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["faculty_card"])
                dept_count = 0

                for card in cards:
                    name_tag = card.select_one(sel["name"])
                    if not name_tag:
                        continue
                    name = " ".join(name_tag.get_text(strip=True).split())
                    if not name:
                        continue

                    title_sel = sel.get("title")
                    title_tag = card.select_one(title_sel) if title_sel else None
                    title = title_tag.get_text(strip=True) if title_tag else ""

                    email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
                    email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

                    rank = self.parse_rank(title)
                    first, last = self.parse_name(name)

                    if name in seen_names:
                        for r in results:
                            if r["name"] == name:
                                if dept["name"] not in r["department"]:
                                    r["department"] += ", " + dept["name"]
                                if dept["area"] not in r["area"]:
                                    r["area"] += ", " + dept["area"]
                        continue

                    seen_names.add(name)
                    results.append({
                        "name": name,
                        "first_name": first,
                        "last_name": last,
                        "original_title": title,
                        "department": dept["name"],
                        "area": dept["area"],
                        "university": self.config["full_name"],
                        "email": email,
                        "rank": rank,
                    })
                    dept_count += 1

                print(f"    → {dept_count} faculty added")
                time.sleep(2)

        finally:
            driver.quit()

        return results
