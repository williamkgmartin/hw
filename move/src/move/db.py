"""SQLite operations for move.

One connection per CLI operation, opened via the `connection()` context
manager. Writes inside a single `with connection()` block are wrapped in a
transaction (committed on normal exit, rolled back on exception).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple

from .config import get_config_dir
from .models import Box, Item


class MoveError(Exception):
    """Base exception for move app errors."""


class BoxNotFoundError(MoveError):
    def __init__(self, label: str):
        self.label = label
        super().__init__(f"no box with label '{label}'")


class BoxExistsError(MoveError):
    def __init__(self, label: str):
        self.label = label
        super().__init__(f"box '{label}' already exists")


def get_db_path() -> Path:
    return get_config_dir() / "move.db"


@contextmanager
def connection():
    """Yield a sqlite3 connection scoped to one CLI operation.

    The schema is created on first run. On normal exit, changes are committed;
    on exception, changes are rolled back. The connection is always closed.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(get_db_path()))
    conn.execute("PRAGMA foreign_keys = ON")
    _initialize_schema(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _initialize_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS boxes (
            id    INTEGER PRIMARY KEY,
            label TEXT NOT NULL UNIQUE COLLATE NOCASE,
            room  TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id     INTEGER PRIMARY KEY,
            box_id INTEGER NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
            name   TEXT NOT NULL
        )
        """
    )
    conn.commit()


# --- Reads ---


def _fetch_box(conn: sqlite3.Connection, label: str) -> Optional[Box]:
    row = conn.execute(
        "SELECT id, label, room FROM boxes WHERE label = ?", (label,)
    ).fetchone()
    if row is None:
        return None
    return Box(id=row[0], label=row[1], room=row[2], items=[])


def _fetch_items(conn: sqlite3.Connection, box_id: int) -> List[Item]:
    rows = conn.execute(
        "SELECT id, box_id, name FROM items WHERE box_id = ? ORDER BY id",
        (box_id,),
    ).fetchall()
    return [Item(id=r[0], box_id=r[1], name=r[2]) for r in rows]


def get_box(label: str) -> Box:
    """Return a box (with items). Raises BoxNotFoundError if missing."""
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        box.items = _fetch_items(conn, box.id)
        return box


def list_boxes_summary() -> List[Tuple[Box, int]]:
    """List all boxes paired with their item counts (items not loaded)."""
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.label, b.room, COUNT(i.id) AS n
            FROM boxes b
            LEFT JOIN items i ON i.box_id = b.id
            GROUP BY b.id
            ORDER BY b.label COLLATE NOCASE
            """
        ).fetchall()
        return [
            (Box(id=r[0], label=r[1], room=r[2], items=[]), r[3])
            for r in rows
        ]


def list_boxes_with_items() -> List[Box]:
    """List all boxes with items populated."""
    with connection() as conn:
        box_rows = conn.execute(
            "SELECT id, label, room FROM boxes ORDER BY label COLLATE NOCASE"
        ).fetchall()
        return [
            Box(
                id=r[0],
                label=r[1],
                room=r[2],
                items=_fetch_items(conn, r[0]),
            )
            for r in box_rows
        ]


def find_items_in_box(label: str, search: str) -> List[Item]:
    """Find items in a box by case-insensitive substring match on name."""
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        rows = conn.execute(
            """
            SELECT id, box_id, name FROM items
            WHERE box_id = ? AND LOWER(name) LIKE ?
            ORDER BY id
            """,
            (box.id, f"%{search.lower()}%"),
        ).fetchall()
        return [Item(id=r[0], box_id=r[1], name=r[2]) for r in rows]


def count_items(label: str) -> int:
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        return conn.execute(
            "SELECT COUNT(*) FROM items WHERE box_id = ?", (box.id,)
        ).fetchone()[0]


# --- Writes ---


def add_box(label: str, room: Optional[str], items: List[str]) -> int:
    """Create a new box with optional initial items.

    Returns the count of items added. Raises BoxExistsError if label exists.
    The existence check and inserts share one transaction.
    """
    with connection() as conn:
        if _fetch_box(conn, label) is not None:
            raise BoxExistsError(label)
        cur = conn.execute(
            "INSERT INTO boxes (label, room) VALUES (?, ?)", (label, room)
        )
        box_id = cur.lastrowid
        for item in items:
            conn.execute(
                "INSERT INTO items (box_id, name) VALUES (?, ?)",
                (box_id, item),
            )
        return len(items)


def add_items_to_box(label: str, items: List[str]) -> int:
    """Append items to an existing box. Returns count added."""
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        for item in items:
            conn.execute(
                "INSERT INTO items (box_id, name) VALUES (?, ?)",
                (box.id, item),
            )
        return len(items)


def delete_item(item_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def set_room(label: str, room: Optional[str]) -> None:
    """Set or clear the room for a box. Pass None to clear."""
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        conn.execute("UPDATE boxes SET room = ? WHERE id = ?", (room, box.id))


def delete_box(label: str) -> int:
    """Delete a box and (via cascade) all its items. Returns items deleted."""
    with connection() as conn:
        box = _fetch_box(conn, label)
        if box is None:
            raise BoxNotFoundError(label)
        n = conn.execute(
            "SELECT COUNT(*) FROM items WHERE box_id = ?", (box.id,)
        ).fetchone()[0]
        conn.execute("DELETE FROM boxes WHERE id = ?", (box.id,))
        return n


def rename_box(old_label: str, new_label: str) -> None:
    with connection() as conn:
        box = _fetch_box(conn, old_label)
        if box is None:
            raise BoxNotFoundError(old_label)
        # Allow case-only renames (e.g. "Box-11" → "BOX-11") by ignoring self.
        clash = conn.execute(
            "SELECT id FROM boxes WHERE label = ? AND id != ?",
            (new_label, box.id),
        ).fetchone()
        if clash:
            raise BoxExistsError(new_label)
        conn.execute(
            "UPDATE boxes SET label = ? WHERE id = ?", (new_label, box.id)
        )
