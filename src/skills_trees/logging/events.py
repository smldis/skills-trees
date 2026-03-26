from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LogEvent:
    event_type: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
