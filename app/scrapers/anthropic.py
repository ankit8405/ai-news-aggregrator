import requests
from typing import List, Optional, Sequence
from html_to_markdown import convert
from .base import BaseScraper, Article


class AnthropicArticle(Article):
    pass


class AnthropicScraper(BaseScraper):
    @property
    def rss_urls(self) -> List[str]:
        return [
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        ]

    def get_articles(self, hours: int = 24) -> Sequence[AnthropicArticle]:
        return [
            AnthropicArticle(**article.model_dump())
            for article in super().get_articles(hours)
        ]

    def url_to_markdown(self, url: str) -> Optional[str]:
        try:
            response = requests.get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
            )
            response.raise_for_status()
            html = response.text
            return convert(html).content
        except Exception:
            return None


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles: Sequence[AnthropicArticle] = scraper.get_articles(hours=100)
    markdown: Optional[str] = scraper.url_to_markdown(articles[1].url)
    print(markdown)