import time
import requests
from urllib.parse import quote
from .base import BaseScraper

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


class JsonAPIScraper(BaseScraper):
    """
    For universities that expose faculty data as a JSON API (e.g. Duke Fuqua).
    Each department has a 'slug' key used to build the API URL.
    Config keys:
      api_base  — base URL (slug and endpoint appended as /{slug}/{endpoint}.json)
      endpoints — list of endpoint names to fetch (default: ["faculty", "emeritus"])
    """

    def scrape(self) -> list[dict]:
        api_base = self.config["api_base"]
        dept_list = self.config["departments"]
        endpoints = self.config.get("endpoints", ["faculty", "emeritus"])

        results = []
        seen_names = set()

        for dept in dept_list:
            slug = quote(dept["slug"])
            dept_name = dept["name"]
            area = dept["area"]

            for endpoint in endpoints:
                url = f"{api_base}/{slug}/{endpoint}.json"
                print(f"  Fetching: {dept_name} ({endpoint})")

                try:
                    resp = requests.get(url, headers=HEADERS, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"    ERROR: {e}")
                    continue

                for person in data:
                    name = person.get("name", "").strip()
                    if not name:
                        continue

                    title = person.get("title", "").strip()
                    rank = self.parse_rank(title)
                    first, last = self.parse_name(name)

                    if name in seen_names:
                        for r in results:
                            if r["name"] == name:
                                if dept_name not in r["department"]:
                                    r["department"] += ", " + dept_name
                                if area not in r["area"]:
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
                        "email": "",
                        "rank": rank,
                    })

                time.sleep(0.3)

        print(f"  → {len(results)} faculty saved")
        return results
