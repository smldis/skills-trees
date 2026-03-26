from __future__ import annotations

from pathlib import Path


class SkillScanner:
    def scan(self, skills_root: Path) -> list[Path]:
        if not skills_root.exists():
            return []
        found: list[Path] = []
        self._scan_dir(skills_root, found)
        return sorted(found)

    def _scan_dir(self, current: Path, found: list[Path]) -> None:
        for child in sorted(current.iterdir(), key=lambda p: p.name):
            if child.name.startswith(".") or not child.is_dir():
                continue
            if child.name in {"references", "examples", "scripts"}:
                continue
            if (child / "SKILL.md").exists():
                found.append(child)
            self._scan_dir(child, found)
