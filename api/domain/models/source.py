from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    RSS = "rss"
    WEB = "web"


class SourcePriority(str, Enum):
    HIGH = "high"
    LOW = "low"


@dataclass
class Source:
    url: str
    name: str
    type: SourceType
    id: Optional[int] = None
    active: bool = True
    priority: SourcePriority = SourcePriority.HIGH
    tag_ids: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_fetched_at: Optional[datetime] = None
    error_count: int = 0
