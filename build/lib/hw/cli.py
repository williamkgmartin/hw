"""CLI interface for hw"""

import sys
from datetime import date, datetime

import click

from . import db
from .config import load_lead_times
from .display import (
    display_assignments_grouped,
    display_course_assignments,
    format_assignment_line,
)
from .ingest import ingest_files


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """hw - CLI assignment tracker for college courses"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Course management commands


@main.command()
def courses():
    """List all registered courses"""
    course_list = db.list_courses()

    if not course_list:
        click.echo("No courses registered yet. Use 'hw add-course' to add one.")
        return

    for course in course_list:
        click.echo(f"{course.code}  {course.name}")


@main.command(name="add-course")
@click.argument("code")
@click.argument("name")
def add_course(code: str, name: str):
    """Register a new course"""
    try:
        db.add_course(code, name)
        click.echo(f"Added course: {code} - {name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command(name="rm-course")
@click.argument("code")
def rm_course(code: str):
    """Remove a course and all its assignments"""
    course = db.get_course_by_code(code)
    if not course:
        click.echo(f"Error: no course with code '{code}'.", err=True)
        sys.exit(1)

    # Get assignment count
    assignments = db.get_assignments_for_course(code, status_filter="all")
    count = len(assignments)

    # Confirm
    if count > 0:
        click.echo(
            f"This will delete {count} assignment{'s' if count != 1 else ''} for {code}."
        )
        if not click.confirm("Are you sure?", default=False):
            click.echo("Cancelled.")
            return

    db.delete_course(code)
    click.echo(f"Deleted course: {code}")


# Assignment management commands


@main.command()
@click.argument("code")
@click.argument("title")
@click.argument("due_date")
@click.argument("category")
def add(code: str, title: str, due_date: str, category: str):
    """Add a single assignment"""
    # Validate course
    course = db.get_course_by_code(code)
    if not course:
        click.echo(
            f"Error: no course with code '{code}'. Run 'hw courses' to see registered courses.",
            err=True,
        )
        sys.exit(1)

    # Validate category
    valid_categories = {"exam", "project", "homework", "quiz", "reading"}
    if category not in valid_categories:
        click.echo(
            f"Error: invalid category '{category}'. Must be one of: {', '.join(sorted(valid_categories))}",
            err=True,
        )
        sys.exit(1)

    # Parse date
    try:
        due = datetime.fromisoformat(due_date).date()
    except ValueError:
        click.echo(
            f"Error: invalid date format '{due_date}'. Expected YYYY-MM-DD.",
            err=True,
        )
        sys.exit(1)

    # Add assignment
    try:
        db.add_assignment(code, title, due, category)
        click.echo(f"Added: {title} ({category}) due {due_date}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _find_single_assignment(code: str, title_search: str, status: str = "todo"):
    """
    Helper to find a single assignment by substring match.
    Returns the assignment if exactly one match, otherwise prints error and exits.
    """
    course = db.get_course_by_code(code)
    if not course:
        click.echo(
            f"Error: no course with code '{code}'.",
            err=True,
        )
        sys.exit(1)

    matches = db.find_assignments_by_title(code, title_search, status=status)

    if len(matches) == 0:
        status_str = "completed" if status == "done" else "incomplete"
        click.echo(
            f"Error: no {status_str} assignment matching '{title_search}' found for {code}.",
            err=True,
        )
        sys.exit(1)
    elif len(matches) > 1:
        click.echo(
            f"Error: multiple assignments match '{title_search}'. Be more specific:",
            err=True,
        )
        today = date.today()
        for assignment in matches:
            click.echo(f"  - {assignment.title} (due {assignment.due_date})", err=True)
        sys.exit(1)

    return matches[0]


@main.command()
@click.argument("code")
@click.argument("title_search")
def done(code: str, title_search: str):
    """Mark an assignment as complete"""
    assignment = _find_single_assignment(code, title_search, status="todo")

    db.update_assignment_status(assignment.id, "done")
    click.echo(f"Marked as done: {assignment.title}")


@main.command()
@click.argument("code")
@click.argument("title_search")
def undo(code: str, title_search: str):
    """Un-mark a completed assignment"""
    assignment = _find_single_assignment(code, title_search, status="done")

    db.update_assignment_status(assignment.id, "todo")
    click.echo(f"Marked as todo: {assignment.title}")


@main.command()
@click.argument("code")
@click.argument("title_search")
@click.option("--due", help="New due date (YYYY-MM-DD)")
@click.option("--cat", help="New category")
@click.option("--title", help="New title")
def edit(code: str, title_search: str, due: str, cat: str, title: str):
    """Edit an assignment's due date, category, or title"""
    if not due and not cat and not title:
        click.echo("Error: at least one of --due, --cat, or --title is required.", err=True)
        sys.exit(1)

    assignment = _find_single_assignment(code, title_search, status="todo")

    # Parse new values
    new_due_date = None
    if due:
        try:
            new_due_date = datetime.fromisoformat(due).date()
        except ValueError:
            click.echo(
                f"Error: invalid date format '{due}'. Expected YYYY-MM-DD.",
                err=True,
            )
            sys.exit(1)

    new_category = None
    if cat:
        valid_categories = {"exam", "project", "homework", "quiz", "reading"}
        if cat not in valid_categories:
            click.echo(
                f"Error: invalid category '{cat}'. Must be one of: {', '.join(sorted(valid_categories))}",
                err=True,
            )
            sys.exit(1)
        new_category = cat

    new_title = title

    # Update
    db.update_assignment(assignment.id, title=new_title, due_date=new_due_date, category=new_category)
    click.echo(f"Updated: {assignment.title}")


@main.command()
@click.argument("code")
@click.argument("title_search")
def rm(code: str, title_search: str):
    """Delete an assignment"""
    assignment = _find_single_assignment(code, title_search, status="todo")

    db.delete_assignment(assignment.id)
    click.echo(f"Deleted: {assignment.title}")


# Ingestion command


@main.command()
@click.argument("files", nargs=-1, required=True)
def ingest(files):
    """Bulk import assignments from JSON files"""
    ingest_files(list(files))


# View commands


@main.command()
def now():
    """Show assignments needing attention now"""
    today = date.today()
    lead_times = load_lead_times()

    assignments = db.get_assignments_needing_attention(today, lead_times, days_ahead=0)
    display_assignments_grouped(assignments, today)


@main.command()
def week():
    """Show assignments needing attention within the next week"""
    today = date.today()
    lead_times = load_lead_times()

    assignments = db.get_assignments_needing_attention(today, lead_times, days_ahead=7)
    display_assignments_grouped(assignments, today)


@main.command()
def overdue():
    """Show only overdue incomplete assignments"""
    today = date.today()

    assignments = db.get_overdue_assignments(today)
    display_assignments_grouped(assignments, today)


@main.command(name="list")
@click.argument("code")
@click.argument("filter", required=False)
def list_assignments(code: str, filter: str):
    """List assignments for a course (incomplete by default, or 'all'/'done')"""
    course = db.get_course_by_code(code)
    if not course:
        click.echo(
            f"Error: no course with code '{code}'.",
            err=True,
        )
        sys.exit(1)

    status_filter = None
    if filter == "all":
        status_filter = "all"
    elif filter == "done":
        status_filter = "done"
    elif filter is not None:
        click.echo(
            f"Error: invalid filter '{filter}'. Use 'all' or 'done'.",
            err=True,
        )
        sys.exit(1)

    assignments = db.get_assignments_for_course(code, status_filter=status_filter)
    today = date.today()

    display_course_assignments(assignments, today, show_all=(status_filter == "all"))


if __name__ == "__main__":
    main()
