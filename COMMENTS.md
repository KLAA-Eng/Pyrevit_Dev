# Comment and Docstring Guide

This guide defines the repository standard for Python comments, Google-style
docstrings, command metadata, and ASCII-art section dividers. Apply it
to new code and to code that is materially changed.

The baseline is the [Google Python Style Guide][google-python-style],
[PEP 8][pep-8], and [PEP 257][pep-257]. Where this guide adds a rule, it is
for the pyRevit, Revit API, and IronPython context of this repository.

All examples use the fictional `Room Readiness Audit` command and illustrate
style only.

[google-python-style]: https://google.github.io/styleguide/pyguide.html
[pep-8]: https://peps.python.org/pep-0008/#comments
[pep-257]: https://peps.python.org/pep-0257/

## Principles

- Use docstrings to describe an interface: what callers may supply, what they
  receive, side effects, and relevant failures.
- Use comments to explain context that the code cannot express: a decision,
  external limitation, compatibility detail, or correctness rule.
- Do not narrate obvious code. Prefer a better name or a small helper when a
  comment only restates the next line.
- Write complete, concise sentences. Start comments and docstring summaries
  with a capital letter and end them with punctuation.
- Use triple double quotes (`"""`) for every Python docstring.
- Keep prose lines at 80 characters or fewer when practical.

## Google-Style Docstrings

Use the complete Google docstring format for every public function, class,
module, nontrivial private helper, and helper with non-obvious behavior. A
one-line docstring is acceptable only when the name, signature, and return
behavior make the full contract obvious.

Begin with a one-line summary followed by a blank line. Use these sections when
they apply, in this order:

1. Extended description
2. `Args:`
3. `Returns:` or `Yields:`
4. `Raises:`

Include each argument by its exact parameter name. When a function has no type
annotations—as is common in pyRevit/IronPython command paths—state the expected
type or host-API object in the argument description. Document side effects in
the extended description, especially model writes, file writes, UI prompts,
transactions, and process/resource lifecycle.

```python
def _room_ids_missing_department(document):
    """Return the IDs of rooms with no Department value.

    Inspects rooms in the active model without modifying the document.

    Args:
        document: Active Revit project document to inspect.

    Returns:
        A list of ElementId values for rooms missing a Department value.

    Raises:
        ValueError: The active document is not a project document.
    """
```

Describe a tuple as one return value, then name its parts in prose:

```python
def _set_room_status(room, status):
    """Set a Room Status parameter on one room.

    Args:
        room: Revit room element to update.
        status: Status text to write to the Room Status parameter.

    Returns:
        A tuple `(success, reason)`, where `success` is a boolean and `reason`
        is an empty string when the write succeeds.
    """
```

Do not include a `Returns:` section for a function that only returns `None`.
Do not document exceptions caused only by a caller violating the documented
contract. Do document meaningful interface failures that callers may need to
handle.

For a module-level Python docstring, make the literal the first statement in
the module. A command's `__doc__` assignment is KLMetadata, not a Python module
docstring; use the convention below instead.

## KLMetadata

Every user-facing `script.py` command MUST define `__version__` and the
user-facing `__doc__` command card. KLMetadata belongs directly after the
encoding declaration and any required `from __future__` imports, before normal
imports.

```python
__version__ = "0.1.0"
__doc__ = """Version: 0.1.0
_____________________________________________________________________
Description:

Inspect rooms in the active model and report rooms that are missing a Department
value.
_____________________________________________________________________
How-to:

-> Click the button
-> Review the pyRevit output report
-> Correct the reported room data in Revit
_____________________________________________________________________
Prototype limits:
- Inspects only the active project document
- Does not modify the Revit model
- Stops when no project document or rooms are available
_____________________________________________________________________
Author: KL&A"""
```

Rules for this block:

- `__version__` is a repository convention for the command's release or
  prototype status.
- `__doc__` is the user-facing command card. Use the ordered sections shown
  above: `Version`, `Description`, `How-to`, applicable limits/requirements,
  and `Author`.
- Use the 69-underscore divider exactly as shown to separate command-card
  sections. Keep the content accurate to observed behavior.
- State destructive or externally visible side effects, required workstation
  software, fixed input counts, and conditions that stop the command.
- Update `__version__` and the `Version:` line together.

