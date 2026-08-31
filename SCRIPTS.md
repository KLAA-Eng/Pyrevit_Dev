# Python Script Guide

This guide defines the repository standard for organizing Python code in this
pyRevit extension. It complements `COMMENTS.md`, which remains the source of
truth for comments, docstrings, KLMetadata, tagged comments, and ASCII-art
section dividers.

The baseline is the [PEP 8 style guide][pep-8], [PEP 257 docstring
conventions][pep-257], the [Google Python Style Guide][google-python-style],
pyRevit's documented extension and command runtime model, and current Revit API
references such as [Revit API Docs][revit-api-docs] and [RVTDocs][rvtdocs].
Where this guide adds a stricter rule, it is for the Revit API, pyRevit,
IronPython, and KLCode maintenance context.

The EF StarterKit checkout at
`C:\Users\lmadden\KLCode.dev.local\pyRevit.repos\EF-StarterKit.clone` is a
useful beginner-facing reference for command shape, metadata, visible workflow
sections, and reusable `lib` examples. Adapt those ideas to this repository's
style instead of copying the template verbatim.

[google-python-style]: https://google.github.io/styleguide/pyguide.html
[pep-8]: https://peps.python.org/pep-0008/
[pep-257]: https://peps.python.org/pep-0257/
[pyrevit-architecture]: https://docs.pyrevitlabs.io/architecture/
[pyrevit-extensions]: https://docs.pyrevitlabs.io/reference/pyrevit/extensions/
[revit-api-docs]: https://www.revitapidocs.com/
[rvtdocs]: https://rvtdocs.com/

## Principles

- Prefer readable, boring Python over clever code.
- Keep pyRevit command scripts as thin adapters over the pyRevit, Revit, WPF,
  Excel COM, or filesystem APIs they need to call.
- Put deterministic, host-independent logic in `lib/` so it can be tested
  without Revit.
- Keep side effects explicit: model writes, transactions, user prompts, file
  writes, process launches, workbook ownership, and output reporting.
- Preserve existing command behavior during formatting or documentation passes
  unless the task explicitly asks for behavior changes.

PEP 8 explicitly allows project-specific guides to take precedence where local
constraints require it. In this repository, compatibility with pyRevit and the
surrounding command bundle style is one of those constraints.

## Compatibility

User-facing `script.py` command paths must remain compatible with the pyRevit
engine that runs them. Unless a command explicitly opts into CPython, write
command code for IronPython/Python 2.7 compatibility.

Avoid these in ordinary command scripts:

- f-strings
- function or variable annotations
- dataclasses
- `pathlib`-only path handling
- CPython-only packages or syntax
- Python 3-only standard-library APIs

Use `from __future__ import print_function` when a command or helper prints
directly. Keep text handling defensive around Revit, Excel COM, and .NET values
because they do not always behave like normal Python strings.

Python 3-friendly helper code is acceptable in `lib/` only when it does not
break any command path that imports it under pyRevit. If a helper is intended
for CPython tooling only, name and document that boundary clearly.

## File Roles

### `script.py`

Use command scripts for pyRevit entry-point work:

- Read the active Revit context.
- Prompt for user selections and files.
- Call Revit, WPF, Excel COM, or other host APIs.
- Validate inputs before model writes.
- Open and close external resources owned by the command.
- Start and commit Revit transactions.
- Render pyRevit output reports and user alerts.

Non-trivial command scripts should define `main()` and call it under
`if __name__ == '__main__':`. Keep the top-level body limited to metadata,
imports, constants, function/class definitions, and the guarded entry point.

### `lib/`

Use `lib/` for reusable or testable code:

- Data parsing and normalization.
- String, unit, path, and worksheet-name formatting.
- Validation rules and skip classification.
- Report row construction.
- Reusable UI helpers used by more than one command.

Do not make pure helpers import `__revit__`, pyRevit forms, WPF windows, Excel
COM, or Revit DB classes unless those APIs are truly part of the helper's job.
If a helper needs host objects, keep the expected object contract clear in the
docstring.

