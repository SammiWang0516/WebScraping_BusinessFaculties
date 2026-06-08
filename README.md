# Business School Faculty Scraper

Scrapes faculty data from the top ~50 US business schools and compiles it into a structured dataset for research purposes. Each faculty record includes name, title, department, research area, rank, and email — designed to be enriched with Scopus Author IDs as a post-processing step.

## Project Structure

```
.
├── main.py                  # Full pipeline: scrape → merge → enrich
├── scrape.py                # Stage 1 — scrapes university websites → output CSVs
├── merge.py                 # Stage 2 — fills Scopus IDs from the 2025 reference sheet
├── enrich.py                # Stage 3 — calls Scopus API for remaining missing IDs
├── compare.py               # Stage 4 — cross-year comparison → 2026_master.xlsx
│
├── config/
│   └── universities.json    # University metadata, department URLs, and CSS selectors
│
├── scrapers/
│   ├── __init__.py          # Scraper registry (maps scraper_type → class)
│   ├── base.py              # Shared logic: name parsing, rank parsing
│   ├── static_bs4.py        # Static HTML pages (requests + BeautifulSoup)
│   ├── static_dl.py         # Static HTML pages using definition list structure (e.g. MIT Sloan)
│   ├── selenium_bs4.py      # JavaScript-rendered pages (Selenium + BeautifulSoup)
│   ├── selenium_stealth.py  # Cloudflare-protected pages (undetected-chromedriver)
│   └── json_api.py          # JSON or HTML API endpoints (e.g. Duke, Illinois, Boston College)
│
├── debug/                   # One-off debugging scripts used during scraper development
│   ├── debug_columbia.py
│   ├── debug_indiana.py
│   ├── debug_mit.py
│   ├── debug_nyu.py
│   └── debug_usc.py
│
├── output/                  # Generated CSVs (one per university) + 2026_master.xlsx
├── old/                     # Original per-university scripts from 2025 (reference only)
├── requirements.txt
└── README.md
```

## Setup

**1. Create and activate the virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate       # Mac/Linux
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Make sure Google Chrome is installed.** Six universities use Selenium-based scrapers that require a real Chrome browser. `webdriver-manager` downloads a matching ChromeDriver automatically, but Chrome itself must already be on the machine.

**4. Add your Scopus API key to the venv activation script** so it loads automatically:
```bash
echo 'export SCOPUS_API_KEY=your_key_here' >> .venv/bin/activate
```
Get a key at dev.elsevier.com using your institutional account. Always activate the venv before running any script — the API key is set at activation time.

> **Quota note:** The Scopus Author Search API allows 5,000 calls per week. A full run across all 49 universities typically uses 4,000–6,000 calls (depending on how many faculty already have IDs from the merge step). If you hit the quota mid-run, the script stops and prints a resume command. You can either wait for the weekly reset or register a second API key and swap it in.

## Usage

**Full pipeline** (scrape + merge + enrich) for one or more universities:
```bash
python main.py --index 01
python main.py --index 01 02
python main.py                   # all configured universities
```

**Individual stages** (when you need to re-run just one step):
```bash
python scrape.py --index 01      # re-scrape if website changed
python merge.py  --index 01      # re-run after updating the reference Excel sheet
python enrich.py --index 01      # re-run if API quota was hit earlier
python enrich.py --verify        # deeper multi-pass Scopus search for unresolved rows
python compare.py                # rebuild 2026_master.xlsx (combine + verify_ID sheets)
```

## Pipeline Stages

### Stage 1 — `scrape.py`
Reads `config/universities.json`, launches the right scraper for each university, and saves a CSV to `output/`. Each row is one faculty member with these columns:

| Column | Description |
|---|---|
| `name` | Full name as listed on the university website |
| `first_name` | First word of the name |
| `last_name` | Last word of the name (middle initials dropped) |
| `original_title` | Raw title string from the university website |
| `department` | Department name as listed on the university website |
| `area` | Mapped research area (standardized category) |
| `university` | Full university name |
| `email` | Faculty email (if publicly listed) |
| `rank` | Parsed rank — all ranks retained (see rank list below) |

**Ranks captured:** Adjunct, Assistant, Associate, Clinical Professor, Dean, Emeritus, Lecturer, Other, Professor, Professor of Practice, Senior Lecturer, Teaching Professor, Visiting

### Stage 2 — `merge.py`
Matches scraped faculty against the 2025 reference Excel sheet by name and copies over existing Scopus Author IDs. Covers ~90% of returning faculty automatically. Flags fuzzy matches for manual review.

