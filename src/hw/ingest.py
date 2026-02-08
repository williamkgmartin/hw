"""JSON ingestion logic for hw"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .db import get_course_by_code, upsert_assignment
from .models import AssignmentCategory


VALID_CATEGORIES = {"exam", "project", "homework", "quiz", "reading"}


def ingest_file(file_path: Path) -> None:
    """Ingest assignments from a JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)

    course_code = data.get("course")
    if not course_code:
        raise ValueError(f"Missing 'course' field in {file_path}")

    # Verify course exists
    course = get_course_by_code(course_code)
    if not course:
        raise ValueError(
            f"No course with code '{course_code}'. Run 'hw courses' to see registered courses."
        )

    assignments = data.get("assignments", [])

    for assignment_data in assignments:
        title = assignment_data.get("title")
        due_str = assignment_data.get("due")
        category = assignment_data.get("category")

        # Validate required fields
        if not title:
            raise ValueError(f"Missing 'title' field in assignment: {assignment_data}")
        if not due_str:
            raise ValueError(f"Missing 'due' field in assignment: {assignment_data}")
        if not category:
            raise ValueError(f"Missing 'category' field in assignment: {assignment_data}")

        # Validate category
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )

        # Parse due date
        try:
            due_date = datetime.fromisoformat(due_str).date()
        except ValueError:
            raise ValueError(
                f"Invalid date format '{due_str}'. Expected YYYY-MM-DD."
            )

        # Upsert assignment
        assignment, was_created = upsert_assignment(
            course_code, title, due_date, category
        )

        # Print what was done
        symbol = "+" if was_created else "~"
        print(
            f"  {symbol} {course_code}: {title} ({category}) due {due_str}"
        )


def ingest_files(file_paths: List[str]) -> None:
    """Ingest assignments from multiple JSON files"""
    for file_path_str in file_paths:
        file_path = Path(file_path_str)

        if not file_path.exists():
            print(f"Error: file not found: {file_path}")
            continue

        try:
            ingest_file(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
