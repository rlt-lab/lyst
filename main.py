from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from platformdirs import user_data_dir
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Input, Label, ListItem, ListView


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class ListRow:
    id: int
    title: str


@dataclass
class ItemRow:
    id: int
    text: str
    checked: int
    sort_order: int


class DB:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                list_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL,
                FOREIGN KEY(list_id) REFERENCES lists(id)
            )
            """
        )
        self.conn.commit()

    def lists(self) -> list[ListRow]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT id, title FROM lists ORDER BY updated_at DESC, id DESC"
        ).fetchall()
        return [ListRow(int(r["id"]), str(r["title"])) for r in rows]

    def get_list_by_title(self, title: str) -> Optional[ListRow]:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT id, title FROM lists WHERE title = ?", (title,)
        ).fetchone()
        if not row:
            return None
        return ListRow(int(row["id"]), str(row["title"]))

    def create_list(self, title: str) -> int:
        cur = self.conn.cursor()
        now = _now()
        cur.execute(
            "INSERT INTO lists (title, created_at, updated_at) VALUES (?, ?, ?)",
            (title, now, now),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def rename_list(self, list_id: int, title: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE lists SET title = ?, updated_at = ? WHERE id = ?",
            (title, _now(), list_id),
        )
        self.conn.commit()

    def delete_list(self, list_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM items WHERE list_id = ?", (list_id,))
        cur.execute("DELETE FROM lists WHERE id = ?", (list_id,))
        self.conn.commit()

    def items(self, list_id: int) -> list[ItemRow]:
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT id, text, checked, sort_order
            FROM items
            WHERE list_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (list_id,),
        ).fetchall()
        return [
            ItemRow(
                id=int(r["id"]),
                text=str(r["text"]),
                checked=int(r["checked"]),
                sort_order=int(r["sort_order"]),
            )
            for r in rows
        ]

    def add_item(self, list_id: int, text: str) -> int:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM items WHERE list_id = ?",
            (list_id,),
        ).fetchone()
        next_order = int(row["next_order"]) if row else 1
        cur.execute(
            "INSERT INTO items (list_id, text, checked, sort_order) VALUES (?, ?, 0, ?)",
            (list_id, text, next_order),
        )
        cur.execute(
            "UPDATE lists SET updated_at = ? WHERE id = ?",
            (_now(), list_id),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_item_text(self, item_id: int, text: str) -> None:
        cur = self.conn.cursor()
        cur.execute("UPDATE items SET text = ? WHERE id = ?", (text, item_id))
        self.conn.commit()

    def toggle_item(self, item_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE items SET checked = CASE checked WHEN 0 THEN 1 ELSE 0 END WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()

    def delete_item(self, list_id: int, item_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()
        self._normalize_order(list_id)

    def move_item(self, list_id: int, item_id: int, direction: int) -> None:
        items = self.items(list_id)
        index = next((i for i, item in enumerate(items) if item.id == item_id), None)
        if index is None:
            return
        target = index + direction
        if target < 0 or target >= len(items):
            return
        items[index], items[target] = items[target], items[index]
        self._rewrite_order(list_id, items)

    def _normalize_order(self, list_id: int) -> None:
        items = self.items(list_id)
        self._rewrite_order(list_id, items)

    def _rewrite_order(self, list_id: int, items: list[ItemRow]) -> None:
        cur = self.conn.cursor()
        for idx, item in enumerate(items, start=1):
            cur.execute(
                "UPDATE items SET sort_order = ? WHERE id = ?",
                (idx, item.id),
            )
        cur.execute(
            "UPDATE lists SET updated_at = ? WHERE id = ?",
            (_now(), list_id),
        )
        self.conn.commit()


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [
        ("y", "yes", "Yes"),
        ("n", "no", "No"),
        ("escape", "no", "No"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(self.message, id="modal-title")
            yield Label("Press y to confirm, n to cancel.", id="modal-help")

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)


class InputScreen(ModalScreen[Optional[str]]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str, value: str = "") -> None:
        super().__init__()
        self.title = title
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical(id="modal"):
            yield Label(self.title, id="modal-title")
            yield Input(value=self.value, placeholder="Type and press Enter")
            yield Label("Enter to save, Esc to cancel.", id="modal-help")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class MainScreen(Screen):
    BINDINGS = [
        Binding("tab", "switch_focus", "Switch Panel", show=True),
        Binding("shift+tab", "switch_focus", "Switch Panel", show=False),
        Binding("n", "new_list", "New List", show=True),
        Binding("r", "rename_list", "Rename", show=True),
        Binding("d", "delete", "Delete", show=True),
        Binding("a", "add_item", "Add Item", show=True),
        Binding("e", "edit_item", "Edit", show=True),
        Binding("[", "move_up", "Move Up", show=True),
        Binding("]", "move_down", "Move Down", show=True),
        Binding("q", "app.quit", "Quit", show=True),
    ]

    def __init__(self, db: DB, start_list: Optional[str] = None) -> None:
        super().__init__()
        self.db = db
        self.start_list = start_list
        self._list_rows: list[ListRow] = []
        self._item_rows: list[ItemRow] = []
        self._selected_list: Optional[ListRow] = None
        self._focus_panel: str = "lists"

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):
            with Vertical(id="lists-panel"):
                yield Label("Lists", id="lists-header")
                yield ListView(id="lists")
            with Vertical(id="items-panel"):
                yield Label("", id="items-header")
                yield ListView(id="items")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_lists()
        if self.start_list:
            name = self.start_list.strip()
            if name:
                row = self.db.get_list_by_title(name)
                if row is None:
                    list_id = self.db.create_list(name)
                    row = ListRow(list_id, name)
                    self.refresh_lists()
                self._select_list(row)
                self._focus_items()
                return
        self._focus_lists()

    def _focus_lists(self) -> None:
        self._focus_panel = "lists"
        self.query_one("#lists", ListView).focus()
        self._update_panel_borders()

    def _focus_items(self) -> None:
        self._focus_panel = "items"
        self.query_one("#items", ListView).focus()
        self._update_panel_borders()

    def _update_panel_borders(self) -> None:
        lists_panel = self.query_one("#lists-panel")
        items_panel = self.query_one("#items-panel")
        if self._focus_panel == "lists":
            lists_panel.add_class("active")
            items_panel.remove_class("active")
        else:
            lists_panel.remove_class("active")
            items_panel.add_class("active")

    def action_switch_focus(self) -> None:
        if self._focus_panel == "lists":
            self._focus_items()
        else:
            self._focus_lists()

    # --- Lists panel ---

    def refresh_lists(self) -> None:
        view = self.query_one("#lists", ListView)
        view.clear()
        self._list_rows = self.db.lists()
        if not self._list_rows:
            view.append(ListItem(Label("No lists yet \u2014 press n", classes="muted")))
            return
        for row in self._list_rows:
            prefix = "> " if self._selected_list and row.id == self._selected_list.id else "  "
            view.append(ListItem(Label(f"{prefix}{row.title}")))

    def _selected_list_row(self) -> Optional[ListRow]:
        if not self._list_rows:
            return None
        view = self.query_one("#lists", ListView)
        index = view.index
        if index is None or index < 0 or index >= len(self._list_rows):
            return None
        return self._list_rows[index]

    def _select_list(self, row: ListRow) -> None:
        self._selected_list = row
        self.query_one("#items-header", Label).update(row.title)
        self.refresh_items()
        self.refresh_lists()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv = event.list_view
        if lv.id == "lists":
            row = self._selected_list_row()
            if row:
                self._select_list(row)
        elif lv.id == "items":
            item = self._selected_item_row()
            if item and self._selected_list:
                self.db.toggle_item(item.id)
                self.refresh_items()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        lv = event.list_view
        if lv.id == "lists" and self._list_rows:
            index = lv.index
            if index is not None and 0 <= index < len(self._list_rows):
                row = self._list_rows[index]
                self._selected_list = row
                self.query_one("#items-header", Label).update(row.title)
                self.refresh_items()
                # Update the ">" prefix in the lists panel
                for i, child in enumerate(lv.children):
                    label = child.query_one(Label)
                    prefix = "> " if i == index else "  "
                    label.update(f"{prefix}{self._list_rows[i].title}")

    def action_new_list(self) -> None:
        def _on_result(value: Optional[str]) -> None:
            if not value:
                return
            list_id = self.db.create_list(value)
            row = ListRow(list_id, value)
            self.refresh_lists()
            self._select_list(row)

        self.app.push_screen(InputScreen("New list"), _on_result)

    def action_rename_list(self) -> None:
        if self._focus_panel != "lists":
            return
        row = self._selected_list_row()
        if not row:
            return

        def _on_result(value: Optional[str]) -> None:
            if not value:
                return
            self.db.rename_list(row.id, value)
            if self._selected_list and self._selected_list.id == row.id:
                self._selected_list = ListRow(row.id, value)
                self.query_one("#items-header", Label).update(value)
            self.refresh_lists()

        self.app.push_screen(InputScreen("Rename list", row.title), _on_result)

    def action_delete(self) -> None:
        if self._focus_panel == "lists":
            self._delete_list()
        else:
            self._delete_item()

    def _delete_list(self) -> None:
        row = self._selected_list_row()
        if not row:
            return

        def _on_result(confirmed: bool) -> None:
            if not confirmed:
                return
            self.db.delete_list(row.id)
            if self._selected_list and self._selected_list.id == row.id:
                self._selected_list = None
                self.query_one("#items-header", Label).update("")
                self._item_rows = []
                items_view = self.query_one("#items", ListView)
                items_view.clear()
                items_view.append(
                    ListItem(Label("Select a list", classes="muted"))
                )
            self.refresh_lists()

        self.app.push_screen(ConfirmScreen(f"Delete list '{row.title}'?"), _on_result)

    # --- Items panel ---

    def refresh_items(self) -> None:
        view = self.query_one("#items", ListView)
        view.clear()
        if not self._selected_list:
            view.append(ListItem(Label("Select a list", classes="muted")))
            return
        self._item_rows = self.db.items(self._selected_list.id)
        if not self._item_rows:
            view.append(ListItem(Label("No items yet \u2014 press a", classes="muted")))
            return
        for item in self._item_rows:
            box = "[x]" if item.checked else "[ ]"
            classes = "checked" if item.checked else ""
            view.append(ListItem(Label(f"{box} {item.text}", classes=classes)))

    def _selected_item_row(self) -> Optional[ItemRow]:
        if not self._item_rows:
            return None
        view = self.query_one("#items", ListView)
        index = view.index
        if index is None or index < 0 or index >= len(self._item_rows):
            return None
        return self._item_rows[index]

    def action_add_item(self) -> None:
        if not self._selected_list:
            return

        list_id = self._selected_list.id

        def _on_result(value: Optional[str]) -> None:
            if not value:
                return
            self.db.add_item(list_id, value)
            self.refresh_items()

        self.app.push_screen(InputScreen("New item"), _on_result)

    def action_edit_item(self) -> None:
        if self._focus_panel != "items":
            return
        item = self._selected_item_row()
        if not item:
            return

        def _on_result(value: Optional[str]) -> None:
            if not value:
                return
            self.db.update_item_text(item.id, value)
            self.refresh_items()

        self.app.push_screen(InputScreen("Edit item", item.text), _on_result)

    def _delete_item(self) -> None:
        if not self._selected_list:
            return
        item = self._selected_item_row()
        if not item:
            return
        list_id = self._selected_list.id

        def _on_result(confirmed: bool) -> None:
            if not confirmed:
                return
            self.db.delete_item(list_id, item.id)
            self.refresh_items()

        self.app.push_screen(ConfirmScreen("Delete this item?"), _on_result)

    def action_move_up(self) -> None:
        if self._focus_panel != "items" or not self._selected_list:
            return
        item = self._selected_item_row()
        if not item:
            return
        self.db.move_item(self._selected_list.id, item.id, -1)
        self.refresh_items()

    def action_move_down(self) -> None:
        if self._focus_panel != "items" or not self._selected_list:
            return
        item = self._selected_item_row()
        if not item:
            return
        self.db.move_item(self._selected_list.id, item.id, 1)
        self.refresh_items()


class LystApp(App):
    CSS = """
    Screen {
        background: #1f2430;
        color: #cccac2;
    }

    #main {
        height: 1fr;
        padding: 1 2;
    }

    #lists-panel {
        width: 30;
        border: round #171b24;
        padding: 1 2;
    }

    #lists-panel.active {
        border: round #ffcc66;
    }

    #items-panel {
        width: 1fr;
        border: round #171b24;
        padding: 1 2;
        margin-left: 1;
    }

    #items-panel.active {
        border: round #ffcc66;
    }

    #lists-header, #items-header {
        text-style: bold;
        color: #ffcc66;
        padding-bottom: 1;
    }

    ListView {
        height: 1fr;
        background: transparent;
    }

    ListView:focus {
        background: transparent;
    }

    ListItem {
        background: transparent;
    }

    ListItem.-highlight {
        background: #2b3245;
    }

    .checked {
        color: #505868;
    }

    .muted {
        color: #707a8c;
    }

    Footer {
        background: #1c212c;
        color: #cccac2;
    }

    Footer > .footer--highlight {
        background: #2b3245;
    }

    Footer > .footer--key {
        color: #cccac2;
        background: #2b3245;
    }

    Footer > .footer--description {
        color: #707a8c;
    }

    ModalScreen {
        align: center middle;
        background: rgba(31, 36, 48, 0.85);
    }

    #modal {
        width: 60;
        padding: 1 2;
        background: #282e3b;
        border: round #ffcc66;
    }

    #modal > * {
        margin-bottom: 1;
    }

    #modal-title {
        text-style: bold;
        color: #cccac2;
    }

    #modal-help {
        color: #707a8c;
    }

    Input {
        background: #1f2430;
        color: #cccac2;
        border: tall #505868;
    }

    Input:focus {
        border: tall #ffcc66;
    }
    """

    def __init__(self, db: DB, start_list: Optional[str] = None) -> None:
        super().__init__()
        self.db = db
        self.start_list = start_list

    async def on_mount(self) -> None:
        self.push_screen(MainScreen(self.db, self.start_list))


def main() -> None:
    data_dir = Path(user_data_dir("lyst"))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "lyst.db"
    try:
        db = DB(str(db_path))
    except sqlite3.Error as exc:
        print(f"Error: unable to open database at {db_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    start_list = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    LystApp(db, start_list).run()


if __name__ == "__main__":
    main()
