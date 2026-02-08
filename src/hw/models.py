"""Data models for hw"""

from dataclasses import dataclass
from datetime import date
from typing import Literal


AssignmentCategory = Literal["exam", "project", "homework", "quiz", "reading"]
AssignmentStatus = Literal["todo", "done"]


@dataclass
class Course:
    """Represents a course"""

    id: int
    code: str
    name: str


@dataclass
class Assignment:
    """Represents an assignment"""

    id: int
    course_id: int
    course_code: str  # Denormalized for easier display
    title: str
    due_date: date
    category: AssignmentCategory
    status: AssignmentStatus

    def days_until_due(self, today: date) -> int:
        """Calculate days until due (negative if overdue)"""
        return (self.due_date - today).days

    def is_overdue(self, today: date) -> bool:
        """Check if assignment is overdue"""
        return self.days_until_due(today) < 0

    def is_due_today(self, today: date) -> bool:
        """Check if assignment is due today"""
        return self.days_until_due(today) == 0

    def attention_date(self, lead_time: int, today: date) -> date:
        """Calculate the date when this assignment needs attention"""
        from datetime import timedelta

        return self.due_date - timedelta(days=lead_time)

    def needs_attention(self, lead_time: int, today: date) -> bool:
        """Check if assignment needs attention based on lead time"""
        return today >= self.attention_date(lead_time, today)