### Stage 3 — `enrich.py`
Calls the Scopus Author Search API for faculty still missing an ID after the merge step. Auto-fills unambiguous matches, flags multiple candidates for manual review, and reports faculty not found in Scopus (typically new hires or non-publishing practitioners).

After the script finishes, check the terminal output for any **"Multiple candidates"** blocks. These are faculty where Scopus returned more than one result — the script prints all candidates with their IDs and affiliations and leaves the `scopus_id` field blank in the CSV. Open the CSV for that university and fill in the correct ID by hand (verify against the affiliation).

After all three stages, the CSV gains a `scopus_id` column as the first field.

**`--verify` mode** (`python enrich.py --verify`): runs a deeper multi-pass search against the `verify_ID` sheet in `2026_master.xlsx` for any rows still missing a confirmed ID. Unlike the per-university pass (single query per person), verify mode tries up to four fallback strategies per faculty member: standard query, adding a subject-area filter, alternate first-name spellings, and a no-affiliation fallback using subject area alone. Use this after running `compare.py` if you want to recover additional IDs for new hires. Requires ~5,000 API quota calls for a full run (~800 rows).

### Stage 4 — `compare.py`
Cross-year analysis script. Reads the 2025 reference Excel sheet and all 2026 CSVs, then writes `output/2026_master.xlsx` with two analysis sheets:

**`combine` sheet** — one row per tenure-track faculty member (Professor / Associate / Assistant) in either year, with columns:

| Column | Description |
|---|---|
| `ScopusAuthorID` | Scopus ID extracted from the 2025 reference sheet only. Blank if the person was not in 2025 or had no ID in the 2025 data. |
| `SuggestID` | Scopus ID from the 2026 enrichment pipeline or `--verify` run. Populated only for new hires (faculty not present in 2025). Blank for returning faculty. |
| `Full Name` | Display name |
| `Original Title` | Raw title string from the source |
| `University` | University name |
| `Original Area` | Research area |
| `First Name` / `Last Name` | Parsed name components |
| `2025 Rank` | Rank from the 2025 reference sheet (blank for new hires) |
| `2026 Rank` | Rank from the 2026 scrape (blank if not found in 2026) |
| `Status` | `Active`, `Promoted`, `Demoted`, `New hire`, `Retired (Emeritus)`, `Moved to [University]`, `Unknown / Dismissed` |

**`verify_ID` sheet** — subset of combine rows that need ID verification:
- Returning faculty whose 2025 record had no Scopus ID
- All new hires (SuggestID present but unconfirmed, or blank)

## Adding a New University

1. Add an entry to `config/universities.json` with the appropriate `scraper_type`.
2. If the site needs a new scraping strategy, add a class in `scrapers/` that extends `BaseScraper` and register it in `scrapers/__init__.py`.

### Available scraper types

| Type | Use case |
|---|---|
| `static_bs4` | Static HTML, one URL per department (e.g. UPenn Wharton, UT Austin McCombs) |
| `static_dl` | Static HTML using `<dt>`/`<dd>` definition list structure (e.g. MIT Sloan) |
| `selenium_bs4` | JavaScript-rendered pages — headless Chrome, multiple modes (see below) |
| `selenium_stealth` | Cloudflare-protected pages — undetected-chromedriver required (e.g. Columbia) |
| `json_api` | JSON or HTML endpoints served by the university's backend — multiple modes (see below) |

### `selenium_bs4` modes

The mode is selected automatically based on which keys are present in the config entry (checked in this priority order):

