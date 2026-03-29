# AGENTS.md

## Purpose

`skills-trees` is a minimal Python package for workspace-local skills packages.

The package currently does three things:

- discover skills from a workspace `.skills/` tree
- validate skill structure and metadata
- generate agent-facing context from valid skills

This project intentionally does not own routing, prompt assembly, or script execution orchestration.

## Tech Stack

- Python `>=3.11`
- `PyYAML`
- `pytest`
- packaging via `setuptools`

## Repository Layout

- `src/skills_trees/api.py`
  Public API surface.
- `src/skills_trees/cli.py`
  CLI entrypoint for `discover`, `validate`, and `context`.
- `src/skills_trees/discovery/`
  Scanner, parser, and validator.
- `src/skills_trees/models/`
  Dataclasses for config, discovery, skills, and validation.
- `src/skills_trees/logging/`
  Lightweight event recording.
- `src/skills_trees/utils/`
  File helpers and serialization.
- `tests/`
  Pytest coverage for discovery, validation, hierarchy, and CLI behavior.

## Current Product Rules

- A directory is a skill node only if it contains `SKILL.md`.
- `skill.yaml` is optional.
- If `skill.yaml` is present, agent context uses YAML-derived content.
- If `skill.yaml` is absent, agent context uses the full `SKILL.md`.
- Missing `skill.yaml` is valid behavior and must not produce a warning.
- Unknown metadata fields in `skill.yaml` are ignored without warnings.
- Paths containing spaces are invalid.
- Skill ordering is deterministic preorder traversal with alphabetical sibling ordering.
- Generated context includes validation errors and warnings for real package problems.

## Local Commands

Install dev dependencies:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
pytest -q
```

Run the CLI:

```bash
skills-trees --help
skills-trees discover --workspace .
skills-trees validate --workspace .
skills-trees context --workspace .
```

Run without installation:

```bash
PYTHONPATH=src python -m skills_trees.cli --help
```

## Editing Guidelines

- Keep the v1 scope narrow.
- Prefer small, deterministic behavior over speculative abstractions.
- Do not add routing, automatic skill selection, or package-owned script execution unless explicitly requested.
- Keep JSON and text outputs stable; tests depend on that behavior.
- When changing validation behavior, update tests first or in the same change.
- When changing public API or CLI output, update `README.md` and tests.

## Verification Expectations

After meaningful code changes, run:

```bash
pytest -q
```

If CLI behavior changes, verify `tests/test_cli.py`.

## Notes

- The environment may print unrelated `/etc/profile.d/... append_path` shell noise; ignore it unless the command itself fails.
- The repo may contain user edits in progress. Do not revert unrelated local changes.
