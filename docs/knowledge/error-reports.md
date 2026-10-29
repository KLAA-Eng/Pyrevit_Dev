# Error reports

Error reports let a tool record an unexpected failure where its owner can
collect it, and let a user quote the failure in feedback. They are written by
[`lib/error_reports.py`](../../lib/error_reports.py) (host-independent) and
[`lib/error_reports_revit.py`](../../lib/error_reports_revit.py) (pyRevit
context, clipboard). As of 10.29.2026 only
[PDF Overlay](../../KL%26A%20Tools_dev.tab/05%20DevSandbox.panel/Prototype.pulldown/PDF%20Overlay.pushbutton/SPEC.md)
uses them.

## What happens on an error

1. The tool catches the unexpected exception and calls
   `report_exception(tool, tool_code, action, log_path)`.
2. One JSON file, `<report id>.json`, is written to
   `%LOCALAPPDATA%\KLA Tools\Error Reports` on the user's computer. The id
   names the tool, date, and time, for example `PDFO-20261029-1432-7F3A`.
3. The id is copied to the clipboard, and the tool tells the user to paste it
   into **Outreach > Suggestions/Bugs Feedback**.

Writing a report never raises; if no folder can be written, the user is told
so instead. Expected problems the user can fix (for example "open a plan
view") are messages, not reports.

## What a report contains

- Tool id, name, and version; the action the user ran (for example
  `Check Members`).
- The error type, message, and full traceback.
- Context: extension version (`build_info.VERSION_LABEL`), Revit version and
  build, Revit user name, pyRevit version, Windows user name, and the model's
  file name without its folder (cloud model ids are removed).
- The last 40 lines of the tool's own log, when it has one.
- A **signature** (tool, error type, and innermost file, line, and function).
  Reports with the same signature are the same bug seen again. It leaves out
  the message, which often holds element ids or paths.

Including the user name and model file name was the owner's decision on
10.29.2026. Reports do not include model paths, element data, or PDF content.

## Collecting reports and handing them off

Reports stay on each computer for now. To collect them:

1. Ask the user to zip `%LOCALAPPDATA%\KLA Tools\Error Reports` (or just the
   file named by the id they sent) and send it to you.
2. Summarize them:

   ```bash
   python scripts/summarize_error_reports.py path\to\reports.zip
   ```

   The summary groups reports by signature, most frequent first, with counts,
   first and last dates, actions, tool versions, users, and report ids. Add
   `--id <report id>` to print one full report. With no path, it reads your
   own local folder.
3. For a fix, give the summary (or the zip) and the user's feedback to the
   developer or assistant working on the tool.

## Collecting centrally later

Set `SHARED_REPORTS_FOLDER` in `lib/error_reports.py` to a folder every Revit
user can write to, such as a UNC share. Each report is then also written there
when the folder is reachable, still one file per incident so writers never
collide. The local copy is always kept. Point `summarize_error_reports.py` at
the shared folder to see every user's reports.

## Adding reports to another tool

Give the tool an id and a short code, and call `report_exception` from the
`except` that handles unexpected failures:

```python
from error_reports_revit import report_exception

TOOL = {'id': 'devsandbox.example', 'name': 'Example', 'version': __version__}

try:
    run_tool()
except Exception:
    report_id, message = report_exception(TOOL, 'EXMP', 'Run')
    forms.alert('Example failed.\n\n' + message, warn_icon=True)
```

Keep the action names short and stable, since they appear in summaries.
