# hw

A command-line assignment tracker for managing coursework across multiple classes. `hw` uses category-based lead times to surface assignments when you actually need to start thinking about them, rather than just showing everything due in the next week.

## Installation

### Linux

Install using `pipx`, which creates an isolated environment for the tool:

```bash
sudo apt install pipx
pipx ensurepath
pipx install /path/to/hw
```

For development or if you want changes to the code to take effect immediately:

```bash
pipx install -e /path/to/hw
```

### macOS

```bash
brew install pipx
pipx ensurepath
pipx install /path/to/hw
```

After installation, the `hw` command will be available globally.

## Quick Start

```bash
# Register your courses
hw add-course CS201 "Data Structures"
hw add-course MATH301 "Linear Algebra"

# Add some assignments
hw add CS201 "Problem Set 1" 2026-02-15 homework
hw add CS201 "Midterm Exam" 2026-03-10 exam

# Check what needs attention
hw now

# Mark assignments complete
hw done CS201 "Problem"
```

## How It Works

Each assignment has a category (`exam`, `project`, `homework`, `quiz`, `reading`) with a corresponding lead time measured in days. The lead time determines when an assignment enters your attention window. An exam with a 10-day lead time will show up in `hw now` once you're within 10 days of the due date.

Default lead times:
- `exam`: 10 days
- `project`: 7 days
- `homework`: 2 days
- `quiz`: 2 days
- `reading`: 1 day

You can adjust these in `~/.hw/config.toml` after first run.

## Commands

### Course Management

**List courses**
```bash
hw courses
```

**Add a course**
```bash
hw add-course CODE "Course Name"
```
Example: `hw add-course CS201 "Data Structures"`

**Remove a course**
```bash
hw rm-course CODE
```
Deletes the course and all its assignments. Prompts for confirmation if assignments exist.

### Adding and Managing Assignments

**Add an assignment**
```bash
hw add CODE "Title" YYYY-MM-DD CATEGORY
```
Example: `hw add CS201 "Problem Set 3" 2026-02-20 homework`

Valid categories: `exam`, `project`, `homework`, `quiz`, `reading`

**Mark as complete**
```bash
hw done CODE "search string"
```
Example: `hw done CS201 "Problem Set 3"` or just `hw done CS201 "Set 3"`

The search string matches any substring of the assignment title (case-insensitive). If multiple assignments match, you'll get an error asking you to be more specific. If exactly one matches, it gets marked done.

**Undo completion**
```bash
hw undo CODE "search string"
```
Same substring matching as `done`, but searches completed assignments.

**Edit an assignment**
```bash
hw edit CODE "search string" [--due YYYY-MM-DD] [--cat CATEGORY] [--title "New Title"]
```
Example: `hw edit CS201 "Midterm" --due 2026-03-15 --cat exam`

You can change the due date, category, title, or any combination. At least one flag is required.

**Delete an assignment**
```bash
hw rm CODE "search string"
```
Permanently removes the assignment.

### Viewing Assignments

**Show what needs attention now**
```bash
hw now
```
Displays assignments that are overdue, due today, or within their lead time window.

**Show the week ahead**
```bash
hw week
```
Like `hw now`, but extends the window by 7 days. Useful for weekly planning.

**Show only overdue items**
```bash
hw overdue
```

**List assignments for a course**
```bash
hw list CODE          # Incomplete assignments only
hw list CODE all      # All assignments (incomplete and completed)
hw list CODE done     # Completed assignments only
```

The output groups assignments into sections: `OVERDUE`, `DUE TODAY`, and `UPCOMING`. Overdue items show `[X days overdue]`, while future assignments show `[X days]`. Completed items in the `all` view are marked with `[done]`.

### Bulk Import

**Ingest from JSON**
```bash
hw ingest file.json
hw ingest *.json
```

JSON format:
```json
{
  "course": "CS201",
  "assignments": [
    {
      "title": "Problem Set 3",
      "due": "2026-02-18",
      "category": "homework"
    },
    {
      "title": "Midterm Exam",
      "due": "2026-03-15",
      "category": "exam"
    }
  ]
}
```

The course code must already exist in your database. If an assignment with the same title already exists for that course, `ingest` updates its due date and category rather than creating a duplicate.

Lines starting with `+` indicate new assignments; `~` indicates updates to existing ones.

### Using LLMs for JSON Generation

You can paste syllabus text into an LLM (Claude, ChatGPT, etc.) and ask it to generate JSON in the format above. This is faster than manual entry for courses with many assignments.

Example prompt:
> Extract all assignments from this syllabus and format them as JSON for the hw tool. Use course code CS201. Format: {"course": "CS201", "assignments": [{"title": "...", "due": "YYYY-MM-DD", "category": "homework|exam|project|quiz|reading"}]}

**Note on academic materials:** Be mindful of your institution's policies when using LLMs with private course materials. Some syllabi contain proprietary information or are covered by academic honor codes. If your syllabus is publicly available or your instructor has no restrictions, you're fine. Otherwise, check first or redact sensitive content.

## Data Storage

The tool stores its data in `~/.hw/`:
- `hw.db`: SQLite database containing courses and assignments
- `config.toml`: Lead time configuration

Both are created automatically on first run.

## Implementation

The codebase is straightforward Python with minimal dependencies. It uses Click for CLI argument parsing and SQLite for storage. No ORM—just raw SQL with the `sqlite3` module.

Structure:
- `cli.py`: Command definitions and CLI entry point
- `db.py`: Database initialization and query functions
- `config.py`: Config file reading and creation
- `models.py`: Data classes for Course and Assignment
- `display.py`: Output formatting logic
- `ingest.py`: JSON parsing and upsert logic

The database schema enforces a `UNIQUE(course_id, title)` constraint to prevent duplicate assignments. The `ingest` command uses this for upsert behavior: if an assignment already exists, it updates the due date and category rather than failing or creating a duplicate.

Lead time calculations happen in `db.py`. For each category, an assignment's "attention date" is `due_date - lead_time`. The `now` and `week` views fetch all incomplete assignments, then filter based on whether today is on or after the attention date. `week` extends this by 7 days.

Substring matching in `done`, `undo`, `edit`, and `rm` uses SQLite's case-insensitive `LIKE` with wildcards. If the search matches multiple assignments, the tool prints all matches and exits without modifying anything.

## License

This project has no formal license. It's a personal tool for tracking assignments.
