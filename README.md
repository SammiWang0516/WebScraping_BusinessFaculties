# Business School Faculty Scraper

Scrapes faculty data from the top ~50 US business schools and compiles it into a structured dataset for research purposes. Each faculty record includes name, title, department, research area, rank, and email — designed to be enriched with Scopus Author IDs as a post-processing step.

## Project Structure

```
.
├── main.py                  # Full pipeline: scrape → merge → enrich
├── scrape.py                # Stage 1 — scrapes university websites → output CSVs
├── merge.py                 # Stage 2 — fills Scopus IDs from the 2025 reference sheet
├── enrich.py                # Stage 3 — calls Scopus API for remaining missing IDs
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
│   └── selenium_stealth.py  # Cloudflare-protected pages (undetected-chromedriver)
│
├── output/                  # Generated CSVs, one per university (git-ignored)
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

**3. Add your Scopus API key to the venv activation script** so it loads automatically:
```bash
echo 'export SCOPUS_API_KEY=your_key_here' >> .venv/bin/activate
```
Get a key at dev.elsevier.com using your institutional account. Always activate the venv before running any script — the API key is set at activation time.

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
| `area` | Mapped research area (one of 18 standardized categories) |
| `university` | Full university name |
| `email` | Faculty email (if publicly listed) |
| `rank` | Parsed rank — all ranks retained (see rank list below) |

**Ranks captured:** Adjunct, Assistant Professor, Associate Professor, Clinical Professor, Dean, Emeritus Professor, Lecturer, Other, Professor, Professor of Practice, Senior Lecturer, Visiting Professor

### Stage 2 — `merge.py`
Matches scraped faculty against the 2025 reference Excel sheet by name and copies over existing Scopus Author IDs. Covers ~90% of returning faculty automatically. Flags fuzzy matches for manual review.

### Stage 3 — `enrich.py`
Calls the Scopus Author Search API for faculty still missing an ID after the merge step. Auto-fills unambiguous matches, flags multiple candidates for manual review, and reports faculty not found in Scopus (typically new hires or non-publishing practitioners).

After all three stages, the CSV gains a `scopus_id` column as the first field.

## Adding a New University

1. Add an entry to `config/universities.json` with the appropriate `scraper_type`.
2. If the site needs a new scraping strategy, add a class in `scrapers/` that extends `BaseScraper` and register it in `scrapers/__init__.py`.

### Available scraper types

| Type | Use case |
|---|---|
| `static_bs4` | Static HTML, one URL per department (e.g. UPenn Wharton) |
| `static_dl` | Static HTML using `<dt>`/`<dd>` definition list structure (e.g. MIT Sloan) |
| `selenium_bs4` | JavaScript-rendered pages — headless Chrome, three modes (see below) |
| `selenium_stealth` | Cloudflare-protected pages — undetected-chromedriver required (e.g. Columbia) |

### `selenium_bs4` modes

The mode is selected automatically based on which keys are present in the config entry:

| Keys present | Mode | Description |
|---|---|---|
| `url` + `total_pages` | Paginated | Loops over `?page=0..N`, reads dept from a card element (e.g. NYU Stern) |
| `url` only | Single URL | Loads one page, infers dept from keyword matching against title text (e.g. USC, UT Dallas) |
| Neither | Per-dept | One request per department URL in config, dept assigned from config (e.g. Harvard, Chicago Booth) |

### Config entry formats

**Static HTML, one URL per department** (`static_bs4`):
```json
{
  "index": "01",
  "name": "University Name",
  "school": "School of Business",
  "full_name": "University Name (School of Business)",
  "scraper_type": "static_bs4",
  "departments": [
    { "name": "Finance Department", "url": "https://...", "area": "Finance" }
  ],
  "selectors": {
    "faculty_row": "li.css-class",
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
  "full_name": "Massachusetts Institute of Technology (MIT Sloan School of Management)",
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
  "full_name": "University of Southern California (Marshall School of Business)",
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

Department is inferred by keyword-matching the faculty member's title text against each department's `name` and `match_aliases` list. Use `match_aliases` when the text on the site uses different phrasing than the canonical department name.

**JavaScript-rendered, per-dept URLs** (`selenium_bs4`, per-dept mode):
```json
{
  "index": "04",
  "name": "Harvard University",
  "school": "Harvard Business School",
  "full_name": "Harvard University (Harvard Business School)",
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

**JavaScript-rendered, paginated** (`selenium_bs4`, paginated mode):
```json
{
  "index": "08",
  "name": "New York University",
  "school": "Stern School of Business",
  "full_name": "New York University (Stern School of Business)",
  "scraper_type": "selenium_bs4",
  "url": "https://www.stern.nyu.edu/faculty",
  "total_pages": 25,
  "departments": [
    { "name": "Finance", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "div.shadow-share",
    "name": "h2",
    "title": "p.italic",
    "dept_text": "p.text-emperor:not(.italic)"
  }
}
```

The `dept_text` selector reads the department name directly from the card element instead of inferring it from title keywords. The scraper strips a trailing " Department" suffix and looks up the area from the department list.

## Research Areas (18 standardized categories)

```
Accounting                                    Information Systems
Business Analytics, Decision Science & Stats  International
Business Communication                        Management Organizations (Org. Behavior)
Business Econ and Policy                      Marketing
Business Law                                  Nonprofit
Entrepreneurship                              Production and Operations
Finance                                       Project Management
Healthcare                                    Real Estate
                                              Strategy
                                              Supply Chain and Logistics
```

## Scopus Author ID

Scopus IDs are not available on university websites — they are looked up via the [Scopus Author Search API](https://dev.elsevier.com/) (Stage 3) or manually at [scopus.com](https://www.scopus.com). Faculty with no publications in Scopus-indexed venues will not have an ID — this is common for Professors of Practice and Clinical Professors.

A faculty member can also have **multiple Scopus IDs** if their name was indexed inconsistently across papers. When the API returns multiple candidates, always verify by checking the affiliation.

## Universities Covered

49 US business schools, indexed 01–53 (with gaps). See `config/universities.json` for the full list.

Currently scraped (tenure-track faculty comparison — 2025 dataset vs. 2026 scrape):

| # | University | Page Type | 2025 | 2026 | Δ |
|---|---|---|---|---|---|
| 01 | UPenn Wharton | Static HTML, one URL per dept | 300 | 304 | +4 |
| 02 | UT Dallas Jindal | JavaScript, single page | 132 | 192 | +60 |
| 03 | Columbia CBS | JavaScript + Cloudflare | 137 | 139 | +2 |
| 04 | Harvard HBS | JavaScript, one URL per dept | 199 | 192 | −7 |
| 05 | Chicago Booth | JavaScript, one URL per dept | 151 | 152 | +1 |
| 06 | USC Marshall | JavaScript, single page | 147 | 145 | −2 |
| 07 | MIT Sloan | Static HTML, definition list | 132 | 278 | +146 |
| 08 | NYU Stern | JavaScript, paginated | 157 | 172 | +15 |
| 09 | Indiana Kelley | JavaScript, dropdown filter | 189 | 212 | +23 |
| 10 | UT Austin McCombs | Static HTML, single page | 140 | 209 | +69 |

**Notes on large differences:**
- **MIT +146** — 2025 scraped individual group pages and missed research center affiliates. 2026 uses the main directory.
- **UT Austin +69** — 2025 script was incomplete (single department, one page). 2026 captures the full directory.
- **UT Dallas +60** — School has been actively expanding. Every department grew.

2025 counts are tenure-track only (Professor / Associate Professor / Assistant Professor). 2026 counts include the same three ranks; all other ranks (Lecturer, Adjunct, Emeritus, Clinical, etc.) are captured separately in the CSV but excluded from this comparison.
