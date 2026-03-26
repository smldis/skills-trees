from __future__ import annotations

from pathlib import Path

from skills_trees.api import discover_skills
from skills_trees.models.common import RuntimeConfig


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_paths_with_spaces_are_invalid(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "bad skill" / "SKILL.md", "# Bad")
    result = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == ["bad skill"]
