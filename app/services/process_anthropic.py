from typing import Optional
from ..scrapers.anthropic import AnthropicScraper
from ..database.repository import Repository
from .base import BaseProcessService


class AnthropicMarkdownProcessor(BaseProcessService):
    def __init__(self):
        super().__init__()
        self.scraper = AnthropicScraper()
        self.repo = Repository()

    def get_items_to_process(self, limit: Optional[int] = None) -> list:
        return self.repo.get_anthropic_articles_without_markdown(limit=limit)

    def process_item(self, item) -> Optional[str]:
        return self.scraper.url_to_markdown(item.url)

    def save_result(self, item, result: str) -> bool:
        return self.repo.update_anthropic_article_markdown(item.guid, result)


def process_anthropic_markdown(limit: Optional[int] = None) -> dict:
    processor = AnthropicMarkdownProcessor()
    return processor.process(limit=limit)


if __name__ == "__main__":
    result = process_anthropic_markdown()
    print(f"Total articles: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")
