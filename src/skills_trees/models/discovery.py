from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..logging.events import LogEvent
from .skill import SkillTree
from .validation import ValidationMessage


@dataclass(slots=True)
class DiscoveryResult:
    skills_root: Path
    tree: SkillTree
    valid_nodes: list[str] = field(default_factory=list)
    invalid_nodes: list[str] = field(default_factory=list)
    logs: list[LogEvent] = field(default_factory=list)


@dataclass(slots=True)
class AgentContextSource:
    slug: str
    source_type: str
    source_path: Path


@dataclass(slots=True)
class AgentContextResult:
    context: str
    sources: list[AgentContextSource] = field(default_factory=list)
    messages: list[ValidationMessage] = field(default_factory=list)
    logs: list[LogEvent] = field(default_factory=list)
