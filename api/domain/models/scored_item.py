from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ScoredItem:
    item_id: int
    score: int                        # 0–100
    reason: str
    id: Optional[int] = None
    keywords_matched: list[str] = field(default_factory=list)
    notified_at: Optional[datetime] = None
    scored_at: datetime = field(default_factory=datetime.utcnow)
