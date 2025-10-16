from datetime import datetime
from typing import Dict


class CrawlStatus:
    def __init__(self):
        self.jobs: Dict[str, dict] = {}

    def start(self, name: str, total_urls: int = 0):
        """Register new crawl job."""
        self.jobs[name] = {
            "status": "running",
            "started": datetime.now(),
            "total_urls": total_urls,
            "processed": 0,
            "errors": 0,
            "finished": None,
        }

    def update(self, name: str, success: bool = True):
        """Update progress."""
        if name in self.jobs:
            self.jobs[name]["processed"] += 1
            if not success:
                self.jobs[name]["errors"] += 1

    def finish(self, name: str):
        """Mark as finished."""
        if name in self.jobs:
            self.jobs[name]["status"] = "finished"
            self.jobs[name]["finished"] = datetime.now()

    def get(self, name: str) -> dict:
        """Get status."""
        return self.jobs.get(name, {"status": "unknown"})


# Global instance
crawl_status = CrawlStatus()
