import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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
        sel = self.config.get("selectors", {})
        if "url" in self.config and "total_pages" in self.config:
            return self._scrape_paginated()
        elif "url" in self.config and "dept_select" in sel:
            return self._scrape_select_dept()
        elif "url" in self.config:
            return self._scrape_single(self.config["url"])
        else:
            return self._scrape_per_dept()

    # ------------------------------------------------------------------
    # Single URL mode — one page, dept inferred from title (UT Dallas)
    # ------------------------------------------------------------------
    def _scrape_single(self, url: str) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]

        scroll_count = self.config.get("scroll_count", 0)
        print(f"  Loading: {url}")
        driver = make_driver()
        try:
            driver.get(url)
            wait_selector = f"{sel['faculty_card']} {sel['name']}"
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            except Exception:
                print(f"    Timed out waiting for content — attempting parse anyway")
            if scroll_count:
                prev = 0
                for i in range(scroll_count):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2.5)
                    n = len(driver.find_elements(By.CSS_SELECTOR, sel["faculty_card"]))
                    if n == prev and i > 2:
                        break
                    prev = n
                print(f"    Scrolled {i+1} times, {prev} cards loaded")
            else:
                time.sleep(3)
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
            if title_sel:
                title_parts = [t.get_text(strip=True) for t in card.select(title_sel)]
                title = " | ".join(p for p in title_parts if p)
            else:
                title = ""

            email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

            rank = self.parse_rank(title)

            # title_has_dept: title is "Rank,Department" — split on first comma
            dept_name, area = "", ""
            if sel.get("title_has_dept") and "," in title:
                raw_dept = title.split(",", 1)[1].strip().replace(" & ", " and ")
                dept_area_map = {d["name"].lower().replace(" & ", " and "): (d["name"], d["area"])
                                 for d in dept_list}
                if raw_dept.lower() in dept_area_map:
                    dept_name, area = dept_area_map[raw_dept.lower()]
            else:
                norm_parts = [p.lower().replace(" & ", " and ") for p in (title_parts if title_sel else [title])]
                for dept in dept_list:
                    keywords = [dept["name"].lower()] + [a.lower() for a in dept.get("match_aliases", [])]
                    if any(any(kw in part for kw in keywords) for part in norm_parts):
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

                # Wait for name element inside a card — ensures content is populated, not just the container
                wait_selector = f"{sel['faculty_card']} {sel['name']}"
                try:
                    WebDriverWait(driver, 40).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
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

    # ------------------------------------------------------------------
    # Paginated mode — multiple ?page=N URLs, dept read directly from card (NYU)
    # ------------------------------------------------------------------
    def _scrape_paginated(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]
        base_url = self.config["url"]
        total_pages = self.config["total_pages"]
        dept_area_map = {d["name"].lower(): d["area"] for d in dept_list}

        results = []
        seen_names = set()

        driver = make_driver()
        try:
            for page_num in range(total_pages):
                url = base_url if page_num == 0 else f"{base_url}?page={page_num}"
                print(f"  Page {page_num + 1}/{total_pages}")
                driver.get(url)

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel["faculty_card"]))
                    )
                except Exception:
                    print(f"    Timed out — skipping page {page_num}")
                    continue

                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["faculty_card"])

                for card in cards:
                    name_tag = card.select_one(sel["name"])
                    if not name_tag:
                        continue
                    name = " ".join(name_tag.get_text(strip=True).split())
                    if not name:
                        continue

                    # Title (italic paragraph)
                    title_sel = sel.get("title")
                    title_tag = card.select_one(title_sel) if title_sel else None
                    title = title_tag.get_text(strip=True) if title_tag else ""

                    # Department text read directly from card, strip trailing " Department"
                    dept_name, area = "", ""
                    dept_sel = sel.get("dept_text")
                    if dept_sel:
                        dept_tag = card.select_one(dept_sel)
                        if dept_tag:
                            raw = dept_tag.get_text(strip=True)
                            dept_name = raw.removesuffix(" Department").strip()
                            area = dept_area_map.get(dept_name.lower(), "")

                    # Email — try mailto href first, then link text containing @
                    email = ""
                    email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
                    if email_tag:
                        email = email_tag["href"].replace("mailto:", "").strip()
                    else:
                        for a in card.find_all("a"):
                            txt = a.get_text(strip=True)
                            if "@" in txt:
                                email = txt
                                break

                    rank = self.parse_rank(title)
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

                print(f"    → {len(results)} total so far")
                time.sleep(1)

        finally:
            driver.quit()

        return results

    # ------------------------------------------------------------------
    # Select-dept mode — dropdown filters by dept, all results on one page (Indiana Kelley)
    # Config: url, selectors.dept_select (CSS for <select>),
    #         selectors.status_btn_id, selectors.search_btn_id
    # ------------------------------------------------------------------
    def _scrape_select_dept(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]
        url = self.config["url"]

        status_btn_id = sel.get("status_btn_id")
        search_btn_id = sel.get("search_btn_id")
        dept_select_css = sel["dept_select"]

        results = []
        seen_names = set()

        driver = make_driver()
        try:
            driver.get(url)

            # Click "show all" button if present (e.g. shows adjuncts/visitors too)
            if status_btn_id:
                try:
                    btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.ID, status_btn_id))
                    )
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                except Exception:
                    print(f"    status_btn '{status_btn_id}' not found — continuing")

            for dept in dept_list:
                dept_name = dept["name"]
                print(f"  Fetching dept: {dept_name}")

                # Select department from dropdown
                try:
                    sel_el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, dept_select_css))
                    )
                    Select(sel_el).select_by_visible_text(dept_name)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"    Could not select '{dept_name}': {e} — skipping")
                    continue

                # Click search button
                if search_btn_id:
                    try:
                        srch = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, search_btn_id))
                        )
                        driver.execute_script("arguments[0].click();", srch)
                        time.sleep(2)
                    except Exception as e:
                        print(f"    search_btn '{search_btn_id}' failed: {e}")

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

                    # Title: first text node of the title <p> (before <br/>)
                    title = ""
                    title_sel = sel.get("title")
                    if title_sel:
                        p = card.select_one(title_sel)
                        if p:
                            title = next((s.strip() for s in p.strings if s.strip()), "")

                    email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
                    email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

                    rank = self.parse_rank(title)
                    first, last = self.parse_name(name)

                    if name in seen_names:
                        for r in results:
                            if r["name"] == name:
                                if dept_name not in r["department"]:
                                    r["department"] += ", " + dept_name
                                if dept["area"] not in r["area"]:
                                    r["area"] += ", " + dept["area"]
                        continue

                    seen_names.add(name)
                    results.append({
                        "name": name,
                        "first_name": first,
                        "last_name": last,
                        "original_title": title,
                        "department": dept_name,
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

        print(f"  Total: {len(results)} faculty saved")
        return results
