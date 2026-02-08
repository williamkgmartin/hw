"""Database operations for hw"""

import sqlite3
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from .config import get_config_dir
from .models import Assignment, AssignmentCategory, AssignmentStatus, Course


def get_db_path() -> Path:
    """Get the database file path (~/.hw/hw.db)"""
    return get_config_dir() / "hw.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, initializing the database if necessary"""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    # Initialize schema if needed
    _initialize_schema(conn)

    return conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL REFERENCES courses(id),
            title TEXT NOT NULL,
            due_date DATE NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('exam','project','homework','quiz','reading')),
            status TEXT NOT NULL DEFAULT 'todo' CHECK(status IN ('todo','done')),
            UNIQUE(course_id, title)
        )
        """
    )

    conn.commit()


# Course operations


def add_course(code: str, name: str) -> Course:
    """Add a new course"""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO courses (code, name) VALUES (?, ?)", (code, name)
    )
    course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return Course(id=course_id, code=code, name=name)


def get_course_by_code(code: str) -> Optional[Course]:
    """Get a course by its code"""
    conn = get_connection()
    cursor = conn.execute("SELECT id, code, name FROM courses WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return Course(id=row[0], code=row[1], name=row[2])
    return None


def list_courses() -> List[Course]:
    """List all courses"""
    conn = get_connection()
    cursor = conn.execute("SELECT id, code, name FROM courses ORDER BY code")
    courses = [Course(id=row[0], code=row[1], name=row[2]) for row in cursor.fetchall()]
    conn.close()
    return courses


def delete_course(code: str) -> int:
    """Delete a course and return the number of assignments deleted"""
    conn = get_connection()
    course = get_course_by_code(code)
    if not course:
        conn.close()
        return 0

    # Count assignments
    cursor = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE course_id = ?", (course.id,)
    )
    assignment_count = cursor.fetchone()[0]

    # Delete assignments and course
    conn.execute("DELETE FROM assignments WHERE course_id = ?", (course.id,))
    conn.execute("DELETE FROM courses WHERE id = ?", (course.id,))
    conn.commit()
    conn.close()

    return assignment_count


# Assignment operations


def add_assignment(
    course_code: str,
    title: str,
    due_date: date,
    category: AssignmentCategory,
) -> Assignment:
    """Add a new assignment"""
    course = get_course_by_code(course_code)
    if not course:
        raise ValueError(f"No course with code '{course_code}'")

    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO assignments (course_id, title, due_date, category, status)
        VALUES (?, ?, ?, ?, 'todo')
        """,
        (course.id, title, due_date.isoformat(), category),
    )
    assignment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return Assignment(
        id=assignment_id,
        course_id=course.id,
        course_code=course_code,
        title=title,
        due_date=due_date,
        category=category,
        status="todo",
    )


def upsert_assignment(
    course_code: str,
    title: str,
    due_date: date,
    category: AssignmentCategory,
) -> Tuple[Assignment, bool]:
    """
    Insert or update an assignment. Returns (assignment, was_created).
    If an assignment with the same course_id and title exists, updates it.
    """
    course = get_course_by_code(course_code)
    if not course:
        raise ValueError(f"No course with code '{course_code}'")

    conn = get_connection()

    # Try to find existing assignment
    cursor = conn.execute(
        """
        SELECT id, status FROM assignments
        WHERE course_id = ? AND title = ?
        """,
        (course.id, title),
    )
    existing = cursor.fetchone()

    if existing:
        # Update existing assignment
        assignment_id, status = existing
        conn.execute(
            """
            UPDATE assignments
            SET due_date = ?, category = ?
            WHERE id = ?
            """,
            (due_date.isoformat(), category, assignment_id),
        )
        conn.commit()
        conn.close()
        return (
            Assignment(
                id=assignment_id,
                course_id=course.id,
                course_code=course_code,
                title=title,
                due_date=due_date,
                category=category,
                status=status,
            ),
            False,
        )
    else:
        # Insert new assignment
        cursor = conn.execute(
            """
            INSERT INTO assignments (course_id, title, due_date, category, status)
            VALUES (?, ?, ?, ?, 'todo')
            """,
            (course.id, title, due_date.isoformat(), category),
        )
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return (
            Assignment(
                id=assignment_id,
                course_id=course.id,
                course_code=course_code,
                title=title,
                due_date=due_date,
                category=category,
                status="todo",
            ),
            True,
        )


