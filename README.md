# Lyst

A fast, keyboard-first TUI app for creating and managing multiple lists (to-dos, groceries, etc.).

## Install

### uv
```bash
uv sync
lyst
```

### pip
```bash
pip install .
lyst
```

### From wheel
```bash
uv pip install dist/lyst-0.1.0-py3-none-any.whl
# or
pip install dist/lyst-0.1.0-py3-none-any.whl
```

### Run without installing
```bash
uv run python main.py
# or
python main.py
```

## Usage
```bash
lyst              # open list index
lyst groceries    # open or create a list by name
```

## Key Bindings
- Global: `q` quit, `Esc` back.
- Index: `Enter/o` open, `n` new, `r` rename, `d` delete.
- Detail: `Enter` toggle, `a` add, `e` edit, `d` delete, `[` move up, `]` move down.

## Data
- SQLite stored at `~/.lyst/lyst.db` (via `platformdirs`).
