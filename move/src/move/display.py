"""Display and formatting logic for move."""

from typing import List, Optional, Tuple

from .models import Box


def _room_label(room: Optional[str]) -> str:
    return room if room else "—"


def _pluralize(n: int, noun: str) -> str:
    return f"{n} {noun}{'s' if n != 1 else ''}"


def display_box_detail(box: Box) -> None:
    """Show one box: header line + items."""
    print(f"Box {box.label}  ·  {_room_label(box.room)}")
    if not box.items:
        print("  (no items)")
        return
    for item in box.items:
        print(f"  - {item.name}")


def display_boxes_summary(rows: List[Tuple[Box, int]]) -> None:
    """Display the short list-all view: label, room, item count."""
    if not rows:
        print("No boxes yet. Use 'move add <label> [items...]' to start.")
        return
    label_width = max((len(box.label) for box, _ in rows), default=5)
    for box, count in rows:
        room = _room_label(box.room)
        items_str = f"({_pluralize(count, 'item')})"
        print(f"  {box.label:<{label_width}}  {room:<14}  {items_str}")


def display_boxes_verbose(boxes: List[Box]) -> None:
    """Display the long list-all view: each box with its items."""
    if not boxes:
        print("No boxes yet. Use 'move add <label> [items...]' to start.")
        return
    label_width = max((len(b.label) for b in boxes), default=5)
    indent = " " * (label_width + 4)
    for i, box in enumerate(boxes):
        if i > 0:
            print()
        print(f"  {box.label:<{label_width}}  {_room_label(box.room)}")
        if not box.items:
            print(f"{indent}(no items)")
            continue
        for item in box.items:
            print(f"{indent}- {item.name}")
