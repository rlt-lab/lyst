# Lyst

A fast, keyboard-first TUI app for creating and managing multiple lists (to-dos, groceries, etc.).

## Install

### uv
```bash
uv sync
lyst
lyst groceries
```

### pip
```bash
pip install .
lyst
lyst groceries
```

### Run without installing
```bash
uv run python main.py
# or
python main.py
python main.py groceries
```

## Key Bindings
- Global: `q` quit, `Esc` back.
- Index: `Enter/o` open, `n` new, `r` rename, `d` delete.
- Detail: `Enter` toggle, `a` add, `e` edit, `d` delete, `[` move up, `]` move down.

## Data
- SQLite stored at `~/.lyst/lyst.db` (via `platformdirs`).