### `tests/`

Tests should cover host-independent behavior first. Favor tests around `lib/`
functions and mocked command-adapter logic over tests that require live Revit,
Excel, or network drives.

Design return values so tests can assert:

- successful rows or elements
- skipped rows or elements
- skip reasons
- normalized names, units, and values
- failure messages that affect the user report

### `SPEC.md`

Each user-facing command should use `SPEC.md` for the operational contract:

- what the command does
- expected inputs
- user prompts
- excluded elements or unsupported cases
- model or file outputs
- acceptance notes for manual Revit validation

Keep implementation details in code comments and docstrings. Keep user behavior
and testing expectations in `SPEC.md`.

## Script Layout

Use the existing KLCode command shape for new or materially changed scripts:

1. Encoding declaration.
2. Required `from __future__` imports.
3. KLMetadata block: `__title__`, `__author__` when known, `__version__`, and
   `__doc__`.
4. Major `COMMENTS.md` section divider for imports.
5. Imports grouped by standard library, pyRevit/Revit/.NET, then local `lib`.
6. Command setup and constants.
7. Helper functions.
8. Classes, only when a command needs WPF or stateful behavior.
9. `main()`.
10. Guarded command entry point.

Use the `COMMENTS.md` rules for the exact KLMetadata card, Google-style
docstrings, tagged comments, and ASCII-art dividers. Do not add a second
module-level docstring to a command script solely to satisfy generic Python
style guidance; the command card is the user-facing command documentation.

Example skeleton:

```python
# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Room Readiness Audit"
__author__ = "KL&A"
__version__ = "0.1.0"
__doc__ = """Version: 0.1.0
_____________________________________________________________________
Description:

Inspect rooms in the active model and report rooms that need review.
_____________________________________________________________________
How-to:

-> Click the button
-> Review the pyRevit output report
_____________________________________________________________________
Author: KL&A"""

# Major Imports divider from COMMENTS.md goes here.

import os

from pyrevit import DB, forms, revit, script


COMMAND_TITLE = __title__


def _collect_rooms(document):
    """Return project rooms from the active document.

    Args:
        document: Active Revit project document.

    Returns:
        A list of Revit room elements.
    """
    return list(DB.FilteredElementCollector(document).OfCategory(
        DB.BuiltInCategory.OST_Rooms))


def main():
    """Run the room readiness audit."""
    document = revit.doc
    rooms = _collect_rooms(document)
    if not rooms:
        forms.alert("No rooms were found.", title=COMMAND_TITLE)
        return

    output = script.get_output()
    output.print_md("# {}".format(COMMAND_TITLE))
    output.print_md("Rooms reviewed: {}".format(len(rooms)))


if __name__ == '__main__':
    main()
```

## Imports

Prefer explicit imports for new code. PEP 8 discourages wildcard imports
because they hide where names come from and make automated checks weaker.

Recommended for new command code:

```python
from pyrevit import DB, forms, revit, script
```

Use direct Autodesk or .NET imports when the local codebase already does so or
when the explicit type is clearer:

```python
from Autodesk.Revit.Exceptions import ArgumentException
from System.Diagnostics.Process import Start
```

Avoid this in new code unless preserving a legacy script during a narrow edit:

```python
from Autodesk.Revit.DB import *
```

If a deeply nested command needs to import from extension `lib/`, keep the path
setup small, local, and explained. Prefer a reusable helper for finding the
extension root when several commands need the same setup.

## Revit API Boundaries

Validate early and write late:

- Collect and normalize Revit data before starting a transaction when possible.
- Prompt and validate user selections before any model write.
- Cancel by returning cleanly before external work or model changes begin.
- Keep model writes inside the smallest clear transaction that matches the
  user's undo expectation.
- Use one transaction for one coherent user action, not one transaction per
  element unless the command needs partial commits.
