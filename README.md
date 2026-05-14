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
│   ├── static_bs4.py        # For static HTML pages (requests + BeautifulSoup)
│   └── selenium_bs4.py      # For JavaScript-rendered pages (Selenium + BeautifulSoup)
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
| `rank` | Parsed rank: Professor / Associate / Assistant / Dean |

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
| `static_bs4` | Static HTML pages — fast, no browser needed |
| `selenium_bs4` | JavaScript-rendered pages — requires Chrome |

### Config entry format

**Static HTML** (`static_bs4`) — one URL per department:
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
    "email_link_class": "email-class",
    "skip_title_keywords": ["Emeritus", "Adjunct", "Visiting", "Lecturer"]
  }
}
```

**JavaScript-rendered** (`selenium_bs4`) — single URL, department inferred from title:
```json
{
  "index": "02",
  "name": "University Name",
  "school": "School of Business",
  "full_name": "University Name (School of Business)",
  "scraper_type": "selenium_bs4",
  "url": "https://...",
  "departments": [
    { "name": "Finance", "area": "Finance" }
  ],
  "selectors": {
    "faculty_card": "div.card-class",
    "name": "h3 a",
    "title": "h4",
    "skip_title_keywords": ["Emeritus", "Adjunct", "Visiting", "of Practice", "Clinical"]
  }
}
```

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

49 US business schools, indexed 01–53 (with gaps). See `config/universities.json` for the full list. Currently scraped: **01** (UPenn), **02** (UT Dallas).
