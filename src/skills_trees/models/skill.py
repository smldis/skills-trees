from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .validation import ValidationMessage


@dataclass(slots=True)
class ScriptEntrypoint:
    name: str
    path: str
    description: str | None = None


@dataclass(slots=True)
class SkillMetadata:
    name: str
    description: str
    version: str | None = None
    tags: list[str] = field(default_factory=list)
    when_to_use: list[str] = field(default_factory=list)
    priority: int | None = None
    inputs: list[str] = field(default_factory=list)
    workspace_globs: list[str] = field(default_factory=list)
    evidence_patterns: list[str] = field(default_factory=list)
    script_entrypoints: list[ScriptEntrypoint] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    exclusive_with: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkillNode:
    name: str
    slug: str
    path: Path
    relative_path: Path
    parent_slug: str | None
    metadata: SkillMetadata
    skill_md_path: Path
    skill_yaml_path: Path | None
    references_dir: Path | None
    examples_dir: Path | None
    scripts_dir: Path | None
    children: list[str] = field(default_factory=list)
    is_valid: bool = True
    validation_messages: list[ValidationMessage] = field(default_factory=list)


@dataclass(slots=True)
class SkillTree:
    root_nodes: list[str]
    nodes_by_slug: dict[str, SkillNode]

    def get_node(self, slug: str) -> SkillNode:
        return self.nodes_by_slug[slug]

    def get_descendants(self, slug: str) -> list[SkillNode]:
        node = self.get_node(slug)
        results: list[SkillNode] = []
        for child_slug in node.children:
            child = self.get_node(child_slug)
            results.append(child)
            results.extend(self.get_descendants(child_slug))
        return results

    def get_path(self, slug: str) -> list[SkillNode]:
        parts: list[SkillNode] = []
        current = self.get_node(slug)
        while True:
            parts.append(current)
            if current.parent_slug is None:
                break
            current = self.get_node(current.parent_slug)
        return list(reversed(parts))

    def iter_preorder(self) -> list[SkillNode]:
        ordered: list[SkillNode] = []

        def visit(slug: str) -> None:
            node = self.get_node(slug)
            ordered.append(node)
            for child_slug in sorted(node.children):
                visit(child_slug)

        for slug in sorted(self.root_nodes):
            visit(slug)
        return ordered
