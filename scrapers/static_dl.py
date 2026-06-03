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


class StaticDLScraper(BaseScraper):
    """
    For MIT Sloan's alphabetical directory, which uses a definition list structure:
      <dt class="directory--item-title"><a>Last, First</a></dt>
      <dd class="directory--item-def">Chair text + Rank, Academic Group</dd>
    Names are in "Last, First" format and are reversed before output.
    """

    def scrape(self) -> list[dict]:
        url = self.config["url"]
        dept_list = self.config["departments"]

        print(f"  Fetching: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    ERROR: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        dts = soup.select("dt.directory--item-title")
        print(f"  {len(dts)} entries found")

        results = []
        seen_names = set()
        for dt in dts:
            a = dt.find("a")
            if not a:
                continue

            # Names stored as "Last, First" — reverse to "First Last"
            raw_name = " ".join(a.get_text(strip=True).split())
            if "," in raw_name:
                last_part, first_part = raw_name.split(",", 1)
                name = first_part.strip() + " " + last_part.strip()
            else:
                name = raw_name
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            dd = dt.find_next_sibling("dd")
            title = " ".join(dd.get_text(strip=True).split()) if dd else ""

            rank = self.parse_rank(title)
            first, last = self.parse_name(name)

            dept_name, area = "", ""
            norm_title = title.lower().replace(" & ", " and ")
            for dept in dept_list:
                keywords = [dept["name"].lower()] + [a.lower() for a in dept.get("match_aliases", [])]
                if any(kw in norm_title for kw in keywords):
                    dept_name = dept["name"]
                    area = dept["area"]
                    break

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

        print(f"  → {len(results)} faculty saved")
        return results
