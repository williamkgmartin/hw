"""CLI interface for move."""

import sys
from typing import List, Optional, Tuple

import click

from . import db
from .display import display_box_detail, display_boxes_summary, display_boxes_verbose
from .models import Item


def _clean_label(label: str) -> str:
    """Strip surrounding whitespace. Errors out if the label is empty."""
    cleaned = label.strip()
    if not cleaned:
        click.echo("Error: label cannot be empty.", err=True)
        sys.exit(1)
    return cleaned


def _parse_items(args: Tuple[str, ...]) -> List[str]:
    """Parse a tuple of positional args into a list of item names.

    Two modes:
    - Comma mode: if ANY arg contains a comma, the whole tail is joined with
      spaces and split on commas; each piece is stripped.
    - Per-arg mode: no commas → each arg is one item (stripped).

    Empty pieces are dropped.
    """
    if any("," in a for a in args):
        joined = " ".join(args)
        return [p.strip() for p in joined.split(",") if p.strip()]
    return [a.strip() for a in args if a.strip()]


def _find_single_item(label: str, search: str) -> Item:
    """Locate exactly one item in a box by substring match, else error + exit."""
    try:
        matches = db.find_items_in_box(label, search)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)

    if not matches:
        click.echo(
            f"Error: no item matching '{search}' in box '{label}'.", err=True
        )
        sys.exit(1)
    if len(matches) > 1:
        click.echo(
            f"Error: {len(matches)} items match '{search}' in box '{label}'. "
            "Be more specific:",
            err=True,
        )
        for item in matches:
            click.echo(f"  - {item.name}", err=True)
        sys.exit(1)
    return matches[0]


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """move - CLI box tracker for managing a house move"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("label")
@click.argument("items", nargs=-1)
@click.option("--room", help="Room this box belongs to (e.g. kitchen)")
def add(label: str, items: Tuple[str, ...], room: Optional[str]):
    """Create a new box. Extra positional args become items."""
    label = _clean_label(label)
    item_list = _parse_items(items)

    try:
        n = db.add_box(label, room, item_list)
    except db.BoxExistsError:
        click.echo(
            f"Error: box '{label}' already exists. Use 'move add-item' to add items.",
            err=True,
        )
        sys.exit(1)

    room_str = f" in {room}" if room else ""
    if n > 0:
        items_str = f"{n} item{'s' if n != 1 else ''}"
        click.echo(f"Added box '{label}'{room_str} with {items_str}.")
    else:
        click.echo(f"Added empty box '{label}'{room_str}.")


@main.command(name="add-item")
@click.argument("label")
@click.argument("items", nargs=-1, required=True)
def add_item(label: str, items: Tuple[str, ...]):
    """Append one or more items to an existing box."""
    label = _clean_label(label)
    item_list = _parse_items(items)
    if not item_list:
        click.echo("Error: no items provided.", err=True)
        sys.exit(1)

    try:
        n = db.add_items_to_box(label, item_list)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)

    click.echo(f"Added {n} item{'s' if n != 1 else ''} to box '{label}'.")


@main.command(name="rm-item")
@click.argument("label")
@click.argument("item_search")
def rm_item(label: str, item_search: str):
    """Remove an item from a box (by substring match)."""
    label = _clean_label(label)
    item = _find_single_item(label, item_search)
    db.delete_item(item.id)
    click.echo(f"Removed '{item.name}' from box '{label}'.")


@main.command(name="set-room")
@click.argument("label")
@click.argument("room")
def set_room(label: str, room: str):
    """Set or replace the room for a box."""
    label = _clean_label(label)
    try:
        db.set_room(label, room)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)
    click.echo(f"Set room of box '{label}' to '{room}'.")


@main.command(name="clear-room")
@click.argument("label")
def clear_room(label: str):
    """Clear the room field on a box."""
    label = _clean_label(label)
    try:
        db.set_room(label, None)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)
    click.echo(f"Cleared room of box '{label}'.")


@main.command()
@click.argument("label")
def rm(label: str):
    """Delete a box and all its items."""
    label = _clean_label(label)
    try:
        n = db.count_items(label)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)

    if n > 0:
        click.echo(f"Box '{label}' has {n} item{'s' if n != 1 else ''}.")
        if not click.confirm("Delete it?", default=False):
            click.echo("Cancelled.")
            return

    db.delete_box(label)
    click.echo(f"Deleted box '{label}'.")


@main.command()
@click.argument("old_label")
@click.argument("new_label")
def rename(old_label: str, new_label: str):
    """Rename a box."""
    old_label = _clean_label(old_label)
    new_label = _clean_label(new_label)
    try:
        db.rename_box(old_label, new_label)
    except db.BoxNotFoundError as e:
        click.echo(f"Error: {e}.", err=True)
        sys.exit(1)
    except db.BoxExistsError:
        click.echo(f"Error: a box named '{new_label}' already exists.", err=True)
        sys.exit(1)
    click.echo(f"Renamed box '{old_label}' to '{new_label}'.")


@main.command(name="list")
@click.argument("label", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Show all items in each box")
def list_cmd(label: Optional[str], verbose: bool):
    """List all boxes, or show one box in detail when LABEL is given."""
    if label is not None:
        label = _clean_label(label)
        try:
            box = db.get_box(label)
        except db.BoxNotFoundError as e:
            click.echo(f"Error: {e}.", err=True)
            sys.exit(1)
        display_box_detail(box)
        return

    if verbose:
        display_boxes_verbose(db.list_boxes_with_items())
    else:
        display_boxes_summary(db.list_boxes_summary())


if __name__ == "__main__":
    main()
