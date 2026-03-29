from __future__ import annotations

from pathlib import Path

from skills_trees.api import discover_skills, validate_skills
from skills_trees.models.common import RuntimeConfig


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_validate_missing_script_entrypoint(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    write(
        skills_root / "python" / "skill.yaml",
        "name: python\ndescription: desc\nscript_entrypoints:\n  - name: run\n    path: scripts/run.sh\n",
    )
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == ["python"]
    assert any(message.code == "missing_script" for message in result.messages)


def test_unknown_metadata_fields_are_ignored(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    write(skills_root / "python" / "skill.yaml", "name: python\ndescription: desc\nfoo: bar\n")
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == []
    assert result.messages == []


def test_validate_frontmatter_metadata(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(
        skills_root / "python" / "SKILL.md",
        "---\nname: python\ndescription: desc\n---\n# Python\n\nUse this.\n",
    )
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == []
    assert result.messages == []


def test_validate_malformed_frontmatter(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(
        skills_root / "python" / "SKILL.md",
        "---\nname: python\ndescription: [oops\n# Python\n",
    )
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == ["python"]
    assert any(message.code == "invalid_frontmatter" for message in result.messages)


def test_validate_strict_name_rules(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    write(skills_root / "python" / "skill.yaml", "name: Python\ndescription: desc\n")
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == ["python"]
    assert any(message.code == "invalid_name" for message in result.messages)


def test_warn_when_both_skill_yaml_and_frontmatter_exist(tmp_path: Path) -> None:
    skills_root = tmp_path / ".skills"
    write(
        skills_root / "python" / "SKILL.md",
        "---\nname: python\ndescription: from frontmatter\n---\n# Python\n",
    )
    write(skills_root / "python" / "skill.yaml", "name: python\ndescription: from yaml\n")
    discovery = discover_skills(RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    result = validate_skills(discovery, RuntimeConfig(workspace_root=tmp_path, skills_root=skills_root))
    assert result.invalid_nodes == []
    assert any(message.code == "multiple_metadata_sources" and message.level == "warning" for message in result.messages)
