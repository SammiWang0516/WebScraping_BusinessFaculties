import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch(url: str) -> BeautifulSoup | None:
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 403:
                wait = 15 * (attempt + 1)
                if attempt < 2:
                    time.sleep(wait)
                    continue
                else:
                    print(f"    ERROR fetching {url}: 403 Forbidden")
                    return None
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"    ERROR fetching {url}: {e}")
    return None


class StaticBS4Scraper(BaseScraper):
    """
    For universities whose faculty pages are static HTML.

    Two modes:
      - Per-dept URLs (each dept has a "url" key): one request per dept (e.g. UPenn Wharton)
      - Single URL (top-level "url" key + "dept_text" selector): one request, dept read from card (e.g. UT Austin McCombs)
    """

    def scrape(self) -> list[dict]:
        sel = self.config["selectors"]
        if "url" in self.config and "dept_text" in sel:
            return self._scrape_single_page()
        if "url" in self.config and "title" in sel:
            return self._scrape_single_keyword()
        if "profile_title" in sel:
            return self._scrape_per_dept_with_profiles()
        return self._scrape_per_dept()

    # ------------------------------------------------------------------
    # Single-page mode — one URL, dept read directly from each card (e.g. McCombs)
    # ------------------------------------------------------------------
    def _scrape_single_page(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]
        dept_area_map = {d["name"].lower(): d["area"] for d in dept_list}

        url = self.config["url"]
        print(f"  Fetching: {url}")
        soup = fetch(url)
        if soup is None:
            return []

        cards = soup.select(sel["faculty_card"])
        print(f"  {len(cards)} cards found")

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
            title = card.select_one(title_sel).get_text(strip=True) if title_sel else ""

            dept_tag = card.select_one(sel["dept_text"])
            dept_name = dept_tag.get_text(strip=True) if dept_tag else ""
            area = dept_area_map.get(dept_name.lower(), "")

            email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

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

        print(f"  → {len(results)} faculty saved")
        return results

    # ------------------------------------------------------------------
    # Single URL, keyword match — dept inferred from title text (e.g. UW Foster)
    # ------------------------------------------------------------------
    def _scrape_single_keyword(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]

        base_url = self.config["url"]
        total_pages = self.config.get("total_pages", 1)

        results = []
        seen_names = set()

        for page_num in range(total_pages):
            page_url = base_url if total_pages == 1 else f"{base_url}?page={page_num}"
            print(f"  Fetching page {page_num + 1}/{total_pages}")
            soup = fetch(page_url)
            if soup is None:
                continue

            for card in soup.select(sel["faculty_card"]):
                name_tag = card.select_one(sel["name"])
                if not name_tag:
                    continue
                name = " ".join(name_tag.get_text(strip=True).split())
                if not name:
                    continue

                title_parts = [t.get_text(strip=True) for t in card.select(sel["title"])]
                title = " | ".join(p for p in title_parts if p)
                first_title = title_parts[0] if title_parts else ""

                email_tag = card.find("a", href=lambda h: h and h.startswith("mailto:"))
                email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

                rank = self.parse_rank(first_title)

                dept_name, area = "", ""
                norm = first_title.lower().replace(" & ", " and ")
                for dept in dept_list:
                    keywords = [dept["name"].lower()] + [a.lower() for a in dept.get("match_aliases", [])]
                    if any(kw in norm for kw in keywords):
                        dept_name = dept["name"]
                        area = dept["area"]
                        break

                # Manual overrides for faculty whose title lacks dept info
                for ov in self.config.get("overrides", []):
                    if ov["name"] == name:
                        dept_name = ov["department"]
                        area = ov["area"]
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

            time.sleep(0.5)

        print(f"  → {len(results)} faculty saved")
        return results

    # ------------------------------------------------------------------
    # Per-dept mode — one URL per department (e.g. UPenn Wharton, Maryland Smith)
    # Supports: listing_next_sel for URL pagination, exclude_if_title_contains,
    #           faculty_card or faculty_row selector, multi-element titles
    # ------------------------------------------------------------------
    def _scrape_per_dept(self) -> list[dict]:
        sel = self.config["selectors"]
        card_sel = sel.get("faculty_card") or sel.get("faculty_row", "li")
        next_page_sel = sel.get("listing_next_sel")
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]
        results = []
        seen_names = set()

        for dept in self.config["departments"]:
            print(f"  Fetching: {dept['name']} — {dept['url']}")
            dept_count = 0
            page_url = dept["url"]

            while page_url:
                soup = fetch(page_url)
                if soup is None:
                    break

                for row in soup.select(card_sel):
                    name_tag = row.select_one(sel["name"])
                    if not name_tag:
                        continue
                    name = " ".join(name_tag.get_text(strip=True).split())
                    if not name:
                        continue

                    email_tag = row.find("a", href=lambda h: h and h.startswith("mailto:"))
                    email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

                    title_sel = sel.get("title")
                    if title_sel:
                        title_parts = [t.get_text(strip=True) for t in row.select(title_sel)]
                        title = " | ".join(p for p in title_parts if p)
                    else:
                        raw_text = row.get_text(separator=" ").strip()
                        title = raw_text
                        if name in title:
                            title = title[title.index(name) + len(name):]
                        if email and email in title:
                            title = title[:title.index(email)]
                        title = title.strip().lstrip(",").strip()

                    if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                        continue

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

                if next_page_sel:
                    next_tag = soup.select_one(next_page_sel)
                    page_url = urljoin(page_url, next_tag["href"]) if next_tag and next_tag.get("href") else None
                else:
                    page_url = None

                if page_url:
                    time.sleep(0.5)

            print(f"    → {dept_count} faculty added")
            time.sleep(1)

        return results

    # ------------------------------------------------------------------
    # Per-dept with profile visits — listing page gives names+links,
    # individual profile pages give title and email (e.g. Cornell Johnson)
    # ------------------------------------------------------------------
    def _scrape_per_dept_with_profiles(self) -> list[dict]:
        sel = self.config["selectors"]
        dept_list = self.config["departments"]

        # Optional: follow paginated listing pages (e.g. Carlson)
        next_page_sel = sel.get("listing_next_sel")
        # Optional: only collect profile links whose href starts with this prefix
        link_prefix = sel.get("profile_link_prefix")

        # Step 1: collect profile_url → [(dept_name, area)] across all area pages
        profile_depts: dict[str, list[tuple[str, str]]] = {}

        for dept in dept_list:
            url = dept.get("url")
            if not url:
                continue
            print(f"  Listing: {dept['name']} — {url}")

            card_sel = sel.get("faculty_card", "li")
            link_sel = sel.get("profile_link", "a")

            page_url = url
            while page_url:
                soup = fetch(page_url)
                if soup is None:
                    break

                for card in soup.select(card_sel):
                    link_tag = card.select_one(link_sel)
                    if not link_tag or not link_tag.get("href"):
                        continue
                    href = link_tag["href"]
                    if link_prefix and not href.startswith(link_prefix):
                        continue
                    profile_url = urljoin(url, href)
                    if profile_url not in profile_depts:
                        profile_depts[profile_url] = []
                    profile_depts[profile_url].append((dept["name"], dept["area"]))

                if next_page_sel:
                    next_tag = soup.select_one(next_page_sel)
                    page_url = urljoin(url, next_tag["href"]) if next_tag and next_tag.get("href") else None
                else:
                    page_url = None

                if page_url:
                    time.sleep(0.5)

            time.sleep(0.5)

        # Step 2: visit each unique profile once
        profile_title_sel = sel["profile_title"]
        name_sel = sel.get("profile_name", "h1")
        profile_delay = self.config.get("profile_visit_delay", 0.3)
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]
        total = len(profile_depts)
        print(f"  Visiting {total} profile pages...")

        results = []
        for i, (profile_url, depts) in enumerate(profile_depts.items()):
            if i % 25 == 0:
                print(f"    {i}/{total}")

            soup = fetch(profile_url)
            if soup is None:
                continue

            name_tag = soup.select_one(name_sel)
            if not name_tag:
                continue
            name = " ".join(name_tag.get_text(strip=True).split())
            if not name:
                continue

            title_tags = soup.select(profile_title_sel)
            title = title_tags[0].get_text(strip=True) if title_tags else ""

            if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                continue

            email_tag = soup.find("a", href=lambda h: h and h.startswith("mailto:"))
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

            dept_name = ", ".join(d[0] for d in depts)
            area = ", ".join(dict.fromkeys(d[1] for d in depts))

            rank = self.parse_rank(title)
            first, last = self.parse_name(name)

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

            time.sleep(profile_delay)

        print(f"  → {len(results)} faculty saved")
        return results
