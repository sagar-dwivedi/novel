from .base_scraper import BaseScraper
from .libread import LibReadScraper


class ScraperFactory:
    @staticmethod
    def create_scraper(website: str) -> BaseScraper:
        scrapers = {
            "libread": LibReadScraper,
        }
        scraper_class = scrapers.get(website)
        if scraper_class:
            return scraper_class()
        else:
            raise ValueError(f"No scraper found for website: {website}")
