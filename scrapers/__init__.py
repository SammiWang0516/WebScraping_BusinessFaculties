from .static_bs4 import StaticBS4Scraper
from .selenium_bs4 import SeleniumBS4Scraper
from .selenium_stealth import SeleniumStealthScraper
from .static_dl import StaticDLScraper

SCRAPER_REGISTRY = {
    "static_bs4": StaticBS4Scraper,
    "selenium_bs4": SeleniumBS4Scraper,
    "selenium_stealth": SeleniumStealthScraper,
    "static_dl": StaticDLScraper,
}


def get_scraper(university_config: dict):
    scraper_type = university_config.get("scraper_type")
    cls = SCRAPER_REGISTRY.get(scraper_type)
    if cls is None:
        raise ValueError(f"Unknown scraper_type '{scraper_type}'. Available: {list(SCRAPER_REGISTRY)}")
    return cls(university_config)
