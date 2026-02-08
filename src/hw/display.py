"""Display and formatting logic for hw"""

from datetime import date
from typing import List

from .models import Assignment


def format_date(d: date) -> str:
    """Format a date as 'Feb 14' or similar"""
    return d.strftime("%b %d")


def format_category(category: str) -> str:
    """Format category as either [TAG] or (tag)"""
    major_categories = {"exam", "project"}

    if category in major_categories:
        return f"[{category.upper()}]"
    else:
        return f"({category})"


def format_days(days: int, is_overdue: bool) -> str:
    """Format the relative days string"""
    if is_overdue:
        abs_days = abs(days)
        if abs_days == 1:
            return "[1 day overdue]"
        else:
            return f"[{abs_days} days overdue]"
    else:
        if days == 0:
            return "[today]"
        elif days == 1:
            return "[1 day]"
        else:
            return f"[{days} days]"


def format_assignment_line(assignment: Assignment, today: date) -> str:
    """Format a single assignment line"""
    days = assignment.days_until_due(today)
    is_overdue = days < 0

    category_str = format_category(assignment.category)
    date_str = format_date(assignment.due_date)
    days_str = format_days(days, is_overdue)

    return f"  {assignment.course_code}  {category_str} {assignment.title}   due {date_str} {days_str}"


def format_assignment_line_with_status(
    assignment: Assignment, today: date, show_done: bool = False
) -> str:
    """Format assignment line, optionally showing done status"""
    line = format_assignment_line(assignment, today)

    if show_done and assignment.status == "done":
        return f"{line} [done]"

    return line


def display_assignments_grouped(assignments: List[Assignment], today: date) -> None:
    """
    Display assignments grouped into OVERDUE, DUE TODAY, and UPCOMING sections.
    Used by 'hw now', 'hw week', and 'hw overdue'.
    """
    if not assignments:
        print("Nothing on the radar.")
        return

    # Group assignments
    overdue = []
    due_today = []
    upcoming = []

    for assignment in assignments:
        days = assignment.days_until_due(today)
        if days < 0:
            overdue.append(assignment)
        elif days == 0:
            due_today.append(assignment)
        else:
            upcoming.append(assignment)

    # Sort each group
    overdue.sort(key=lambda a: a.due_date)  # Most overdue first
    due_today.sort(key=lambda a: a.course_code)  # By course code
    upcoming.sort(key=lambda a: a.due_date)  # Soonest first

    # Display sections
    if overdue:
        print("OVERDUE")
        for assignment in overdue:
            print(format_assignment_line(assignment, today))
        print()

    if due_today:
        print("DUE TODAY")
        for assignment in due_today:
            print(format_assignment_line(assignment, today))
        print()

    if upcoming:
        print("UPCOMING")
        for assignment in upcoming:
            print(format_assignment_line(assignment, today))


def display_course_assignments(
    assignments: List[Assignment], today: date, show_all: bool = False
) -> None:
    """
    Display assignments for a course.
    Used by 'hw list'.
    """
    if not assignments:
        print("No assignments found.")
        return

    for assignment in assignments:
        if show_all:
            print(format_assignment_line_with_status(assignment, today, show_done=True))
        else:
            print(format_assignment_line(assignment, today))
