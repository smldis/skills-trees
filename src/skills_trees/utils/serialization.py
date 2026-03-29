from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import yaml

from ..models.discovery import AgentContextResult
from ..models.skill import SkillNode

YAML_CONTEXT_FIELDS = [
    "name",
    "description",
    "tags",
    "when_to_use",
    "inputs",
    "workspace_globs",
    "evidence_patterns",
    "references",
    "script_entrypoints",
    "exclusive_with",
]


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def serialize_result(result: Any, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(_to_plain(result), indent=2, sort_keys=False)
    if isinstance(result, AgentContextResult):
        return result.context
    return repr(result)


def render_yaml_context(yaml_path: Path) -> str:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return ""
    ordered: dict[str, Any] = {}
    for field in YAML_CONTEXT_FIELDS:
        if field in raw:
            ordered[field] = raw[field]
    rendered = yaml.safe_dump(ordered, sort_keys=False, default_flow_style=False).strip()
    return rendered


def render_metadata_context(raw: dict[str, Any]) -> str:
    ordered: dict[str, Any] = {}
    for field in YAML_CONTEXT_FIELDS:
        if field in raw:
            ordered[field] = raw[field]
    rendered = yaml.safe_dump(ordered, sort_keys=False, default_flow_style=False).strip()
    return rendered


def render_skill_md_context(skill_md_path: Path) -> str:
    return skill_md_path.read_text(encoding="utf-8").strip()


def format_agent_context_text(blocks: list[dict[str, str]], validation_lines: list[str]) -> str:
    lines = ["Skills", ""]
    for block in blocks:
        lines.append(f"- {block['name']}")
        lines.append(f"  path: {block['path']}")
        context_lines = block["context"].splitlines() or [""]
        if context_lines:
            lines.append(f"  context: {context_lines[0]}")
            for extra in context_lines[1:]:
                lines.append(f"    {extra}")
        lines.append("")
    lines.append("Validation")
    lines.append("")
    if validation_lines:
        lines.extend(validation_lines)
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def build_agent_context_block(node: SkillNode) -> dict[str, str]:
    if node.metadata_source == "skill_yaml" and node.skill_yaml_path is not None and node.skill_yaml_path.exists():
        context = render_yaml_context(node.skill_yaml_path)
    elif node.metadata_source == "frontmatter":
        context = render_metadata_context(_load_frontmatter_metadata(node.skill_md_path))
    else:
        context = render_skill_md_context(node.skill_md_path)
    return {
        "name": node.slug,
        "path": node.slug,
        "context": context,
    }


def _load_frontmatter_metadata(skill_md_path: Path) -> dict[str, Any]:
    text = skill_md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    loaded = yaml.safe_load(text[4:end]) or {}
    return loaded if isinstance(loaded, dict) else {}
