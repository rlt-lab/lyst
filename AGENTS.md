# Repository Guidelines

## Project Structure & Module Organization
- `main.py` contains the current entry point (`main()`), and is the only source file.
- `pyproject.toml` defines project metadata and Python requirements.
- `README.md` exists but is currently empty; treat it as the primary place for project overview once content is added.
- No dedicated `tests/` or `src/` directories yet. If the project grows, prefer `src/lyst/` for code and `tests/` for tests.

## Build, Test, and Development Commands
- `uv run python main.py` runs the current entry point.
- `uv run python main.py groceries` opens or creates a list named `groceries`.
- `uv add textual` adds the TUI dependency.
- `uv sync` installs/syncs the environment.
- There are no build or test commands configured yet.

## Coding Style & Naming Conventions
- Follow standard Python style: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes.
- Keep modules small and focused; prefer explicit imports.
- No formatter or linter is configured. If you add one, document it here and in `pyproject.toml`.

## Testing Guidelines
- No testing framework is set up yet.
- When adding tests, prefer `pytest` with files named `test_*.py` under `tests/`.
- Document new test commands here (e.g., `pytest`).

## Commit & Pull Request Guidelines
- This repository has no Git commits yet, so there is no established commit message convention.
- Recommended: use short, imperative commit messages (or Conventional Commits like `feat: add CLI`).
- For PRs, include a concise summary, any relevant issue links, and note how changes were verified (commands run, manual checks).

## Configuration & Security Notes
- `pyproject.toml` currently has no dependencies; add version-pinned dependencies as needed.
- Keep secrets out of the repo; use environment variables or local config files excluded by `.gitignore`.
