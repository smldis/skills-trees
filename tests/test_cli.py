from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_trees.cli import main


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cli_discover_json(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    code = main(["discover", "--workspace", str(tmp_path), "--json"])
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["valid_nodes"] == ["python"]


def test_cli_validate_exit_code(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python")
    write(skills_root / "python" / "skill.yaml", "name: python\ndescription: desc\nscript_entrypoints:\n  - name: run\n    path: scripts/run.sh\n")
    code = main(["validate", "--workspace", str(tmp_path)])
    _ = capsys.readouterr()
    assert code == 1


def test_cli_context_outputs_skill_md_fallback(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / ".skills"
    write(skills_root / "python" / "SKILL.md", "# Python\n\nUse this.")
    code = main(["context", "--workspace", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "path: python" in out
    assert "Use this." in out


def test_cli_help(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Discover, validate, and generate agent context" in out
    assert "discover" in out
    assert "validate" in out
    assert "context" in out


def test_cli_context_uses_frontmatter_metadata(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / ".skills"
    write(
        skills_root / "python" / "SKILL.md",
        "---\nname: python\ndescription: desc\ntags:\n  - cli\n---\n# Python\n\nUse this.\n",
    )
    code = main(["context", "--workspace", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "name: python" in out
    assert "description: desc" in out
    assert "# Python" not in out
