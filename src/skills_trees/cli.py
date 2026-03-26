from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .api import discover_skills, generate_agent_context, validate_skills
from .models.common import RuntimeConfig
from .utils.serialization import serialize_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills-trees",
        description=(
            "Discover, validate, and generate agent context for workspace-local skills packages."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    command_help = {
        "discover": "Discover skills and print the skill tree.",
        "validate": "Validate discovered skills and report warnings or errors.",
        "context": "Generate agent-facing context from discovered skills.",
    }
    for name in ("discover", "validate", "context"):
        sub = subparsers.add_parser(name, help=command_help[name], description=command_help[name])
        sub.add_argument(
            "--workspace",
            required=True,
            help="Workspace root used to resolve the default .skills directory.",
        )
        sub.add_argument(
            "--skills-root",
            help="Explicit skills root directory. Defaults to <workspace>/.skills.",
        )
        sub.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable JSON output.",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace_root = Path(args.workspace).resolve()
    skills_root = Path(args.skills_root).resolve() if args.skills_root else workspace_root / ".skills"
    config = RuntimeConfig(
        workspace_root=workspace_root,
        skills_root=skills_root,
        default_output_format="json" if args.json else "text",
    )
    if args.command == "discover":
        result = discover_skills(config)
        print_discovery(result, config.default_output_format)
        return 0
    discovery = discover_skills(config)
    if args.command == "validate":
        result = validate_skills(discovery, config)
        print(serialize_result(result, config.default_output_format))
        return 1 if result.invalid_nodes else 0
    result = generate_agent_context(discovery, config)
    print(serialize_result(result, config.default_output_format))
    return 0


def print_discovery(result, output_format: str) -> None:
    if output_format == "json":
        print(serialize_result(result, output_format))
        return
    for node in result.tree.iter_preorder():
        indent = "  " * (len(node.slug.split("/")) - 1)
        status = "" if node.is_valid else " [invalid]"
        print(f"{indent}- {node.slug}{status}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
