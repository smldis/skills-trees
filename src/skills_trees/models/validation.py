from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..logging.events import LogEvent


@dataclass(slots=True)
class ValidationMessage:
    level: str
    code: str
    message: str
    path: Path | None = None


@dataclass(slots=True)
class ValidationResult:
    valid_nodes: list[str] = field(default_factory=list)
    invalid_nodes: list[str] = field(default_factory=list)
    messages: list[ValidationMessage] = field(default_factory=list)
    logs: list[LogEvent] = field(default_factory=list)
