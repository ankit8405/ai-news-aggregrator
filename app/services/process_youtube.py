from typing import Optional
from ..scrapers.youtube import YouTubeScraper
from ..database.repository import Repository
from .base import BaseProcessService


TRANSCRIPT_UNAVAILABLE_MARKER = "__UNAVAILABLE__"


class YouTubeTranscriptProcessor(BaseProcessService):
    def __init__(self):
        super().__init__()
        self.scraper = YouTubeScraper()
        self.repo = Repository()
        self.unavailable = 0

    def get_items_to_process(self, limit: Optional[int] = None) -> list:
        return self.repo.get_youtube_videos_without_transcript(limit=limit)

    def process_item(self, item) -> Optional[str]:
        try:
            transcript_result = self.scraper.get_transcript(item.video_id)
            return transcript_result.text if transcript_result else TRANSCRIPT_UNAVAILABLE_MARKER
        except Exception:
            return TRANSCRIPT_UNAVAILABLE_MARKER

    def save_result(self, item, result: str) -> bool:
        success = self.repo.update_youtube_video_transcript(item.video_id, result)
        if result == TRANSCRIPT_UNAVAILABLE_MARKER:
            self.unavailable += 1
        return success

    def process(self, limit: Optional[int] = None) -> dict:
        result = super().process(limit=limit)
        result["unavailable"] = self.unavailable
        return result


def process_youtube_transcripts(limit: Optional[int] = None) -> dict:
    processor = YouTubeTranscriptProcessor()
    return processor.process(limit=limit)


if __name__ == "__main__":
    result = process_youtube_transcripts()
    print(f"Total videos: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Unavailable: {result['unavailable']}")
    print(f"Failed: {result['failed']}")
