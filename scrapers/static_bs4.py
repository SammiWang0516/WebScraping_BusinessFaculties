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


class StaticBS4Scraper(BaseScraper):
    """
    For universities whose faculty pages are static HTML.
    Iterates over each department URL defined in the config and
    extracts faculty rows using BeautifulSoup.
    """

    def scrape(self) -> list[dict]:
        sel = self.config["selectors"]
        skip_keywords = [kw.lower() for kw in sel.get("skip_title_keywords", [])]
        results = []
        seen_names = set()

        for dept in self.config["departments"]:
            print(f"  Fetching: {dept['name']} — {dept['url']}")
            try:
                resp = requests.get(dept["url"], headers=HEADERS, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"    ERROR fetching {dept['url']}: {e}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select(sel["faculty_row"])
            dept_count = 0

            for row in rows:
                name_tag = row.find(sel["name"])
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)
                if not name:
                    continue

                # Extract title: full text of row minus the name and email link
                email_tag = row.find("a", class_=sel.get("email_link_class"))
                email = ""
                if email_tag and email_tag.get("href", "").startswith("mailto:"):
                    email = email_tag["href"].replace("mailto:", "").strip()

                raw_text = row.get_text(separator=" ").strip()
                # Title sits between the name and the email address
                title = raw_text
                if name in title:
                    title = title[title.index(name) + len(name):]
                if email and email in title:
                    title = title[:title.index(email)]
                title = title.strip().lstrip(",").strip()

                # Skip Emeritus, In Memoriam, etc.
                if any(kw in title.lower() for kw in skip_keywords):
                    continue

                rank = self.parse_rank(title)
                # Skip non-faculty roles (lecturers with no professor title count as Other)
                if rank == "Other":
                    continue

                first, last = self.parse_name(name)

                # Dedup: same person listed in multiple departments → append dept, keep one row
                if name in seen_names:
                    for r in results:
                        if r["name"] == name:
                            if dept["name"] not in r["department"]:
                                r["department"] = r["department"] + ", " + dept["name"]
                            if dept["area"] not in r["area"]:
                                r["area"] = r["area"] + ", " + dept["area"]
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
            time.sleep(1)  # polite delay between requests

        return results
