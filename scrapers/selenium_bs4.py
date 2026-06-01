import time
from bs4 import BeautifulSoup, NavigableString
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
        elif "url" in self.config and "table_row_xpath" in sel:
            return self._scrape_table_status()
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
        pre_select_css = sel.get("pre_select_css")
        pre_select_value = sel.get("pre_select_value")
        facetwp_next_css = sel.get("facetwp_next_css")
        dept_area_lookup = {d["name"]: d["area"] for d in dept_list} if sel.get("dept_text") else {}

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
            post_load_wait = self.config.get("post_load_wait", 0)
            if post_load_wait:
                time.sleep(post_load_wait)

            # Pre-select a filter dropdown (e.g. FacetWP type filter)
            if pre_select_css and pre_select_value:
                try:
                    pre_el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, pre_select_css))
                    )
                    Select(pre_el).select_by_value(pre_select_value)
                    time.sleep(3)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                except Exception as e:
                    print(f"    pre_select '{pre_select_value}' failed: {e}")

            load_more_text = self.config.get("load_more_btn_text")
            if facetwp_next_css:
                # FacetWP-style pagination: each click replaces cards (not appends)
                cards = []
                pages = 0
                while True:
                    pages += 1
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    cards.extend(soup.select(sel["faculty_card"]))
                    try:
                        nxt = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, facetwp_next_css))
                        )
                        driver.execute_script("arguments[0].click();", nxt)
                        time.sleep(3)
                    except Exception:
                        break
                print(f"    FacetWP: {pages} pages, {len(cards)} cards total")
            elif load_more_text:
                clicks = 0
                while True:
                    try:
                        btn = WebDriverWait(driver, 8).until(
                            EC.element_to_be_clickable((By.XPATH, f'//button[contains(text(), "{load_more_text}")]'))
                        )
                        driver.execute_script("arguments[0].click();", btn)
                        clicks += 1
                        time.sleep(2)
                    except Exception:
                        break
                n = len(driver.find_elements(By.CSS_SELECTOR, sel["faculty_card"]))
                print(f"    Clicked '{load_more_text}' {clicks} times, {n} cards loaded")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["faculty_card"])
            elif scroll_count:
                scroll_sleep = self.config.get("scroll_sleep", 2.5)
                prev = 0
                for i in range(scroll_count):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_sleep)
                    n = len(driver.find_elements(By.CSS_SELECTOR, sel["faculty_card"]))
                    if n == prev and i > 2:
                        break
                    prev = n
                print(f"    Scrolled {i+1} times, {prev} cards loaded")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["faculty_card"])
            else:
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                cards = soup.select(sel["faculty_card"])
        finally:
            driver.quit()

        print(f"  {len(cards)} cards found on page")

        results = []
        seen_names = set()
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        for card in cards:
            name_tag = card.select_one(sel["name"])
            if not name_tag:
                continue
            name = " ".join(name_tag.get_text(strip=True).replace('﻿', '').split())
            if not name:
                continue

            title_sel = sel.get("title")
            if title_sel:
                title_parts = [t.get_text(strip=True) for t in card.select(title_sel)]
                title = " | ".join(p for p in title_parts if p)
            else:
                title = ""

            if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                continue

            email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

            rank = self.parse_rank(title)

            # dept_text: department name read directly from a card element
            dept_name, area = "", ""
            dept_text_sel = sel.get("dept_text")
            if dept_text_sel:
                dept_tag = card.select_one(dept_text_sel)
                raw_dept = dept_tag.get_text(strip=True) if dept_tag else ""
                dept_name, area = "", ""
                # Some pages store multiple depts as "Dept A,Dept B" — find first match
                for seg in raw_dept.split(","):
                    seg = seg.strip()
                    if seg in dept_area_lookup:
                        dept_name = seg
                        area = dept_area_lookup[seg]
                        break
                if not area:
                    continue  # skip non-academic staff
            elif sel.get("title_has_dept") and "," in title:
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
    # Per-dept URL mode — one page per dept, dept assigned from config (Harvard, ASU)
    # Supports next_page_btn_aria for button-click pagination (e.g. ASU W.P. Carey)
    # ------------------------------------------------------------------
    def _scrape_per_dept(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]
        next_page_aria = self.config.get("next_page_btn_aria")
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        results = []
        seen_names = set()

        for dept in dept_list:
            url = dept.get("url")
            if not url:
                print(f"  Skipping {dept['name']} — no URL in config")
                continue

            print(f"  Fetching: {dept['name']} — {url}")
            driver = make_driver()
            try:
                driver.get(url)

                wait_selector = f"{sel['faculty_card']} {sel['name']}"
                try:
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                except Exception:
                    print(f"    Timed out — skipping {dept['name']}")
                    continue

                dept_count = 0
                while True:
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    cards = soup.select(sel["faculty_card"])
                    count_before = len(seen_names)

                    for card in cards:
                        name_tag = card.select_one(sel["name"])
                        if not name_tag:
                            continue
                        name = " ".join(name_tag.get_text(strip=True).split())
                        if not name:
                            continue

                        title_sel = sel.get("title")
                        if title_sel and sel.get("title_all_except_last"):
                            title_tag = card.select_one(title_sel)
                            if title_tag:
                                nodes = [str(c).strip() for c in title_tag.children
                                         if isinstance(c, NavigableString) and str(c).strip()]
                                title = " ".join(nodes[:-1]) if nodes else ""
                            else:
                                title = ""
                        else:
                            title_tag = card.select_one(title_sel) if title_sel else None
                            title = title_tag.get_text(strip=True) if title_tag else ""

                        if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                            continue

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

                    if next_page_aria:
                        # If no new names were added this page, we've hit the end
                        if len(seen_names) == count_before:
                            break
                        try:
                            btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f'//button[@aria-label="{next_page_aria}"]'))
                            )
                            driver.execute_script("arguments[0].click();", btn)
                            # Wait for AJAX to replace cards before re-parsing
                            time.sleep(2)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, sel["faculty_card"]))
                            )
                            time.sleep(1)
                        except Exception:
                            break
                    else:
                        break

                print(f"    → {dept_count} faculty added")

            finally:
                driver.quit()

        return results

    # ------------------------------------------------------------------
    # Table-status mode — single URL, all rows in JS-rendered table,
    # filter by status column, names in "Last, First" format (e.g. Georgia Tech)
    # ------------------------------------------------------------------
    def _scrape_table_status(self) -> list[dict]:
        sel = self.config["selectors"]
        row_xpath = sel["table_row_xpath"]
        name_sel = sel["name"]
        title_sel = sel["title"]
        dept_sel = sel.get("dept", "div.stylized-table__dept")
        keep_statuses = set(self.config.get("keep_statuses", []))
        dept_area_map = self.config.get("dept_area_map", {})

        url = self.config["url"]
        print(f"  Loading: {url}")
        driver = make_driver()
        try:
            driver.get(url)
            time.sleep(5)
            rows = driver.find_elements(By.XPATH, row_xpath)
            print(f"  Found {len(rows)} total rows")

            results = []
            seen_names = set()

            for row in rows:
                html = row.get_attribute("outerHTML")
                soup = BeautifulSoup(html, "html.parser")
                tds = soup.find_all("td")
                if len(tds) < 3:
                    continue

                status = tds[2].get_text(strip=True)
                if keep_statuses and status not in keep_statuses:
                    continue

                name_tag = tds[1].select_one(name_sel)
                if not name_tag:
                    continue
                raw = " ".join(name_tag.get_text(strip=True).split())
                if "," in raw:
                    last_part, first_part = raw.split(",", 1)
                    raw = first_part.strip() + " " + last_part.strip()
                name = raw
                if not name or name in seen_names:
                    continue
                seen_names.add(name)

                title_tag = tds[1].select_one(title_sel)
                title = title_tag.get_text(strip=True) if title_tag else ""

                dept_div = tds[3].select_one(dept_sel) if len(tds) > 3 else None
                dept_raw = dept_div.get_text(strip=True) if dept_div else ""
                dept_primary = dept_raw.split(",")[0].strip() if dept_raw else ""
                area = dept_area_map.get(dept_primary, "Other")

                email_tag = soup.find("a", href=lambda h: h and h.startswith("mailto:"))
                email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

                rank = self.parse_rank(title)
                first, last = self.parse_name(name)

                results.append({
                    "name": name,
                    "first_name": first,
                    "last_name": last,
                    "original_title": title,
                    "department": dept_primary,
                    "area": area,
                    "university": self.config["full_name"],
                    "email": email,
                    "rank": rank,
                })
        finally:
            driver.quit()

        print(f"  → {len(results)} faculty saved")
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
    # Select-dept mode — dropdown filters by dept, all results on one page (Indiana Kelley, Berkeley Haas)
    # Config: url, selectors.dept_select (CSS for <select>),
    #         selectors.status_btn_id, selectors.search_btn_id,
    #         load_more_css (optional CSS for a "load more" link to click until gone)
    # ------------------------------------------------------------------
    def _scrape_select_dept(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]
        url = self.config["url"]

        status_btn_id = sel.get("status_btn_id")
        search_btn_id = sel.get("search_btn_id")
        dept_select_css = sel["dept_select"]
        load_more_css = self.config.get("load_more_css")

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
                    time.sleep(2)
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

                # Click "load more" link until it disappears
                if load_more_css:
                    while True:
                        try:
                            more = driver.find_element(By.CSS_SELECTOR, load_more_css)
                            if more.is_displayed():
                                driver.execute_script("arguments[0].click();", more)
                                time.sleep(2)
                            else:
                                break
                        except Exception:
                            break

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
