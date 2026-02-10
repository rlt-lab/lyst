# PRD: Lyst TUI Lists

## Summary
Lyst is a fast, keyboard-first TUI app for creating and managing multiple lists (to-dos, groceries, etc.). The interface is clean, modern, and minimal, optimized for low friction and small LOC.

## Goals
- Launch instantly and feel responsive on common terminals.
- Manage multiple lists with quick navigation and simple key bindings.
- Keep UI minimal: side-by-side two-panel layout (lists left, items right).
- Persist data locally with SQLite.
- Keep implementation minimal (small LOC, few dependencies).

## Non-Goals
- Cloud sync, collaboration, or accounts.
- Tags, search, filters, or advanced metadata.
- Mobile or GUI version.

## Core User Flows
1. Start app -> see lists in left panel, items for selected list in right panel.
2. Create a list, rename it, or delete it (confirm required).
3. In items panel: add, edit, delete, reorder, and check items.
4. Tab/Shift+Tab to switch focus between lists and items panels.
5. Optional: launch with a list name argument (e.g., `lyst groceries`) to open or create that list directly.

## UX & Interaction
- Side-by-side layout: lists panel (left, ~30 chars wide), items panel (right, fills remaining).
- Active panel border uses accent color (#ffcc66); inactive panel uses dim border.
- Arrow keys move selection within the focused panel.
- Tab / Shift+Tab switches focus between panels.
- Delete always requires a yes/no confirmation dialog.
- Inputs use a modal prompt overlay.
- Theme: Ayu Dusk (Mirage) — dark mellow palette. No heatmap. Unchecked items use primary text color; checked items are dimmed.
- Edit UX: modal input prompt (prefill existing text, `Enter` saves, `Esc` cancels).
- Context-sensitive footer shows available keybindings.
- CLI: if a list name is passed as an argument, open that list; create it if it does not exist.

## Key Bindings (MVP)
- Global: `q` quit, `Tab`/`Shift+Tab` switch panel.
- Lists panel: `n` new list, `r` rename, `d` delete list, `Enter` select list.
- Items panel: `a` add item, `e` edit, `d` delete item, `Enter` toggle check, `[` move up, `]` move down.

## Data & Persistence
- SQLite file stored locally at `~/.lyst/lyst.db` (via `platformdirs`).
- Tables: `lists(id INTEGER, title, created_at, updated_at)`, `items(id INTEGER, list_id INTEGER, text, checked, sort_order)`.
- Write on each mutation; load on startup.
- Sort order is based on user input sequence: first item gets the lowest `sort_order`, next item is second, etc. Reordering updates `sort_order` accordingly.
- Errors: if the DB cannot be opened or written, show a clear error message and exit to avoid data loss.

## Acceptance Criteria
- All key flows work without mouse input.
- Delete confirmation required for lists and items.
- Items can be reordered and checked off.
- Data persists across runs.

## Open Questions
- Whether to remember last-opened list.

## Planned Enhancements
- Add a console script entry later so `lyst <list-name>` works without `python main.py`.
