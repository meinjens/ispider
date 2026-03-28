from dataclasses import dataclass
from typing import Optional


@dataclass
class Keyword:
    term: str
    threshold: int = 60             # Mindest-Score für Push-Trigger
    notify: bool = True
    active: bool = True
    id: Optional[int] = None
