from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseProcessService(ABC):
    def __init__(self):
        self.logger = logger

    @abstractmethod
    def process_item(self, item: Any) -> Optional[Any]:
        pass

    @abstractmethod
    def get_items_to_process(self, limit: Optional[int] = None) -> list:
        pass

    @abstractmethod
    def save_result(self, item: Any, result: Any) -> bool:
        pass

    def process(self, limit: Optional[int] = None) -> Dict[str, Any]:
        items = self.get_items_to_process(limit=limit)
        total = len(items)
        processed = 0
        failed = 0

        self.logger.info(f"Starting processing for {total} items")

        for idx, item in enumerate(items, 1):
            item_id = self._get_item_id(item)
            item_title = self._get_item_title(item)
            display_title = item_title[:60] + "..." if len(item_title) > 60 else item_title

            self.logger.info(f"[{idx}/{total}] Processing {display_title} (ID: {item_id})")

            try:
                result = self.process_item(item)
                if result:
                    if self.save_result(item, result):
                        processed += 1
                        self.logger.info(f"✓ Successfully processed {item_id}")
                    else:
                        failed += 1
                        self.logger.warning(f"✗ Failed to save result for {item_id}")
                else:
                    failed += 1
                    self.logger.warning(f"✗ Failed to process {item_id}")
            except Exception as e:
                failed += 1
                self.logger.error(f"✗ Error processing {item_id}: {e}")

        self.logger.info(f"Processing complete: {processed} processed, {failed} failed out of {total} total")

        return {
            "total": total,
            "processed": processed,
            "failed": failed
        }

    def _get_item_id(self, item: Any) -> str:
        if hasattr(item, "id"):
            return str(item.id)
        if hasattr(item, "guid"):
            return str(item.guid)
        if hasattr(item, "video_id"):
            return str(item.video_id)
        if isinstance(item, dict):
            return str(item.get("id", item.get("guid", item.get("video_id", "unknown"))))
        return "unknown"

    def _get_item_title(self, item: Any) -> str:
        if hasattr(item, "title"):
            return str(item.title)
        if isinstance(item, dict):
            return str(item.get("title", "Untitled"))
        return "Untitled"
