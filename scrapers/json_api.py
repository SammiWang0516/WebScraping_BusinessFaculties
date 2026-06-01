import html
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
        if self.config.get("wp_rest_acf_url"):
            return self._scrape_wp_rest_acf()
        if self.config.get("wp_rest_url"):
            return self._scrape_wp_rest()
        if self.config.get("static_json_url"):
            return self._scrape_static_json()
        return self._scrape_slug()

    # ------------------------------------------------------------------
    # Static JSON file mode — single JSON URL with items array (e.g. Miami Herbert)
    # Config keys: static_json_url, static_json_items_key (default "items"),
    #              taxonomy_dept_key (reads item["taxonomy"][key]),
    #              dept_area_map (dict: dept_name → area),
    #              exclude_if_title_contains
    # ------------------------------------------------------------------
    def _scrape_static_json(self) -> list[dict]:
        url = self.config["static_json_url"]
        items_key = self.config.get("static_json_items_key", "items")
        taxonomy_dept_key = self.config.get("taxonomy_dept_key")
        dept_area_map = self.config.get("dept_area_map", {})
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items = data[items_key] if items_key else data
        items = [i for i in items if isinstance(i, dict)]
        print(f"  Fetched {len(items)} records from JSON feed")

        results = []
        seen_names = set()
        for item in items:
            name = html.unescape(item.get("name", "")).strip()
            if not name or name in seen_names:
                continue
            title = item.get("title", "").strip()
            if not title:
                continue
            if exclude_patterns and any(p in title.lower() for p in exclude_patterns):
                continue

            if taxonomy_dept_key:
                raw_depts = item.get("taxonomy", {}).get(taxonomy_dept_key, [])
            else:
                raw_depts = []

            dept_entries = [(d, dept_area_map.get(d, "")) for d in raw_depts if d]
            dept_entries = [(d, a) for d, a in dept_entries if a]
            if not dept_entries:
                continue

            dept_name = ", ".join(d[0] for d in dept_entries)
            area = ", ".join(dict.fromkeys(d[1] for d in dept_entries))

            rank = self.parse_rank(title)
            first, last = self.parse_name(name)
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

        print(f"  → {len(results)} faculty saved")
        return results

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

    # ------------------------------------------------------------------
    # WordPress REST API mode — paginated JSON endpoint (e.g. BU Questrom)
    # Config keys: wp_rest_url, wp_rest_params, dept_area_map (dict: str(dept_id) → {name, area})
    # ------------------------------------------------------------------
    def _scrape_wp_rest(self) -> list[dict]:
        base_url = self.config["wp_rest_url"]
        params = dict(self.config.get("wp_rest_params", {}))
        dept_id_map = {int(k): v for k, v in self.config.get("dept_area_map", {}).items()}
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        results = []
        seen_names = set()
        page = 1
        total_pages = None

        while True:
            params["page"] = page
            try:
                resp = requests.get(base_url, params=params, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                if total_pages is None:
                    total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
                    print(f"  API: {resp.headers.get('X-WP-Total')} profiles across {total_pages} pages")
                data = resp.json()
            except Exception as e:
                print(f"    ERROR page {page}: {e}")
                break

            for item in data:
                name = item.get("title", {}).get("rendered", "").strip()
                if not name:
                    continue

                meta = item.get("meta", {})
                raw_pos = meta.get("position") or []
                if isinstance(raw_pos, str):
                    raw_pos = [raw_pos] if raw_pos else []
                # Find the first position containing a faculty rank keyword for rank parsing;
                # honorific/admin titles (e.g. "Dean's Research Scholar") often come first
                rank_kws = ("professor", "lecturer", "instructor", "visiting", "adjunct", "emeritus")
                rank_title = next((p for p in raw_pos if any(kw in p.lower() for kw in rank_kws)), raw_pos[0] if raw_pos else "")
                title = rank_title.strip()
                original_title = " | ".join(p.strip() for p in raw_pos if p.strip())
                email = (meta.get("email") or "").strip()

                if exclude_patterns and original_title and any(p in original_title.lower() for p in exclude_patterns):
                    continue

                dept_ids = item.get("faculty-departments", [])
                dept_name = ", ".join(dept_id_map[d]["name"] for d in dept_ids if d in dept_id_map)
                area = ", ".join(dict.fromkeys(dept_id_map[d]["area"] for d in dept_ids if d in dept_id_map))

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
                    "original_title": original_title,
                    "department": dept_name,
                    "area": area,
                    "university": self.config["full_name"],
                    "email": email,
                    "rank": rank,
                })

            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)

        print(f"  → {len(results)} faculty saved")
        return results

    # ------------------------------------------------------------------
    # WordPress REST API with ACF fields — e.g. Georgia Terry
    # Config keys: wp_rest_acf_url, wp_rest_params,
    #              dept_area_map (dict: str(group_id) → {name, area}),
    #              exclude_if_title_contains
    # ------------------------------------------------------------------
    def _scrape_wp_rest_acf(self) -> list[dict]:
        base_url = self.config["wp_rest_acf_url"]
        params = dict(self.config.get("wp_rest_params", {}))
        dept_id_map = {int(k): v for k, v in self.config.get("dept_area_map", {}).items()}
        exclude_patterns = [p.lower() for p in self.config.get("exclude_if_title_contains", [])]

        results = []
        seen_names = set()
        page = 1
        total_pages = None

        while True:
            params["page"] = page
            try:
                resp = requests.get(base_url, params=params, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                if total_pages is None:
                    total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
                    print(f"  API: {resp.headers.get('X-WP-Total')} profiles across {total_pages} pages")
                data = resp.json()
            except Exception as e:
                print(f"    ERROR page {page}: {e}")
                break

            for item in data:
                group_ids = item.get("group", [])
                dept_entries = [(dept_id_map[g]["name"], dept_id_map[g]["area"])
                                for g in group_ids if g in dept_id_map]
                if not dept_entries:
                    continue

                name = html.unescape(item.get("title", {}).get("rendered", "")).strip()
                if not name:
                    continue

                acf = item.get("acf", {})
                email = (acf.get("email") or "").strip()

                job_titles = acf.get("job_titles") or []
                titles = list(dict.fromkeys(
                    jt["position"]["title"].strip()
                    for jt in job_titles
                    if jt.get("position", {}).get("title")
                ))
                title = titles[0] if titles else ""
                original_title = " | ".join(titles)

                if not title:
                    continue
                if exclude_patterns and any(p in original_title.lower() for p in exclude_patterns):
                    continue

                dept_name = ", ".join(dict.fromkeys(d[0] for d in dept_entries))
                area = ", ".join(dict.fromkeys(d[1] for d in dept_entries))

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
                    "original_title": original_title,
                    "department": dept_name,
                    "area": area,
                    "university": self.config["full_name"],
                    "email": email,
                    "rank": rank,
                })

            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)

        print(f"  → {len(results)} faculty saved")
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
