import logging
from typing import Optional
from ..agent.digest import DigestAgent, DigestOutput
from ..database.repository import Repository
from .base import BaseProcessService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class DigestProcessor(BaseProcessService):
    def __init__(self):
        super().__init__()
        self.agent = DigestAgent()
        self.repo = Repository()

    def get_items_to_process(self, limit: Optional[int] = None) -> list:
        return self.repo.get_articles_without_digest(limit=limit)

    def process_item(self, item: dict) -> Optional[DigestOutput]:
        return self.agent.generate_digest(
            title=item["title"],
            content=item["content"],
            article_type=item["type"]
        )

    def save_result(self, item: dict, result: DigestOutput) -> bool:
        try:
            self.repo.create_digest(
                article_type=item["type"],
                article_id=item["id"],
                url=item["url"],
                title=result.title,
                summary=result.summary,
                published_at=item.get("published_at")
            )
            return True
        except Exception:
            return False

    def _get_item_id(self, item: dict) -> str:
        return f"{item['type']}:{item['id']}"

    def _get_item_title(self, item: dict) -> str:
        return item["title"]


def process_digests(limit: Optional[int] = None) -> dict:
    processor = DigestProcessor()
    return processor.process(limit=limit)


if __name__ == "__main__":
    result = process_digests()
    print(f"Total articles: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")