- Report skipped or failed elements when the result would otherwise look
  complete.

Treat Revit API boundaries as correctness boundaries. A collector, transaction,
selection, unit conversion, or element ID compatibility branch should be obvious
to the next maintainer.

Use Revit API references before relying on version-specific behavior:

- Check the official Revit API reference or Revit API Docs for the member's
  expected namespace, return type, exceptions, and version availability.
- Use RVTDocs as a coding reference when search, side-by-side Revit version
  checks, or Python translations of API examples would speed up implementation.
- Confirm translated examples against this repository's pyRevit and IronPython
  constraints before copying the shape into a command script.
- Add a `COMPAT` comment when a code path exists because Revit API members differ
  across supported Revit versions.

## UI and Output Boundaries

Use pyRevit forms and output APIs intentionally:

- Use forms for user decisions and file selection.
- Use `script.get_output()` for detailed reports, tables, and diagnostics.
- Keep alert text short and actionable.
- Put longer failure details in the pyRevit output window.
- Keep WPF window classes focused on UI state and event handling.
- Move deterministic transformations out of WPF handlers and into helpers.

When using custom XAML, follow the existing local GUI patterns and avoid changing
shared templates unless the task explicitly calls for a shared UI update.

## External Resources

Commands that open files, workbooks, processes, or network resources must make
ownership clear:

- The function that opens an Excel COM application should also close it, or
  clearly transfer ownership to its caller.
- Open analyst-owned workbooks read-only when the command only needs values.
- Save only at deliberate persistence points.
- Close workbooks and quit Excel in `finally` blocks.
- Do not leave files locked after a failed command.
- Do not assume network paths exist; validate and report missing resources.

## Error Handling

Catch broad exceptions only at command boundaries or around known host/API
compatibility failures.

Good broad-exception locations:

- a guarded `if __name__ == '__main__':` block that reports diagnostics
- a compatibility fallback for Revit, pyRevit, .NET, or Excel COM APIs
- cleanup that must continue even if a resource is already closed

Poor broad-exception locations:

- hiding failed model writes
- discarding skipped engineering data
- treating missing parameters or schedules as success
- suppressing workbook or file errors before the user can act on them

When a command continues after a failure, record the reason in the output report
or returned skip data.

## Reusable Logic

Structure reusable helpers so command scripts can stay small:

- Accept ordinary Python values when possible.
- Return ordinary Python values when possible.
- Return tuples or dictionaries that include enough context for reports and
  tests.
- Avoid mutating inputs unless that is the documented purpose.
- Keep value normalization in one place so command output and tests agree.

When moving logic from a command into `lib/`, preserve the command's existing
behavior first. Refactor for clarity only after the behavior is covered or easy
to verify.

## EF StarterKit Influence

Use the EF StarterKit as a teaching and onboarding reference, not as a strict
source template.

Carry forward these ideas:

- a visible command skeleton
- clear metadata near the top
- imports, variables/setup, functions/classes, and main sections
- small reusable examples under `lib/`
- beginner-friendly comments around pyRevit globals and reusable imports

Do not carry forward these patterns into new KLCode code:

- emoji comments
- wildcard Revit imports by default
- dense decorative separators
- placeholder sign-off text
- comments that narrate ordinary Python syntax
- import spacing that relies on visual alignment

KLCode scripts should feel approachable, but they also need to remain searchable,
reviewable, and compatible with automated checks.

## Review Checklist

- Is the command script still a thin adapter over host APIs?
- Did deterministic logic move to, or remain in, `lib/`?
- Is command code compatible with its intended pyRevit engine?
- Are imports explicit and grouped clearly?
- Are user selections validated before transactions or external writes?
- Are transactions scoped to coherent user actions?
- Are skipped items and failed writes reported instead of hidden?
- Are external resources closed in `finally` blocks or equivalent cleanup?
- Are tests focused on host-independent behavior where possible?
- Does `COMMENTS.md` cover the comments, docstrings, metadata, and dividers?
