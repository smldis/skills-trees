from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimeConfig:
    workspace_root: Path
    skills_root: Path
    default_output_format: str = "text"
    log_file: Path | None = None
