from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
    All scrapers return a list of dicts with these keys:
      name, first_name, last_name, original_title, department, area, university, email
    """

    def __init__(self, university_config: dict):
        self.config = university_config

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def parse_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split()
        if len(parts) == 0:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[-1]

    def parse_rank(self, title: str) -> str:
        t = title.lower()
        if "dean" in t:
            return "Dean"
        if "assistant professor" in t:
            return "Assistant"
        if "associate professor" in t:
            return "Associate"
        if "professor" in t:
            return "Professor"
        return "Other"
