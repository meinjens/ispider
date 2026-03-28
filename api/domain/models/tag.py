from dataclasses import dataclass
from typing import Optional


@dataclass
class Tag:
    name: str
    color: str = "#00B37E"
    id: Optional[int] = None