The normal Google module-docstring rule still applies to reusable `lib/` modules
when they need module documentation. Do not add a second long user guide to a
command script solely to satisfy that rule.

## Inline and Block Comments

Comments are a teaching aid in this repository. Add them liberally around
unfamiliar Revit, pyRevit, Excel COM, and IronPython behavior, but make each
comment answer a question the code cannot answer for a new maintainer:

- **Why is this necessary?** Explain a business rule, data assumption, or
  non-obvious decision.
- **What does the host API do here?** Explain a Revit, pyRevit, or Excel COM
  behavior that differs from ordinary Python.
- **What would break if this changed?** Explain resource ownership, a
  transaction boundary, a workbook contract, or a correctness rule.
- **What is this small step accomplishing?** Explain a transformation or
  fallback when the variable names alone do not make it clear.

Do not narrate ordinary Python syntax or repeat a clear name. For example,
`for room in rooms:` does not need a comment; a comment is useful when the
loop deliberately skips linked-model rooms, preserves order, or prepares data
for a later Revit transaction.

### Choosing a comment style

Use a block comment immediately above a related sequence of statements. Prefer
it for a decision, an API limitation, a multi-step transformation, resource
ownership, or failure handling. This is the default style for beginner-facing
explanations.

```python
# Revit collectors are lazy. Materialize this one before counting and iterating
# so the same result set is used for both operations.
rooms = list(room_collector)
for room in rooms:
    ...

# Build report-ready text here so every caller displays the same value.
return formatted_report
```

Use an inline (trailing) comment when a single statement needs a short reason,
unit, boundary, or external constraint. It MUST be separated from the code by
at least two spaces, start with `# `, and remain short enough that the complete
line is easy to scan. Use a block comment instead when the explanation needs
more than one sentence or applies to more than one statement.

```python
COMMAND_TITLE = "Room Readiness Audit"  # User-facing report title.

first_excel_row = 1  # Excel COM collections use one-based indexes.
```

Do not vertically align inline comments. Avoid comments that merely repeat the
code:

```python
# Avoid: the condition already states this.
# Skip rooms without a department.
if not room.Department:
    continue

# Prefer: explain the rule that is not apparent from the condition.
# Department is optional in early design phases, so exclude those rooms from
# the final readiness score instead of treating them as failed rooms.
if not room.Department:
    continue
```

### Beginner-friendly placement rules

Apply these rules while writing or reviewing command code:

1. Comment a meaningful block before its first statement, rather than adding a
   comment to every line inside it.
2. Add a short inline comment to a literal only when its unit, source, or
   constraint is not already named. Prefer a named constant when it is reused.
3. Comment each non-obvious API boundary: collector behavior, COM indexing,
   document transactions, file ownership, workbook refreshes, and API-version
   fallbacks.
4. Comment error recovery where the `except` clause intentionally continues,
   falls back, or changes the user-visible result. State why that is safe.
5. Comment transformations at the point where data changes shape, units, or
   meaning. Name the input and the resulting contract.
6. Keep a comment next to the code it explains. Update or remove it whenever
   the related behavior changes.

### Workflow-phase comments

For a command with a multi-step workflow, add a short action-oriented comment
before every meaningful phase. This style is inspired by EF-Tools' beginner
examples, but uses plain text instead of emojis so comments remain searchable,
accessible, and consistent in every editor.

Start with a verb that describes the result of the next block: **Collect**,
**Filter**, **Validate**, **Transform**, **Select**, **Open**, **Write**,
**Report**, or **Clean up**. Add a second sentence only when a beginner needs
to know why the phase exists, what host-API rule applies, or what happens when
it fails.

```python
# Collect all project views, then retain only the templates that can receive
# the selected filter. Revit returns both views and templates in this collector.
view_templates = [view for view in views if view.IsTemplate]

# Validate the selection before starting a transaction. Cancelling here leaves
# the model unchanged and avoids opening a transaction with no work to perform.
if not selected_templates:
    forms.alert("Select at least one template.", exitscript=True)

# Write the changes inside one transaction so Revit can undo the complete
# operation if a later update fails.
with revit.Transaction("Copy View Filters"):
    _copy_filters(selected_templates)
```

Use one workflow-phase comment per cohesive block, not one label per line.
Subsequent comments inside the block should explain only a distinct API detail,
conversion, fallback, or safety constraint. Keep the existing tagged-comment
rules for persistent compatibility, workaround, and invariant information.

