"""Dataclass models for move."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    id: int
    box_id: int
    name: str


@dataclass
class Box:
    id: int
    label: str
    room: Optional[str]
    items: List[Item] = field(default_factory=list)
