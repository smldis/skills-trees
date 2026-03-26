from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .events import LogEvent


@dataclass
class EventRecorder:
    log_file: Path
    _events: list[LogEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if self.log_file.exists():
            age = datetime.now(timezone.utc) - datetime.fromtimestamp(
                self.log_file.stat().st_mtime, tz=timezone.utc
            )
            if age > timedelta(days=2):
                self.log_file.write_text("", encoding="utf-8")

    def record(self, event: LogEvent) -> None:
        self._events.append(event)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"{event.event_type} {event.message}\n")

    def events(self) -> list[LogEvent]:
        return list(self._events)
