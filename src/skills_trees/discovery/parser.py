from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..models.skill import ScriptEntrypoint, SkillMetadata, SkillNode, SkillTree


class SkillParser:
    def __init__(self, skills_root: Path) -> None:
        self.skills_root = skills_root

    def parse_node(self, path: Path, parent_slug: str | None) -> SkillNode:
        relative_path = path.relative_to(self.skills_root)
        slug = relative_path.as_posix()
        metadata, metadata_source, skill_md_body = self.parse_metadata(path)
        references_dir = path / "references" if (path / "references").exists() else None
        examples_dir = path / "examples" if (path / "examples").exists() else None
        scripts_dir = path / "scripts" if (path / "scripts").exists() else None
        skill_yaml_path = path / "skill.yaml" if (path / "skill.yaml").exists() else None
        return SkillNode(
            name=metadata.name,
            slug=slug,
            path=path,
            relative_path=relative_path,
            parent_slug=parent_slug,
            metadata=metadata,
            metadata_source=metadata_source,
            skill_md_path=path / "SKILL.md",
            skill_yaml_path=skill_yaml_path,
            references_dir=references_dir,
            examples_dir=examples_dir,
            scripts_dir=scripts_dir,
            skill_md_body=skill_md_body,
        )

    def parse_metadata(self, path: Path) -> tuple[SkillMetadata, str | None, str]:
        yaml_path = path / "skill.yaml"
        skill_md_path = path / "SKILL.md"
        try:
            skill_md_text = skill_md_path.read_text(encoding="utf-8") if skill_md_path.exists() else ""
        except UnicodeDecodeError:
            skill_md_text = ""
        frontmatter = self._parse_frontmatter(skill_md_text)
        if yaml_path.exists():
            try:
                loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            except Exception:
                loaded = {}
            if not isinstance(loaded, dict):
                loaded = {}
            return self._build_metadata(loaded, path), "skill_yaml", frontmatter["body"]
        if isinstance(frontmatter["metadata"], dict):
            return self._build_metadata(frontmatter["metadata"], path), "frontmatter", frontmatter["body"]
        return SkillMetadata(name=path.name, description=""), None, skill_md_text.strip()

    def _build_metadata(self, loaded: dict[str, Any], path: Path) -> SkillMetadata:
        script_entrypoints = []
        for item in loaded.get("script_entrypoints", []) or []:
            if isinstance(item, dict) and "name" in item and "path" in item:
                script_entrypoints.append(
                    ScriptEntrypoint(
                        name=str(item["name"]),
                        path=str(item["path"]),
                        description=str(item["description"]) if "description" in item else None,
                    )
                )
        return SkillMetadata(
            name=str(loaded.get("name", path.name)),
            description=str(loaded.get("description", "")),
            version=str(loaded["version"]) if "version" in loaded else None,
            tags=[str(v) for v in loaded.get("tags", []) or []],
            when_to_use=[str(v) for v in loaded.get("when_to_use", []) or []],
            priority=int(loaded["priority"]) if "priority" in loaded and loaded["priority"] is not None else None,
            inputs=[str(v) for v in loaded.get("inputs", []) or []],
            workspace_globs=[str(v) for v in loaded.get("workspace_globs", []) or []],
            evidence_patterns=[str(v) for v in loaded.get("evidence_patterns", []) or []],
            script_entrypoints=script_entrypoints,
            references=[str(v) for v in loaded.get("references", []) or []],
            exclusive_with=[str(v) for v in loaded.get("exclusive_with", []) or []],
        )

    def _parse_frontmatter(self, text: str) -> dict[str, Any]:
        if not text.startswith("---\n"):
            return {"metadata": None, "body": text.strip(), "has_frontmatter": False}
        marker = "\n---\n"
        end = text.find(marker, 4)
        if end == -1:
            return {"metadata": None, "body": text.strip(), "has_frontmatter": True}
        raw = text[4:end]
        body = text[end + len(marker) :].strip()
        try:
            loaded = yaml.safe_load(raw) or {}
        except Exception:
            loaded = None
        return {"metadata": loaded, "body": body, "has_frontmatter": True}

    def build_tree(self, nodes: list[SkillNode]) -> SkillTree:
        by_slug = {node.slug: node for node in nodes}
        root_nodes: list[str] = []
        for node in nodes:
            parent_slug = self._find_parent_slug(node.slug, by_slug)
            node.parent_slug = parent_slug
            if parent_slug is None:
                root_nodes.append(node.slug)
            else:
                by_slug[parent_slug].children.append(node.slug)
        for node in nodes:
            node.children.sort()
        root_nodes.sort()
        return SkillTree(root_nodes=root_nodes, nodes_by_slug=by_slug)

    def _find_parent_slug(self, slug: str, by_slug: dict[str, SkillNode]) -> str | None:
        parts = slug.split("/")
        while len(parts) > 1:
            parts.pop()
            candidate = "/".join(parts)
            if candidate in by_slug:
                return candidate
        return None
