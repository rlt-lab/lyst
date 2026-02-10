# TECHSTACK: Lyst TUI Lists

## Runtime & Language
- Python 3.14 (from `pyproject.toml`).
- Project managed with `uv` (already initialized via `uv init lyst`).

## UI Framework
- Textual for the TUI.
- Single-screen, side-by-side two-panel layout: lists on the left, items on the right.
- Tab / Shift+Tab switches focus between panels; active panel border highlighted.
- Context-sensitive footer showing available keybindings.
- Theme: Ayu Dusk (Mirage) — a modern dark mellow palette with accent highlights.

## Data Storage
- SQLite for persistence.
- Schema:
  - `lists(id INTEGER PRIMARY KEY, title TEXT, created_at TEXT, updated_at TEXT)`
  - `items(id INTEGER PRIMARY KEY, list_id INTEGER, text TEXT, checked INTEGER, sort_order INTEGER)`
- Use a small data access layer (inline functions) for minimal LOC.
- Database path: `~/.lyst/lyst.db` via `platformdirs`.

## Project Layout (initial)
- `main.py` contains app entry point and UI logic.
- `pyproject.toml` defines dependencies.

## Dependencies (MVP)
- `textual`
- `sqlite3` (stdlib)
- Optional: `platformdirs` for user data path.

## Theme Spec (Ayu Dusk / Mirage)
- Base background: `#1f2430`
- Surface (panels): `#242936`
- Primary text: `#cccac2`
- Muted text: `#707a8c`
- Accent (active borders, selection): `#ffcc66`
- Checked/dimmed items: `#505868`
- Highlight (selected row bg): `#2b3245`
- Inactive border: `#171b24`
- Footer background: `#1c212c`
- Modal border: `#ffcc66`, modal background: `#282e3b`
- Error/delete: `#ff6666`
- No heatmap. Unchecked items use primary text color; checked items use dimmed color.

## Dev Commands (uv)
- Run app: `uv run python main.py`
- Add dependency: `uv add textual`
- Sync env: `uv sync`
- Example with list arg: `uv run python main.py groceries`

## Engineering Guidelines
- Favor small functions and direct state updates.
- Keep rendering and input handling separate.
- No background tasks or threading in MVP.
- On DB errors, show a concise error message and exit.
