from __future__ import annotations

from pathlib import Path


def default_log_file(workspace_root: Path) -> Path:
    return workspace_root / ".skills-trees.log"


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
