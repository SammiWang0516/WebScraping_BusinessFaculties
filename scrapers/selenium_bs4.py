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
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


class SeleniumBS4Scraper(BaseScraper):
    """
    For universities whose faculty pages require JavaScript rendering.

    Two modes depending on config:
      - Single URL (top-level "url" key): loads one page, infers dept from title text (e.g. UT Dallas)
      - Per-dept URLs (each dept has a "url" key): loops over depts, assigns dept from config (e.g. Harvard)
    """

    def scrape(self) -> list[dict]:
        if "url" in self.config:
            return self._scrape_single(self.config["url"])
        else:
            return self._scrape_per_dept()

    # ------------------------------------------------------------------
    # Single URL mode — one page, dept inferred from title (UT Dallas)
    # ------------------------------------------------------------------
    def _scrape_single(self, url: str) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]

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

            dept_name, area = "", ""
            for dept in dept_list:
                if dept["name"].lower() in title.lower():
                    dept_name = dept["name"]
                    area = dept["area"]
                    break

            first, last = self.parse_name(name)

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

        print(f"  → {len(results)} faculty saved")
        return results

    # ------------------------------------------------------------------
    # Per-dept URL mode — one page per dept, dept assigned from config (Harvard)
    # ------------------------------------------------------------------
    def _scrape_per_dept(self) -> list[dict]:
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
                    print(f"    Timed out — skipping {dept['name']}")
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
                time.sleep(1)

        finally:
            driver.quit()

        return results
