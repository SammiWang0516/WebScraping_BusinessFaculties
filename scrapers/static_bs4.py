import time
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
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
    # Per-dept mode — one URL per department (e.g. UPenn Wharton)
    # ------------------------------------------------------------------
    def _scrape_per_dept(self) -> list[dict]:
        sel = self.config["selectors"]
        results = []
        seen_names = set()

        for dept in self.config["departments"]:
            print(f"  Fetching: {dept['name']} — {dept['url']}")
            soup = fetch(dept["url"])
            if soup is None:
                continue

            rows = soup.select(sel["faculty_row"])
            dept_count = 0

            for row in rows:
                name_tag = row.select_one(sel["name"])
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)
                if not name:
                    continue

                # Email from listing page
                email_tag = row.find("a", class_=sel.get("email_link_class"))
                email = ""
                if email_tag and email_tag.get("href", "").startswith("mailto:"):
                    email = email_tag["href"].replace("mailto:", "").strip()

                # Title: text between name and email
                raw_text = row.get_text(separator=" ").strip()
                title = raw_text
                if name in title:
                    title = title[title.index(name) + len(name):]
                if email and email in title:
                    title = title[:title.index(email)]
                title = title.strip().lstrip(",").strip()

                rank = self.parse_rank(title)
                first, last = self.parse_name(name)

                # Dedup: cross-dept faculty → merge dept and area, keep one row
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

        return results
