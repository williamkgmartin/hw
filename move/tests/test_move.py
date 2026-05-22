"""Smoke tests for the move app.

Covers the comma parser (a place where a regression would silently corrupt
input) and the basic DB lifecycle (a place where a regression would silently
corrupt stored data).
"""

import pytest

from move import db
from move.cli import _parse_items


@pytest.fixture(autouse=True)
def tmp_config(monkeypatch, tmp_path):
    """Point MOVE_CONFIG_DIR at a temp directory for every test."""
    monkeypatch.setenv("MOVE_CONFIG_DIR", str(tmp_path))
    yield tmp_path


# --- _parse_items ---


def test_parse_items_per_arg_mode():
    assert _parse_items(("lamp", "book", "chair")) == ["lamp", "book", "chair"]


def test_parse_items_quoted_multiword():
    assert _parse_items(("kitchen knife", "throw pillow")) == [
        "kitchen knife",
        "throw pillow",
    ]


def test_parse_items_comma_mode_with_spaces():
    assert _parse_items(("kitchen", "knife,", "throw", "pillow,", "lamp")) == [
        "kitchen knife",
        "throw pillow",
        "lamp",
    ]


def test_parse_items_comma_mode_no_spaces():
    assert _parse_items(("lamp,book,chair",)) == ["lamp", "book", "chair"]


def test_parse_items_strips_whitespace():
    assert _parse_items(("  lamp  ,  book  ",)) == ["lamp", "book"]


def test_parse_items_drops_empty_pieces():
    assert _parse_items(("lamp,, ,book",)) == ["lamp", "book"]


def test_parse_items_empty():
    assert _parse_items(()) == []


# --- schema + CRUD ---


def test_schema_initializes_clean():
    assert db.list_boxes_summary() == []


def test_add_and_get_box():
    db.add_box("11", "kitchen", ["knife", "book"])
    box = db.get_box("11")
    assert box.label == "11"
    assert box.room == "kitchen"
    assert [i.name for i in box.items] == ["knife", "book"]


def test_add_empty_box():
    db.add_box("12", None, [])
    box = db.get_box("12")
    assert box.room is None
    assert box.items == []


def test_label_unique_case_insensitive():
    db.add_box("Box-A", None, [])
    with pytest.raises(db.BoxExistsError):
        db.add_box("box-a", None, [])


def test_label_lookup_case_insensitive():
    db.add_box("Box-A", None, ["thing"])
    box = db.get_box("BOX-A")
    assert box.label == "Box-A"  # original casing preserved
    assert [i.name for i in box.items] == ["thing"]


def test_cascade_delete_removes_items():
    db.add_box("11", None, ["a", "b", "c"])
    box_id = db.get_box("11").id
    n = db.delete_box("11")
    assert n == 3
    with db.connection() as conn:
        leftover = conn.execute(
            "SELECT COUNT(*) FROM items WHERE box_id = ?", (box_id,)
        ).fetchone()[0]
        assert leftover == 0


def test_set_and_clear_room():
    db.add_box("11", None, [])
    db.set_room("11", "kitchen")
    assert db.get_box("11").room == "kitchen"
    db.set_room("11", None)
    assert db.get_box("11").room is None


def test_add_items_to_box():
    db.add_box("11", None, ["knife"])
    db.add_items_to_box("11", ["book", "chair"])
    box = db.get_box("11")
    assert [i.name for i in box.items] == ["knife", "book", "chair"]


def test_add_items_to_missing_box():
    with pytest.raises(db.BoxNotFoundError):
        db.add_items_to_box("99", ["lamp"])


def test_find_items_substring():
    db.add_box("11", None, ["knife", "book", "notebook"])
    matches = db.find_items_in_box("11", "book")
    assert sorted(m.name for m in matches) == ["book", "notebook"]


def test_delete_item():
    db.add_box("11", None, ["knife", "book"])
    matches = db.find_items_in_box("11", "kni")
    assert len(matches) == 1
    db.delete_item(matches[0].id)
    assert [i.name for i in db.get_box("11").items] == ["book"]


def test_rename_box():
    db.add_box("11", "kitchen", ["a"])
    db.rename_box("11", "11-fragile")
    box = db.get_box("11-fragile")
    assert box.label == "11-fragile"
    assert [i.name for i in box.items] == ["a"]
    with pytest.raises(db.BoxNotFoundError):
        db.get_box("11")


def test_rename_box_collision():
    db.add_box("11", None, [])
    db.add_box("12", None, [])
    with pytest.raises(db.BoxExistsError):
        db.rename_box("11", "12")


def test_rename_box_case_only():
    """Renaming 'Box-A' to 'BOX-A' should succeed (same row, case change)."""
    db.add_box("Box-A", None, [])
    db.rename_box("Box-A", "BOX-A")
    assert db.get_box("BOX-A").label == "BOX-A"


def test_list_boxes_summary_ordering_and_counts():
    db.add_box("b", None, ["x"])
    db.add_box("a", None, ["x", "y"])
    db.add_box("c", None, [])
    rows = db.list_boxes_summary()
    assert [box.label for box, _ in rows] == ["a", "b", "c"]
    assert [n for _, n in rows] == [2, 1, 0]


def test_list_boxes_with_items():
    db.add_box("11", "kitchen", ["knife"])
    db.add_box("12", None, [])
    boxes = db.list_boxes_with_items()
    assert [b.label for b in boxes] == ["11", "12"]
    assert [len(b.items) for b in boxes] == [1, 0]


def test_get_missing_box():
    with pytest.raises(db.BoxNotFoundError):
        db.get_box("nope")