Use these patterns as starting points:

```python
# Revit returns internal feet. Convert before comparing against the
# millimeter-based office standard used by this command.
clearance_mm = DB.UnitUtils.ConvertFromInternalUnits(
    clearance_feet,
    DB.UnitTypeId.Millimeters)

# The post-processing workbook owns the formulas. Open it read-only so this
# command can refresh values without overwriting the analyst's workbook.
workbook = excel.Workbooks.Open(path, ReadOnly=True)

# Keep all model changes in one transaction so Cancel rolls back the complete
# update instead of leaving some family types updated.
with revit.Transaction("Update Room Status"):
    _write_statuses(rooms)

try:
    worksheet.Cells.Clear()
except Exception:
    # Some Excel COM wrappers expose only UsedRange.Clear; both calls remove
    # stale export values before the current, potentially smaller grid is set.
    worksheet.UsedRange.Clear()
```

Before adding a comment, ask: "Would a capable new maintainer know the reason
for this line or block from the names and surrounding code?" If yes, omit the
comment. If no, add the shortest complete explanation that gives the reason.

## Tagged Comments

Use only the following uppercase tags. Put the tag at the beginning of a block
comment in the form `# TAG: ...`; do not bury a tag in a trailing comment.

| Tag | Use | Required content | Example |
| --- | --- | --- | --- |
| `TODO` | Known incomplete or improvable work. | An issue link/reference **or** a precise, observable removal condition. | `# TODO: GH-123 - Add linked-model room checks before the next audit release.` |
| `FIXME` | Known wrong or fragile behavior that can affect results. | The failure/risk and a tracker or precise exit condition. | `# FIXME: GH-456 - Later-phase rooms are missing from the audit report.` |
| `DEPRECATED` | A callable, path, or behavior remains available but must not be used for new code. | The replacement and removal condition. | `# DEPRECATED: Use _room_ids_missing_department(); remove after version 1.0.` |
| `COMPAT` | Version- or environment-specific behavior. | Affected versions/environments and why the branch exists. | `# COMPAT: Revit 2024+ exposes Value; older versions expose IntegerValue.` |
| `WORKAROUND` | A limitation or defect in an external API, product, or file contract. | The external cause and the condition for removing the workaround when known. | `# WORKAROUND: Check Department values one room at a time; the API has no blank-value filter.` |
| `INVARIANT` | A rule that must remain true for correctness, safety, or data integrity. | The rule and, when useful, the consequence of violating it. | `# INVARIANT: Do not modify rooms while collecting audit results.` |

Use a repository issue, a stable external issue URL, or an unambiguous migration
event as the reference. Do not use a person or team name as a substitute for
context. Remove the tagged comment when the associated condition is resolved.

Do not introduce `HACK`, `XXX`, `NOTE`, `DONE`, or ad hoc variants. Their
meaning is either ambiguous or better expressed by one of the standard tags.

## ASCII-Art Section Dividers

This repository intentionally uses ASCII-art section dividers in pyRevit command
scripts. They are a visual navigation aid, not a substitute for a semantic
heading. Retain the established three-line art plus separator for major command
sections, such as imports, variables, functions, and the main entry point.

Follow every ASCII-art divider with a plain-text section label so the section is
searchable and understandable without interpreting the art:

```python
# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
# ==================================================================
# Functions
# ------------------------------------------------------------------
```

Use the same divider shape consistently within a script. Use ordinary
plain-text subsection headings for smaller groups:

```python
# Room collection helpers
# ------------------------------------------------------------------
```

Do not use ASCII art for individual functions, short branches, or decorative
spacing. The label is required even when the art visually spells the section
name.

## Review Checklist

- Does every required docstring use Google-style summary, blank line, and
  applicable `Args:`, `Returns:`/`Yields:`, and `Raises:` sections?
- Does each docstring describe the interface rather than implementation trivia?
- Are Revit transactions, external-resource ownership, and meaningful side
  effects documented where callers need to know them?
- Does each tagged comment use an approved tag and include the required context?
- Does each KLMetadata block use `__version__`, the ordered command card, and
  matching version strings?
- Does every ASCII-art divider have an adjacent plain-text section label?
- Did the change avoid adding redundant narration or unnecessary comment churn?