| Keys present | Mode | Description |
|---|---|---|
| `url` + `total_pages` | Paginated | Loops over `?page=0..N`, reads dept from a card element (e.g. NYU Stern) |
| `url` + `dept_select` in selectors | Select-dept | Selects each dept from a `<select>` dropdown, scrapes results (e.g. Indiana Kelley, Berkeley Haas) |
| `url` + `table_row_xpath` in selectors | Table-status | JS-rendered table filtered by a status column; names are in "Last, First" format (e.g. Georgia Tech Scheller) |
| `url` + `filter_group_prefix` | Checkbox-dept | Clicks a group checkbox + Apply button per dept; expands collapsed filter panel automatically (e.g. Northeastern D'Amore-McKim) |
| `url` only | Single URL | One page, dept inferred by keyword-matching title text. Optional: `facetwp_next_css` (FacetWP pagination), `load_more_btn_text` (load-more button), `scroll_count` (infinite scroll) (e.g. USC Marshall, UT Dallas) |
| Neither | Per-dept | One request per dept URL in config, dept assigned from config. Optional: `next_page_btn_aria` enables button-click pagination through pages (e.g. Harvard HBS, ASU W.P. Carey) |

### `json_api` modes

The mode is selected automatically based on which keys are present in the config entry:

| Keys present | Mode | Description |
|---|---|---|
| `aem_items_url` | AEM items | Fetches a single static HTML endpoint served by Adobe Experience Manager (e.g. Boston College) |
| `bulk_api_url` | Bulk API | Single API call returns all faculty; uses `dept_area_map` to classify by department (e.g. Illinois) |
| `api_base` | Slug | Per-dept JSON endpoints built from `api_base` + department slug (e.g. Duke Fuqua) |

### Config entry formats

**Static HTML, one URL per department** (`static_bs4`):
```json
{
  "index": "01",
  "name": "University Name",
  "school": "School of Business",
  "full_name": "University Name",
  "scraper_type": "static_bs4",
  "departments": [
    { "name": "Finance Department", "url": "https://...", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "li.css-class",
    "name": "strong",
    "email_link_class": "email-class"
  }
}
```

**Static HTML, definition list structure** (`static_dl`):
```json
{
  "index": "07",
  "name": "Massachusetts Institute of Technology",
  "school": "MIT Sloan School of Management",
  "full_name": "Massachusetts Institute of Technology",
  "scraper_type": "static_dl",
  "url": "https://mitsloan.mit.edu/faculty/faculty-directory",
  "departments": [
    { "name": "Finance", "area": "Finance" },
    {
      "name": "Operations Research and Statistics",
      "area": "Business Analytics, Decision Science and Stats",
      "match_aliases": ["operations research", "management science", "professor of statistics"]
    }
  ]
}
```

Names on the MIT page are stored as "Last, First" — the scraper automatically reverses them to "First Last".

**JavaScript-rendered, single URL** (`selenium_bs4`, single URL mode):
```json
{
  "index": "06",
  "name": "University of Southern California",
  "school": "Marshall School of Business",
  "full_name": "University of Southern California",
  "scraper_type": "selenium_bs4",
  "url": "https://www.marshall.usc.edu/faculty-research/faculty-directory",
  "departments": [
    { "name": "Accounting", "area": "Accounting" },
    {
      "name": "Data Sciences and Operations",
      "area": "Business Analytics, Decision Science and Stats",
      "match_aliases": ["data science and operations", "information and operations management"]
    }
  ],
  "selectors": {
    "faculty_card": "li.person-list-item",
    "name": "h3.title",
    "title": "ul.position-list li"
  }
}
```

Department is inferred by keyword-matching the faculty member's title text against each department's `name` and `match_aliases` list.

**JavaScript-rendered, per-dept URLs** (`selenium_bs4`, per-dept mode):
```json
{
  "index": "04",
  "name": "Harvard University",
  "school": "Harvard Business School",
  "full_name": "Harvard University",
  "scraper_type": "selenium_bs4",
  "departments": [
    { "name": "Finance", "url": "https://www.hbs.edu/faculty/units/finance/Pages/faculty.aspx", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "div.media",
    "name": "h2 a",
    "title": "div.nu"
  }
}
```

**JavaScript-rendered, per-dept URLs with button-click pagination** (`selenium_bs4`, per-dept + `next_page_btn_aria`):
```json
{
  "index": "23",
  "name": "Arizona State University",
  "school": "W.P. Carey School of Business",
  "full_name": "Arizona State University",
  "scraper_type": "selenium_bs4",
  "next_page_btn_aria": "Next Page",
  "departments": [
    { "name": "Finance", "url": "https://wpcarey.asu.edu/people/departments/finance", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "div.person",
    "name": "a",
    "title": "div.person-profession h4"
  }
}
```

**JavaScript-rendered, checkbox + apply button filter per dept** (`selenium_bs4`, checkbox-dept mode):
```json
{
  "index": "51",
  "name": "Northeastern University",
  "school": "D'Amore-McKim School of Business",
  "full_name": "Northeastern University (D'Amore-McKim School of Business)",
  "scraper_type": "selenium_bs4",
  "url": "https://damore-mckim.northeastern.edu/people/",
  "filter_group_prefix": "person|group|",
  "filter_apply_css": "button.button-red.filter-button",
  "departments": [
    { "name": "Accounting", "filter_value": "accounting", "area": "Accounting" },
    { "name": "Finance", "filter_value": "finance", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "div.person-line-content",
    "name": "h3 a",
    "title": "div.person-line-role-category",
    "pagination_next_css": "span.page-numbers.current + a.page-numbers"
  }
}
```

Each dept's `filter_value` is appended to `filter_group_prefix` to form the checkbox input `value` attribute. The scraper expands the filter panel (if collapsed via a toggle button), clicks the checkbox via JS, clicks Apply, and follows pagination — then resets before the next dept.

**JSON API, bulk mode** (`json_api`, bulk mode — e.g. Illinois Gies):
```json
{
  "index": "26",
  "name": "University of Illinois at Urbana-Champaign",
  "school": "Gies College of Business",
  "full_name": "University of Illinois at Urbana-Champaign",
  "scraper_type": "json_api",
  "bulk_api_url": "https://facultysearchapi.example.edu/api/Search",
  "bulk_api_params": { "q": "", "collegeType": "business", "take": 999 },
  "bulk_api_items_key": "items",
  "field_map": {
    "name": "fullnamefirst", "title": "title", "email": "email",
    "dept_field": "department", "unit_field": "unit", "bio_field": "biography"
  },
  "keep_if_title_contains": ["professor", "lecturer", "instructor"],
  "exclude_departments": ["Office of the Dean", "IT Partners"],
  "dept_area_map": [
    { "dept": "Accountancy", "label": "Accountancy", "area": "Accounting" },
    { "dept": "Finance", "label": "Finance", "area": "Finance" }
  ]
}
```

**AEM items HTML endpoint** (`json_api`, AEM items mode — e.g. Boston College):
```json
{
  "index": "27",
  "name": "Boston College",
  "school": "Carroll School of Management",
  "full_name": "Boston College",
  "scraper_type": "json_api",
  "aem_items_url": "https://www.bc.edu/.../faculty-list.items.html?displayCount=200",
  "dept_area_map": {
    "Finance": "Finance",
    "Accounting": "Accounting",
    "Management and Organization": "Management"
  }
}
```

The AEM items URL is found by opening the faculty page in Chrome DevTools → Network → Fetch/XHR and looking for a `*.items.html` request. Setting `displayCount` to a large number returns all faculty in one call.

## Research Areas

Standardized area labels used in the `area` column. Older config entries may use slightly different strings; a full normalization pass is planned.

```
Accounting                                    Information Systems
Business Analytics, Decision Science & Stats  Management Organizations (Org. Behavior)
Business Communication                        Marketing
Business Econ and Policy                      Operations & Technology
Business Law                                  Other
Entrepreneurship                              Production and Operations
Finance                                       Real Estate
Healthcare                                    Strategy
                                              Supply Chain and Logistics
```

## Scopus Author ID

Scopus IDs are not available on university websites — they are looked up via the [Scopus Author Search API](https://dev.elsevier.com/) (Stage 3) or manually at [scopus.com](https://www.scopus.com). Faculty with no publications in Scopus-indexed venues will not have an ID — this is common for Professors of Practice and Clinical Professors.

A faculty member can also have **multiple Scopus IDs** if their name was indexed inconsistently across papers. When the API returns multiple candidates, always verify by checking the affiliation.

## Universities Covered

49 US business schools, indexed 01–53 (indices 16, 36, 37, 52 are gaps). See `config/universities.json` for the full list.

Tenure-track faculty comparison — 2025 dataset vs. 2026 scrape (tenure = Professor + Associate + Assistant):

| # | University | School | Scraper | 2025 | 2026 | Δ |
|---|---|---|---|---|---|---|
| 01 | UPenn | Wharton | Static HTML | 300 | 304 | +4 |
| 02 | UT Dallas | Jindal | JavaScript | 132 | 141 | +9 |
| 03 | Columbia | CBS | JS + Cloudflare | 137 | 130 | −7 |
| 04 | Harvard | HBS | JavaScript | 199 | 192 | −7 |
| 05 | Chicago | Booth | JavaScript | 151 | 146 | −5 |
| 06 | USC | Marshall | JavaScript | 147 | 145 | −2 |
| 07 | MIT | Sloan | Static HTML | 132 | 133 | +1 |
| 08 | NYU | Stern | JavaScript | 157 | 152 | −5 |
| 09 | Indiana | Kelley | JavaScript | 189 | 196 | +7 |
| 10 | UT Austin | McCombs | Static HTML | 140 | 137 | −3 |
| 11 | Stanford | GSB | JavaScript | 148 | 137 | −11 |
| 12 | Cornell | SC Johnson | Static HTML | 155 | 158 | +3 |
| 13 | Duke | Fuqua | JSON API | 93 | 90 | −3 |
| 14 | U Washington | Foster | Static HTML | 101 | 98 | −3 |
| 15 | WashU | Olin | JavaScript | 91 | 88 | −3 |
| 17 | UNC | Kenan-Flagler | Static HTML | 93 | 86 | −7 |
| 18 | Michigan | Ross | Static HTML | 129 | 114 | −15 |
| 19 | Minnesota | Carlson | Static HTML | 102 | 98 | −4 |
| 20 | Penn State | Smeal | Static HTML | 101 | 105 | +4 |
| 21 | UCLA | Anderson | Static HTML | 88 | 84 | −4 |
| 22 | Northwestern | Kellogg | JavaScript | 167 | 165 | −2 |
| 23 | Arizona State | W.P. Carey | JavaScript | 165 | 171 | +6 |
| 24 | Maryland | Smith | Static HTML | 106 | 102 | −4 |
| 25 | Ohio State | Fisher | Static HTML | 99 | 101 | +2 |
| 26 | Illinois | Gies | JSON API | 133 | 150 | +17 |
| 27 | Boston College | Carroll | AEM HTML | 83 | 81 | −2 |
| 28 | Texas A&M | Mays | Static HTML | 111 | 114 | +3 |
| 29 | Purdue | Daniels | JavaScript | 111 | 117 | +6 |
| 30 | Yale | SOM | Static HTML | 87 | 89 | +2 |
| 31 | Boston University | Questrom | WordPress REST API | 98 | 103 | +5 |
| 32 | Temple | Fox | Static HTML | 72 | 77 | +5 |
| 33 | UC Berkeley | Haas | JavaScript | 108 | 109 | +1 |
| 34 | Florida | Warrington | Static HTML | 83 | 80 | −3 |
| 35 | Emory | Goizueta | Static HTML | 66 | 67 | +1 |
| 38 | Carnegie Mellon | Tepper | Static HTML | 95 | 94 | −1 |
| 39 | Georgia Tech | Scheller | JavaScript | 74 | 72 | −2 |
| 40 | Colorado | Leeds | JavaScript | 88 | 85 | −3 |
| 41 | Notre Dame | Mendoza | Static HTML | 98 | 102 | +4 |
| 42 | Georgia | Terry | JSON API | 118 | 116 | −2 |
| 43 | Wisconsin | Wisconsin SoB | JavaScript | 94 | 96 | +2 |
| 44 | South Carolina | Moore | Static HTML | 107 | 111 | +4 |
| 45 | Connecticut | UConn | Static HTML | 76 | 93 | +17 |
| 46 | Michigan State | Broad | Static HTML | 91 | 94 | +3 |
| 47 | Utah | Eccles | JavaScript | 88 | 76 | −12 |
| 48 | Miami | Herbert | JSON API | 93 | 92 | −1 |
| 49 | Arizona | Eller | Static HTML | 73 | 71 | −2 |
| 50 | UC Irvine | Merage | JavaScript | 51 | 55 | +4 |
| 51 | Northeastern | D'Amore-McKim | JavaScript | 90 | 103 | +13 |
| 53 | Georgetown | McDonough | Static HTML | 85 | 87 | +2 |

**Notes on large differences:**
- **MIT +1** — After fixing a deduplication bug in the `static_dl` scraper (the MIT directory renders faculty in both alphabetical and group sections simultaneously, causing each person to appear 2–3 times), the corrected 2026 count is 133 — essentially flat with 2025.
- **Illinois +17** — The faculty directory API returns 819 people total but only ~90 are tagged as faculty. The scraper recovers the rest by filtering on department, title keywords, biography text, and individual profile pages.
- **Michigan −15** — The 2025 scraper captured more non-tenure-track rows under "Professor" labels. After improved rank filtering, 2026 is tighter.
- **Stanford −11** — Confirmed drop: several senior faculty retired or moved; the 2026 scrape matches the current GSB directory.
- **UConn +17** — The 2025 scraper followed hyperlinks from a single faculty listing page, missing faculty whose profiles were not linked from that page. The 2026 scraper reads each department page directly, giving complete coverage.
- **Northeastern +13** — The 2025 scraper filtered by research "area" checkboxes; the 2026 scraper filters by department "group" checkboxes. The two taxonomies overlap but are not identical, and the group-based filter captures additional faculty not surfaced by the area filter.
- **Utah −12** — The 2025 scraper collected all entries from the Eccles directory without rank filtering, resulting in some non-tenure-track titles being counted as Professor. The 2026 rank parser is stricter, and a handful of genuine departures also contributed to the drop.

2025 counts are tenure-track only (Professor / Associate / Assistant). 2026 counts include the same three ranks; all other ranks (Lecturer, Adjunct, Emeritus, Clinical, Professor of Practice, etc.) are captured separately in the CSV but excluded from this comparison column.
