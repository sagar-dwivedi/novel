from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

import httpx


@dataclass
class NovelMetadata:
    title: str
    author: str
    description: str
    cover_url: str
    source_url: str
    slug: str


@dataclass
class ChapterMetadata:
    title: str
    url: str
    chapter_number: int


class BaseScraper(ABC):
    def __init__(self):
        self.session: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(follow_redirects=True)
        return self.session

    async def close_client(self) -> None:
        if self.session:
            await self.session.aclose()
            self.session = None

    async def __aenter__(self) -> Self:
        """Context manager support"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager support"""
        await self.close_client()

    async def fetch_html(self, url: str) -> str | None:
        client = await self.get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    @abstractmethod
    async def scrape_metadata(self, url: str) -> NovelMetadata:
        """Scrape novel metadata from the main novel page"""
        ...

    @abstractmethod
    async def get_chapter_list(self, url: str) -> list[ChapterMetadata]:
        """Get list of all chapters for a novel"""
        ...

    @abstractmethod
    async def scrape_chapter(self, chapter_url: str) -> str:
        """Scrape chapter content and return as text"""
        ...

    @staticmethod
    def get_scraper_for_url(url: str) -> str:
        """Factory method to determine which scraper to use"""
        if "libread.com" in url:
            return "libread"
        # Add more sites here
        # elif "example.com" in url:
        #     return "example"
        return "base"
