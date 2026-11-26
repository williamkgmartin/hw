# move

A small CLI for tracking boxes during a house move. Each physical box gets a
label (matching what you wrote on it in Sharpie); the database tracks the
items inside and which room the box belongs to.

## Install

```sh
pip install -e .
```

## Usage

```sh
move add 11 knife book --room kitchen
move add 12 "kitchen knife", "throw pillow", lamp --room bedroom
move add-item 11 fork spoon
move rm-item 11 fork
move set-room 11 dining
move clear-room 11
move rename 11 11-fragile
move rm 11-fragile

move list                # all boxes, summary
move list -v             # all boxes, with items
move list 12             # one box, full detail
```

### Items: spaces in names

Two ways to enter multi-word items:

- Commas: `move add 11 kitchen knife, throw pillow, lamp`
- Shell-quoted: `move add 11 "kitchen knife" "throw pillow" lamp`

If any positional argument contains a comma, the whole tail is treated as a
comma-separated list. Otherwise each argument is one item.

## Data location

SQLite DB at `~/.move/move.db`. Override with `MOVE_CONFIG_DIR` (used by the
test suite).

## Tests

```sh
pip install -e '.[test]'
pytest
```
