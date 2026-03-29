from __future__ import annotations

from pathlib import Path

from .discovery import SkillParser, SkillScanner, SkillValidator
from .logging import EventRecorder, LogEvent
from .models.common import RuntimeConfig
from .models.discovery import AgentContextResult, AgentContextSource, DiscoveryResult
from .models.validation import ValidationResult
from .utils.files import default_log_file
from .utils.serialization import build_agent_context_block, format_agent_context_text


def _recorder(config: RuntimeConfig) -> EventRecorder:
    return EventRecorder(config.log_file or default_log_file(config.workspace_root))


def discover_skills(config: RuntimeConfig) -> DiscoveryResult:
    recorder = _recorder(config)
    recorder.record(LogEvent("skills.discovery.started", "Discovery started"))
    scanner = SkillScanner()
    parser = SkillParser(config.skills_root)
    validator = SkillValidator()
    paths = scanner.scan(config.skills_root)
    nodes = [parser.parse_node(path, None) for path in paths]
    tree = parser.build_tree(nodes)
    for node in tree.iter_preorder():
        validator.validate(node)
    result = DiscoveryResult(
        skills_root=config.skills_root,
        tree=tree,
        valid_nodes=[node.slug for node in tree.iter_preorder() if node.is_valid],
        invalid_nodes=[node.slug for node in tree.iter_preorder() if not node.is_valid],
        logs=recorder.events(),
    )
    recorder.record(LogEvent("skills.discovery.completed", "Discovery completed", {"valid": len(result.valid_nodes)}))
    result.logs = recorder.events()
    return result


def validate_skills(discovery: DiscoveryResult, config: RuntimeConfig) -> ValidationResult:
    recorder = _recorder(config)
    recorder.record(LogEvent("skills.validation.started", "Validation started"))
    validator = SkillValidator()
    result = validator.build_result(discovery.tree)
    for message in result.messages:
        if message.level == "error":
            recorder.record(LogEvent("skills.validation.failed", message.message, {"code": message.code}))
    recorder.record(LogEvent("skills.validation.completed", "Validation completed", {"errors": len(result.invalid_nodes)}))
    result.logs = recorder.events()
    return result


def generate_agent_context(discovery: DiscoveryResult, config: RuntimeConfig) -> AgentContextResult:
    recorder = _recorder(config)
    blocks = []
    sources: list[AgentContextSource] = []
    validation_lines = []
    for node in discovery.tree.iter_preorder():
        if node.is_valid:
            block = build_agent_context_block(node)
            blocks.append(block)
            source_type = node.metadata_source or "skill_md"
            source_path = node.skill_yaml_path if source_type == "skill_yaml" else node.skill_md_path
            sources.append(AgentContextSource(slug=node.slug, source_type=source_type, source_path=source_path))
        for message in node.validation_messages:
            path_str = str(message.path) if message.path is not None else node.slug
            validation_lines.append(f"- {message.level}: `{path_str}` -> {message.message}")
    context = format_agent_context_text(blocks, validation_lines)
    recorder.record(LogEvent("skills.context.generated", "Agent context generated", {"skills": len(blocks)}))
    return AgentContextResult(context=context, sources=sources, messages=[m for n in discovery.tree.iter_preorder() for m in n.validation_messages], logs=recorder.events())
