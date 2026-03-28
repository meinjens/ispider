from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FeedItem:
    source_id: int
    url: str
    url_hash: str
    title: str
    id: Optional[int] = None
    description: Optional[str] = None
    raw_content: Optional[str] = None
    pub_date: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    read: bool = False
