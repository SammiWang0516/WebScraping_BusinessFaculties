from .static_bs4 import StaticBS4Scraper

SCRAPER_REGISTRY = {
    "static_bs4": StaticBS4Scraper,
}


def get_scraper(university_config: dict):
    scraper_type = university_config.get("scraper_type")
    cls = SCRAPER_REGISTRY.get(scraper_type)
    if cls is None:
        raise ValueError(f"Unknown scraper_type '{scraper_type}'. Available: {list(SCRAPER_REGISTRY)}")
    return cls(university_config)
