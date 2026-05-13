# Business School Faculty Scraper

Scrapes faculty data from the top ~50 US business schools and compiles it into a structured dataset for research purposes. Each faculty record includes name, title, department, research area, and rank — designed to be enriched with Scopus Author IDs as a post-processing step.

## Project Structure

```
.
├── config/
│   └── universities.json    # University metadata, department URLs, and CSS selectors
├── scrapers/
│   ├── __init__.py          # Scraper registry (maps scraper_type → class)
│   ├── base.py              # Shared logic: name parsing, rank parsing
│   └── static_bs4.py        # Scraper for static HTML pages (requests + BeautifulSoup)
├── output/                  # Generated CSVs, one per university (git-ignored)
├── old/                     # Original per-university scripts from 2025 (reference only)
├── main.py                  # Entry point
└── README.md
```

## Setup

```bash
pip install requests beautifulsoup4
```

For universities that require Selenium (dynamic/JS-heavy pages), also install:
```bash
pip install selenium webdriver-manager
```

## Usage

Scrape all configured universities:
```bash
python main.py
```

Scrape one or more specific universities by index:
```bash
python main.py --index 01
python main.py --index 01 04 11
```

Output CSVs are saved to `output/` as `{index}_{UniversityName}.csv`.

## Output Columns

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

## Adding a New University

1. Add an entry to `config/universities.json` with the appropriate `scraper_type`.
2. If the site requires a new scraping strategy not yet implemented, add a new class in `scrapers/` that extends `BaseScraper`, and register it in `scrapers/__init__.py`.

### Available scraper types

| Type | Use case |
|---|---|
| `static_bs4` | Static HTML pages (requests + BeautifulSoup) |
| `selenium_scroll` | Infinite scroll pages *(coming soon)* |
| `selenium_dropdown` | Dropdown-filtered faculty lists *(coming soon)* |
| `selenium_paginate` | Paginated faculty lists *(coming soon)* |

### Config entry format

```json
{
  "index": "01",
  "name": "University Name",
  "school": "School of Business",
  "full_name": "University Name",
  "scraper_type": "static_bs4",
  "departments": [
    {
      "name": "Department Name",
      "url": "https://dept.university.edu/faculty/",
      "area": "Standardized Area Name"
    }
  ],
  "selectors": {
    "faculty_row": "li.css-class",
    "name": "strong",
    "email_link_class": "email-class",
    "skip_title_keywords": ["Emeritus", "Emerita", "In Memoriam", "Adjunct", "Visiting", "Practice Professor", "Lecturer"]
  }
}
```

## Research Areas (18 categories)

```
Accounting
Business Analytics, Decision Science and Stats
Business Communication
Business Econ and Policy
Business Law
Entrepreneurship
Finance
Healthcare
Information Systems
International
Management Organizations (Organizational Behavior)
Marketing
Nonprofit
Production and Operations
Project Management
Strategy
Real Estate
Supply Chain and Logistics
```

## Scopus Author ID

Scopus IDs are not scraped — they are looked up separately via the [Scopus Author Search API](https://dev.elsevier.com/) or manually at [scopus.com](https://www.scopus.com) and merged into the final dataset. Faculty with no publications in Scopus-indexed venues will not have an ID.

## Universities Covered

49 US business schools, indexed 01–53 (with gaps). See `config/universities.json` for the full list.
