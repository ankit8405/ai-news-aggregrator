from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence
from abc import ABC, abstractmethod

import certifi
import feedparser
import requests
from pydantic import BaseModel


class Article(BaseModel):
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class BaseScraper(ABC):
    @property
    @abstractmethod
    def rss_urls(self) -> List[str]:
        pass

    def get_articles(self, hours: int = 24) -> Sequence[Article]:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)
        articles = []
        seen_guids = set()

        for rss_url in self.rss_urls:
            try:
                response = requests.get(rss_url, timeout=30, verify=certifi.where())
                response.raise_for_status()
            except Exception as e:
                print(f"  ! failed to fetch {rss_url}: {e}")
                continue

            feed = feedparser.parse(response.content)
            if not feed.entries:
                continue

            for entry in feed.entries:
                published_parsed = getattr(entry, "published_parsed", None)
                if not published_parsed:
                    continue

                published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if published_time >= cutoff_time:
                    guid = entry.get("id", entry.get("link", ""))
                    if guid not in seen_guids:
                        seen_guids.add(guid)
                        articles.append(
                            Article(
                                title=entry.get("title", ""),
                                description=entry.get("description", ""),
                                url=entry.get("link", ""),
                                guid=guid,
                                published_at=published_time,
                                category=entry.get("tags", [{}])[0].get("term")
                                if entry.get("tags")
                                else None,
                            )
                        )

        return articles