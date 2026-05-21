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
        if "emeritus" in t or "emerita" in t:
            return "Emeritus"
        # adjunct/visiting must be checked before assistant/associate/professor
        # so "Adjunct Assistant Professor" → Adjunct, not Assistant
        if "adjunct" in t:
            return "Adjunct"
        if "visiting" in t:
            return "Visiting"
        if "clinical" in t and "professor" in t:
            return "Clinical Professor"
        if "professor of the practice" in t or "professor of practice" in t or "practice professor" in t:
            return "Professor of Practice"
        if "assistant professor" in t:
            return "Assistant"
        if "associate professor" in t:
            return "Associate"
        if "senior lecturer" in t:
            return "Senior Lecturer"
        if "lecturer" in t:
            return "Lecturer"
        if "professor" in t:
            return "Professor"
        if "dean" in t:
            return "Dean"
        return "Other"
