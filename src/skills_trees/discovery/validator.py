from __future__ import annotations

import re
from pathlib import Path

from ..models.skill import SkillNode, SkillTree
from ..models.validation import ValidationMessage, ValidationResult

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KNOWN_METADATA_FIELDS = {
    "name",
    "version",
    "description",
    "tags",
    "when_to_use",
    "priority",
    "inputs",
    "workspace_globs",
    "evidence_patterns",
    "script_entrypoints",
    "references",
    "exclusive_with",
}


class SkillValidator:
    def validate(self, node: SkillNode) -> SkillNode:
        messages: list[ValidationMessage] = []
        if " " in node.slug:
            messages.append(self._error("invalid_path", "Paths containing spaces are invalid skill nodes.", node.path))
        if not node.skill_md_path.exists():
            messages.append(self._error("missing_skill_md", "`SKILL.md` is required.", node.skill_md_path))
        else:
            self._validate_frontmatter(node, messages)
        if node.skill_yaml_path is not None and self._has_frontmatter(node.skill_md_path):
            messages.append(
                self._warning(
                    "multiple_metadata_sources",
                    "Both `skill.yaml` and `SKILL.md` frontmatter are present; `skill.yaml` takes precedence.",
                    node.path,
                )
            )
        if node.skill_yaml_path is not None:
            raw = self._safe_load_yaml(node.skill_yaml_path, messages)
            if raw is not None:
                self._validate_metadata_shape(raw, node, messages, node.skill_yaml_path)
        elif node.metadata_source == "frontmatter":
            raw = self._safe_load_frontmatter(node.skill_md_path, messages)
            if raw is not None:
                self._validate_metadata_shape(raw, node, messages, node.skill_md_path)
        for dirname, path in (
            ("references", node.references_dir),
            ("examples", node.examples_dir),
            ("scripts", node.scripts_dir),
        ):
            if path is not None and not path.is_dir():
                messages.append(self._error(f"invalid_{dirname}_dir", f"`{dirname}/` is not a directory.", path))
        for entry in node.metadata.script_entrypoints:
            target = node.path / entry.path
            if node.scripts_dir is None or not target.exists():
                messages.append(
                    self._error(
                        "missing_script",
                        f"Declared script entrypoint `{entry.name}` points to a file that does not exist.",
                        target,
                    )
                )
        node.validation_messages = messages
        node.is_valid = not any(message.level == "error" for message in messages)
        return node

    def validate_tree(self, tree: SkillTree) -> list[ValidationMessage]:
        messages: list[ValidationMessage] = []
        for node in tree.iter_preorder():
            messages.extend(node.validation_messages)
        return messages

    def build_result(self, tree: SkillTree) -> ValidationResult:
        messages = self.validate_tree(tree)
        return ValidationResult(
            valid_nodes=[node.slug for node in tree.iter_preorder() if node.is_valid],
            invalid_nodes=[node.slug for node in tree.iter_preorder() if not node.is_valid],
            messages=messages,
        )

    def _safe_load_yaml(self, path: Path, messages: list[ValidationMessage]) -> dict | None:
        try:
            import yaml

            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except UnicodeDecodeError:
            messages.append(self._error("invalid_encoding", "Metadata file must be UTF-8.", path))
            return None
        except Exception as exc:  # pragma: no cover
            messages.append(self._error("invalid_yaml", f"Could not parse `skill.yaml`: {exc}", path))
            return None
        if not isinstance(loaded, dict):
            messages.append(self._error("invalid_yaml", "`skill.yaml` must contain a mapping.", path))
            return None
        return loaded

    def _safe_load_frontmatter(self, path: Path, messages: list[ValidationMessage]) -> dict | None:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            messages.append(self._error("invalid_encoding", "`SKILL.md` must be UTF-8.", path))
            return None
        marker = "\n---\n"
        end = text.find(marker, 4)
        if not text.startswith("---\n") or end == -1:
            messages.append(self._error("invalid_frontmatter", "Frontmatter is malformed.", path))
            return None
        try:
            import yaml

            loaded = yaml.safe_load(text[4:end]) or {}
        except Exception as exc:  # pragma: no cover
            messages.append(self._error("invalid_frontmatter", f"Could not parse frontmatter: {exc}", path))
            return None
        if not isinstance(loaded, dict):
            messages.append(self._error("invalid_frontmatter", "Frontmatter must contain a mapping.", path))
            return None
        return loaded

    def _validate_metadata_shape(
        self, raw: dict, node: SkillNode, messages: list[ValidationMessage], source_path: Path
    ) -> None:
        if "name" not in raw or not isinstance(raw.get("name"), str) or not raw.get("name"):
            messages.append(self._error("missing_name", "Metadata requires string field `name`.", source_path))
        if "description" not in raw or not isinstance(raw.get("description"), str) or not raw.get("description"):
            messages.append(
                self._error("missing_description", "Metadata requires string field `description`.", source_path)
            )
        name = raw.get("name")
        if isinstance(name, str) and name:
            self._validate_name(name, node, messages, source_path)
        typed_fields = {
            "version": str,
            "priority": int,
        }
        list_fields = {
            "tags",
            "when_to_use",
            "inputs",
            "workspace_globs",
            "evidence_patterns",
            "references",
            "exclusive_with",
        }
        for field, expected in typed_fields.items():
            if field in raw and raw[field] is not None and not isinstance(raw[field], expected):
                messages.append(self._error("invalid_field_type", f"`{field}` has invalid type.", source_path))
        for field in list_fields:
            if field in raw and not isinstance(raw[field], list):
                messages.append(self._error("invalid_field_type", f"`{field}` has invalid type.", source_path))
        if "script_entrypoints" in raw:
            if not isinstance(raw["script_entrypoints"], list):
                messages.append(self._error("invalid_field_type", "`script_entrypoints` has invalid type.", source_path))
            else:
                for item in raw["script_entrypoints"]:
                    if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("path"), str):
                        messages.append(
                            self._error(
                                "invalid_script_entrypoint",
                                "Each script entrypoint must contain string fields `name` and `path`.",
                                source_path,
                            )
                        )
        # unknown fields ignored by design

    def _validate_frontmatter(self, node: SkillNode, messages: list[ValidationMessage]) -> None:
        try:
            text = node.skill_md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            messages.append(self._error("invalid_encoding", "`SKILL.md` must be UTF-8.", node.skill_md_path))
            return
        if not text.startswith("---\n"):
            return
        if "\n---\n" not in text[4:]:
            messages.append(self._error("invalid_frontmatter", "Frontmatter is malformed.", node.skill_md_path))

    def _has_frontmatter(self, path: Path) -> bool:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return False
        return text.startswith("---\n") and "\n---\n" in text[4:]

    def _validate_name(
        self, name: str, node: SkillNode, messages: list[ValidationMessage], source_path: Path
    ) -> None:
        if len(name) > 64:
            messages.append(self._error("invalid_name", "Metadata `name` must be at most 64 characters.", source_path))
        if not NAME_PATTERN.fullmatch(name):
            messages.append(
                self._error(
                    "invalid_name",
                    "Metadata `name` must use lowercase letters, numbers, and single hyphens only.",
                    source_path,
                )
            )
        if name != node.path.name:
            messages.append(
                self._error(
                    "name_mismatch",
                    "Metadata `name` must match the skill directory name.",
                    source_path,
                )
            )

    def _error(self, code: str, message: str, path: Path | None) -> ValidationMessage:
        return ValidationMessage(level="error", code=code, message=message, path=path)

    def _warning(self, code: str, message: str, path: Path | None) -> ValidationMessage:
        return ValidationMessage(level="warning", code=code, message=message, path=path)
