from __future__ import annotations

from pathlib import Path

from skills_trees.api import discover_skills
from skills_trees.models.common import RuntimeConfig


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_discover_nested_skills(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    write(skills_root / "python" / "pytest" / "SKILL.md", "# Pytest")
    result = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.valid_nodes == ["python", "python/pytest"]
    assert result.tree.get_node("python").children == ["python/pytest"]
