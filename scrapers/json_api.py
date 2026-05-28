import time
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
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
    Three modes:
    1. Slug mode (e.g. Duke): api_base + per-dept slug + endpoint.json
    2. Bulk mode (e.g. Illinois): single API call returns all faculty.
       Config keys: bulk_api_url, bulk_api_params, bulk_api_items_key,
       field_map (name/title/email/dept_field/unit_field),
       dept_area_map (list of {dept, unit?, label, area}),
       exclude_departments, exclude_if_title_contains
    3. AEM items mode (e.g. Boston College): single HTML endpoint returning all faculty.
       Config keys: aem_items_url, dept_area_map (dict: dept→area)
    """

    def scrape(self) -> list[dict]:
        if self.config.get("aem_items_url"):
            return self._scrape_aem_items()
        if self.config.get("bulk_api_url"):
            return self._scrape_bulk()
        return self._scrape_slug()

    def _scrape_aem_items(self) -> list[dict]:
        url = self.config["aem_items_url"]
        dept_area = self.config.get("dept_area_map", {})
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        print(f"  Fetching all faculty from AEM items endpoint...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"    ERROR: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.person-list-expertise")
        print(f"  Found {len(cards)} cards")

        results = []
        seen_names = set()

        for card in cards:
            name_tag = card.select_one("h3 a")
            if not name_tag:
                continue
            first = name_tag.get("data-first-name", "").strip()
            last = name_tag.get("data-last-name", "").strip()
            name = f"{first} {last}".strip() or name_tag.get_text(strip=True)
            if not name:
                continue

            title_tag = card.select_one("h4")
            title = title_tag.get_text(strip=True) if title_tag else ""

            if exclude_patterns and title and any(p in title.lower() for p in exclude_patterns):
                continue

            email_tag = card.select_one("a[href^='mailto:']")
            email = email_tag["href"].replace("mailto:", "").strip() if email_tag else ""

            dept_tag = card.select_one("div.department-column span")
            dept = dept_tag.get_text(strip=True) if dept_tag else "Other"
            area = dept_area.get(dept, "Other")

            rank = self.parse_rank(title)

            if name in seen_names:
                for r in results:
                    if r["name"] == name:
                        if dept not in r["department"]:
                            r["department"] += ", " + dept
                        if area not in r["area"]:
                            r["area"] += ", " + area
                continue

            seen_names.add(name)
            if not first or not last:
                first, last = self.parse_name(name)
            results.append({
                "name": name,
                "first_name": first,
                "last_name": last,
                "original_title": title,
                "department": dept,
                "area": area,
                "university": self.config["full_name"],
                "email": email,
                "rank": rank,
            })

        print(f"  → {len(results)} faculty saved")
        return results

    def _scrape_bulk(self) -> list[dict]:
        url = self.config["bulk_api_url"]
        params = self.config.get("bulk_api_params", {})
        items_key = self.config.get("bulk_api_items_key", "items")
        fm = self.config.get("field_map", {})
        name_field = fm.get("name", "fullnamefirst")
        title_field = fm.get("title", "title")
        email_field = fm.get("email", "email")
        dept_field = fm.get("dept_field", "department")
        unit_field = fm.get("unit_field", "unit")

        exclude_depts = set(self.config.get("exclude_departments", []))
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]
        keep_patterns = [p.lower() for p in self.config.get("keep_if_title_contains", [])]
        bio_field = fm.get("bio_field", "biography")
        include_blank_bio = self.config.get("include_blank_title_if_bio", False)
        dept_area_map = self.config.get("dept_area_map", [])

        print(f"  Fetching all faculty from API...")
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"    ERROR: {e}")
            return []

        items = data if isinstance(data, list) else data.get(items_key, [])
        print(f"  API returned {len(items)} items")

        results = []
        seen_names = set()
        pending_profile = []

        for person in items:
            raw_dept = person.get(dept_field, "").strip()
            raw_unit = person.get(unit_field, "").strip()

            if raw_dept in exclude_depts:
                continue

            # Resolve dept label and area from dept_area_map
            dept_label, area = raw_dept, "Other"
            for mapping in dept_area_map:
                if mapping["dept"] != raw_dept:
                    continue
                if "unit" in mapping and mapping["unit"] != raw_unit:
                    continue
                dept_label = mapping.get("label", raw_dept)
                area = mapping.get("area", "Other")
                break

            name = person.get(name_field, "").strip()
            if not name:
                continue

            title = person.get(title_field, "").strip()
            bio = person.get(bio_field, "").strip() if bio_field else ""

            if title:
                if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                    continue
                if keep_patterns and not any(p in title.lower() for p in keep_patterns):
                    continue
            else:
                # Blank title: include only if bio is present and configured
                if not (include_blank_bio and bio):
                    # Queue for profile scraping if configured
                    profile_cfg = self.config.get("profile_scrape")
                    if profile_cfg:
                        url_field = profile_cfg.get("url_field", "externalurl")
                        profile_path = person.get(url_field, "")
                        if profile_path:
                            pending_profile.append((person, dept_label, area, profile_path))
                    continue
                # Use biography as a rank signal
                title = ""

            email = person.get(email_field, "").strip()
            rank_source = bio if (not title and bio) else title
            rank = self.parse_rank(rank_source)
            first, last = self.parse_name(name)

            if name in seen_names:
                for r in results:
                    if r["name"] == name:
                        if dept_label not in r["department"]:
                            r["department"] += ", " + dept_label
                        if area not in r["area"]:
                            r["area"] += ", " + area
                continue

            seen_names.add(name)
            results.append({
                "name": name,
                "first_name": first,
                "last_name": last,
                "original_title": title,
                "department": dept_label,
                "area": area,
                "university": self.config["full_name"],
                "email": email,
                "rank": rank,
            })

        # Phase 2: profile scraping for blank-title, no-bio people
        if pending_profile:
            profile_cfg = self.config["profile_scrape"]
            base_url = profile_cfg["base_url"]
            institution_kw = [k.lower() for k in profile_cfg.get("institution_keywords", ["university of illinois"])]
            faculty_kw = ["professor", "lecturer", "instructor"]
            print(f"  Profile scraping {len(pending_profile)} blank-title people...")
            found = 0
            for person, dept_label, area, profile_path in pending_profile:
                name_field_val = person.get(name_field, "").strip()
                if not name_field_val or name_field_val in seen_names:
                    continue
                url = base_url.rstrip("/") + profile_path
                try:
                    resp = requests.get(url, headers=HEADERS, timeout=10)
                    lines = [l.strip() for l in BeautifulSoup(resp.text, "html.parser")
                             .get_text(separator="\n").split("\n") if l.strip()]
                    uiuc = [l for l in lines if any(k in l.lower() for k in institution_kw)
                            and any(k in l.lower() for k in faculty_kw)]
                    if not uiuc:
                        time.sleep(0.2)
                        continue
                    current = [l for l in uiuc if l.rstrip().endswith(" to") or "to present" in l.lower()]
                    raw_title = (current or uiuc)[0].split(",")[0].strip()
                    if not any(k in raw_title.lower() for k in faculty_kw):
                        time.sleep(0.2)
                        continue
                    email = person.get(email_field, "").strip()
                    rank = self.parse_rank(raw_title)
                    first, last = self.parse_name(name_field_val)
                    seen_names.add(name_field_val)
                    results.append({
                        "name": name_field_val,
                        "first_name": first,
                        "last_name": last,
                        "original_title": raw_title,
                        "department": dept_label,
                        "area": area,
                        "university": self.config["full_name"],
                        "email": email,
                        "rank": rank,
                    })
                    found += 1
                except Exception:
                    pass
                time.sleep(0.2)
            print(f"  → {found} additional faculty recovered via profile scraping")

        print(f"  → {len(results)} faculty total")
        return results

    def _scrape_slug(self) -> list[dict]:
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