def _row_to_assignment(row: Tuple) -> Assignment:
    """Convert a database row to an Assignment object"""
    from datetime import datetime

    return Assignment(
        id=row[0],
        course_id=row[1],
        course_code=row[2],
        title=row[3],
        due_date=datetime.fromisoformat(row[4]).date(),
        category=row[5],
        status=row[6],
    )


def find_assignments_by_title(
    course_code: str, title_search: str, status: Optional[AssignmentStatus] = None
) -> List[Assignment]:
    """
    Find assignments by substring match on title (case-insensitive).
    If status is provided, filter by that status.
    """
    course = get_course_by_code(course_code)
    if not course:
        return []

    conn = get_connection()

    query = """
        SELECT a.id, a.course_id, c.code, a.title, a.due_date, a.category, a.status
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        WHERE a.course_id = ? AND LOWER(a.title) LIKE ?
    """
    params = [course.id, f"%{title_search.lower()}%"]

    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.due_date"

    cursor = conn.execute(query, params)
    assignments = [_row_to_assignment(row) for row in cursor.fetchall()]
    conn.close()

    return assignments


def update_assignment_status(assignment_id: int, status: AssignmentStatus) -> None:
    """Update an assignment's status"""
    conn = get_connection()
    conn.execute("UPDATE assignments SET status = ? WHERE id = ?", (status, assignment_id))
    conn.commit()
    conn.close()


def update_assignment(
    assignment_id: int,
    title: Optional[str] = None,
    due_date: Optional[date] = None,
    category: Optional[AssignmentCategory] = None,
) -> None:
    """Update an assignment's fields"""
    conn = get_connection()

    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if due_date is not None:
        updates.append("due_date = ?")
        params.append(due_date.isoformat())

    if category is not None:
        updates.append("category = ?")
        params.append(category)

    if updates:
        query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?"
        params.append(assignment_id)
        conn.execute(query, params)
        conn.commit()

    conn.close()


def delete_assignment(assignment_id: int) -> None:
    """Delete an assignment"""
    conn = get_connection()
    conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()


def get_assignments_for_course(
    course_code: str, status_filter: Optional[str] = None
) -> List[Assignment]:
    """
    Get assignments for a course.
    status_filter can be None (incomplete only), 'all', or 'done'.
    """
    course = get_course_by_code(course_code)
    if not course:
        return []

    conn = get_connection()

    query = """
        SELECT a.id, a.course_id, c.code, a.title, a.due_date, a.category, a.status
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        WHERE a.course_id = ?
    """
    params = [course.id]

    if status_filter == "done":
        query += " AND a.status = 'done'"
    elif status_filter != "all":
        query += " AND a.status = 'todo'"

    query += " ORDER BY a.due_date"

    cursor = conn.execute(query, params)
    assignments = [_row_to_assignment(row) for row in cursor.fetchall()]
    conn.close()

    return assignments


def get_assignments_needing_attention(
    today: date, lead_times: dict, days_ahead: int = 0
) -> List[Assignment]:
    """
    Get incomplete assignments that need attention.

    An assignment needs attention if:
    - It's overdue, OR
    - days_until_due <= lead_time + days_ahead

    For 'hw now': days_ahead = 0
    For 'hw week': days_ahead = 7
    """
    conn = get_connection()

    query = """
        SELECT a.id, a.course_id, c.code, a.title, a.due_date, a.category, a.status
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        WHERE a.status = 'todo'
        ORDER BY a.due_date
    """

    cursor = conn.execute(query)
    all_assignments = [_row_to_assignment(row) for row in cursor.fetchall()]
    conn.close()

    # Filter by attention logic
    result = []
    for assignment in all_assignments:
        days_until = assignment.days_until_due(today)
        lead_time = lead_times.get(assignment.category, 0)

        if days_until < 0 or days_until <= lead_time + days_ahead:
            result.append(assignment)

    return result


def get_overdue_assignments(today: date) -> List[Assignment]:
    """Get all overdue incomplete assignments"""
    conn = get_connection()

    query = """
        SELECT a.id, a.course_id, c.code, a.title, a.due_date, a.category, a.status
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        WHERE a.status = 'todo'
        ORDER BY a.due_date
    """

    cursor = conn.execute(query)
    all_assignments = [_row_to_assignment(row) for row in cursor.fetchall()]
    conn.close()

    return [a for a in all_assignments if a.is_overdue(today)]
