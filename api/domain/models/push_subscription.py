from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PushSubscription:
    endpoint: str
    p256dh: str
    auth: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
