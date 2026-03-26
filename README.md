# skills-trees

Minimal workspace-local skills discovery, validation, and agent context generation.

## Rationale

`skills-trees` exists to make local skills packages visible and reliable without turning them into a large runtime orchestration system.

The package focuses on a narrow v1 boundary:

- discover skills from a workspace-local `.skills/` directory
- validate package structure and metadata
- represent hierarchical subskills as a tree
- generate agent-facing context so the agent can see available skills and their paths

The package does not try to own routing, prompt assembly, or script execution orchestration. The agent or host runtime can inspect package files directly and decide how to use them.

## Feature Summary

- Workspace-local discovery of skills and nested subskills
- Validation of `SKILL.md`, `skill.yaml`, and declared resource directories
- Path-based hierarchy model for skill nodes
- Agent-facing context generation using `skill.yaml` when present and full `SKILL.md` otherwise
- Validation warnings and errors included in generated agent context
- CLI commands for `discover`, `validate`, and `context`
- Human-readable and JSON output modes

## CLI

```bash
skills-trees --help
skills-trees discover --workspace .
skills-trees validate --workspace .
skills-trees context --workspace .
```

Use `--json` on any command for machine-readable output.
