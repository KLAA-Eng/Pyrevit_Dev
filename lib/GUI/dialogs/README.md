# Reusable shared dialogs

Opt-in Python/IronPython WPF dialogs using KLCode resources. Existing tools keep
their current calls. The [SPEC](SPEC.md) owns behavior, the
[design system](../../../docs/DESIGNSYSTEM.md) owns visual rules, and the
[consolidation plan](../../../docs/plans/custom-window-consolidation.md) owns
delivery status. Action choice redesign is explicitly deferred.

## APIs and results

| Prepared-data factory (construct only) | Modal helper | Result on acceptance |
| --- | --- | --- |
| `create_message(title, message, ...)` | `show_message(...)` | action `ok`, value None |
| `create_list_single(title, items, ...)` | `select_one(...)` | action `accept`, original payload |
| `create_list_multiple(title, items, ...)` | `select_many(...)` | action `accept`, original payload list |
| `create_sheet_selector(title, items, groups=None, ...)` | `select_sheets(title, document, ...)` | action `accept`, original sheet payload(s) |
| `create_revision_selector(title, items, ...)` | `select_revisions(title, document, ...)` | action `accept`, original revision payload(s) |
| `create_document_selector(title, items, ...)` | `select_open_documents(title, application, active_document, ...)` | action `accept`, original document payload(s) |
| `create_text_prompt(title, prompt, ...)` | `ask_text(...)` | action `accept`, raw string |
| `create_command_switch(title, choices, ...)` | `command_switch(...)` | action `accept`, command key and switch states |
| `create_rename(title, fields, ...)` | `rename(...)` | action `accept`, rules or a separate case action |
| `create_choice(title, choices, ...)` | `choose_action(...)` | Existing action key contract; redesign deferred |

`create_selection(title, items, multiple=True, ...)` and `select_items(...)`
remain the generic APIs. Named sheet/revision/document factories default to
multiple selection and accept `multiple=False`. List Single/Multiple fixes its
mode; do not also supply a `multiple` argument.

All factories take `version=None`, `owner=None`, `navigate=None`. Owner may be a
shown WPF Window, `System.IntPtr`, or integer native handle. Supply the host
owner explicitly. Pure caller version, such as `v1.2`, is metadata; no extension
version is inferred. Message, Text and Command Switch intentionally display no version
footer. Gallery supplies simulated navigation; ordinary shared footers use the
established destinations. Command Switch has no navigation links.

Factories return an unshown window. Modal helpers call ShowDialog and return
`DialogResult`. Inspect `result.action`, `result.value`, `result.is_cancelled`
explicitly; the object is not a Boolean pyRevit result. Close/Escape/Cancel or
unaccepted window closure returns action `cancel`, value None. Accepted empty
text and optional empty selection remain distinct from cancellation. No API
exits the script, runs a chosen command, writes settings or changes a model.

Importing `GUI.dialogs` or its collectors requires neither WPF nor Revit. WPF
loads lazily in factories, using the installed pyRevit framework bootstrap when
needed. Use the host UI thread. Collectors run in a valid Revit API context
before UI opens; callers own source-document lifetime and later operations.

## Message and text

```python
from GUI.dialogs import show_message, ask_text

notice = show_message(__title__, 'Review is complete.', severity='information',
    details='Optional caller-supplied diagnostics.', version=__version__, owner=owner_handle)
text = ask_text(__title__, 'Enter a description.', default='', required=False,
    validator=lambda value: 'Use 100 characters or fewer.' if len(value) > 100 else None,
    version=__version__, owner=owner_handle)
if text.action == 'accept':
    entered_text = text.value  # May legitimately be ''.
```

Message options are `severity='information'`, `details=''`, plus shared metadata.
Severity accepts information/warning/error/success. It is an OK-only notice.
the 24-unit icon and 18-unit Segoe UI SemiBold heading match the outline
severity color; body and details text stay 12. Message uses octagon-alert,
triangle-alert, info and check-check for error, warning, information and success
without changing global roles. Its 16-unit Details chevron points right/down
when collapsed/expanded; expanded text aligns with the body and the severity
icon centers vertically beside the heading.
The former unused multi-button/confirmation options are removed. Initial height
fits content up to 640. Manual width changes preserve chosen height. Details
starts collapsed and expands the bottom after WPF applies its template, retaining
the message viewport until capped. Collapse removes the added height. At the
cap, message and read-only details scroll. Expanded minimum height protects the
message/action area from being squeezed away.

Text options are `default=''`, `required=False`, `validator=None`. The field is
36 high, FontSize 24, centered Segoe UI Bold. Compact height fits prompt/error;
long prompts scroll at the cap. Title/Close remain; `WindowChrome.hide_footer()`
collapses only this template instance's footer row. Other windows keep theirs.
Prompt/input and input-or-validation/OK gaps are 8 units. OK is the only visible
action; title Close or Escape cancels. Natural minimum height keeps these gaps
instead of stretching blank space above the action.
Required checks whitespace without changing the returned string. A pure, quick
validator returns an error string or None; unexpected exceptions propagate as
programming errors. Editing clears feedback. Initial focus selects default text.
Enter accepts valid text; Escape cancels. Message Enter acknowledges OK.

## Selection and collectors

```python
from GUI.dialogs import SelectionItem, select_one, select_sheets

rows = [SelectionItem('first', 'Typical Detail', first_payload, description='Steel'),
        SelectionItem('second', 'Typical Detail', second_payload, description='Concrete')]
result = select_one(__title__, rows, owner=owner_handle, version=__version__)
sheets = select_sheets(__title__, explicit_document, include_placeholders=False,
    owner=owner_handle, version=__version__)
```

`SelectionItem(key, label, value=None, description='', groups=(), checked=False,
enabled=True)` uses unique hashable non-None keys; labels may repeat. Cloned
checks preserve caller rows and original payload identity. No first row is
checked implicitly. Single mode uses the same checkbox style, with exclusive
checking even when the previous check is hidden. Both modes require **Select**:
Enter and double-click do not accept. Space toggles a focused checkbox; keyboard
activation of the focused Select button remains possible with Space.

Options: `groups=None`, `prompt='Select Items'`, `required=True`,
`all_label='All Items'`. Group names derive in input order unless supplied as
`SelectionGroup(key, label)` rows. None is reserved for the implicit All group.
Search matches label/description case-insensitively without regex or reordering.
Group/search filters intersect. Hidden checks remain in the result. Select All
/ Select None affects visible eligible rows only and is absent in single mode.
Disabled rows cannot be accepted. Optional multiple selection may accept an
empty list; optional single selection may accept None. Inspect action.

Initial size is the Selection template's 432 x 576 (minimum 432 x 420). Search
comes first; the optional group dropdown below it is also 24 high. Both fields
align after 16-unit icons and an 8-unit gap. Group uses Lucide Layers-2 through
`KlaGroupGeometry`. Section spacing follows the template's 8/4-unit gaps; gray
Select All/None buttons center above green Select with an 8-unit gap. No visible
Cancel action; header Close/Escape cancels. No selected/visible summary is shown
below the list. Validation remains inline; list/action gaps remain 8 units.

The separate [collectors module](collectors.py) exposes:

- `sheet_items(document, include_placeholders=False, filterfunc=None)` returns
  `(rows, groups)`. Unique sheets sort by number/name; saved sheet sets share
  one check state per sheet. Eligibility/placeholder filtering applies before
  every grouping. The sheet factory labels its implicit group **All Sheets**.
- `revision_items(document, filterfunc=None)` returns rows in sequence order,
  with number/description/date/issued status. Both issued states are eligible
  by default. Per-sheet numbering displays sequence because RevisionNumber is
  not valid as a project-wide number there.
- `document_items(application, active_document=None, include_active=False,
  include_families=True, filterfunc=None)` excludes linked/active documents by
  default and includes projects/families. It requires explicit active_document
  unless include_active=True. Duplicate titles remain distinct; type/path is
  secondary text. Original Document objects provide session keys/payloads.

The modal specialized helpers collect then show. They forward inclusion/filter
options to collectors and remaining options to windows. `select_open_documents`
requires the active_document argument; use None with include_active=True when
there is no active document. Prepared-data factories perform no Revit query and
can be used with caller-prepared data instead. Family documents yield no sheets
or revisions. These APIs are not drop-in pyRevit return-type replacements.

## Command Switch

```python
from GUI.dialogs import ActionChoice, CommandSwitch, command_switch

result = command_switch(__title__, [
    ActionChoice('active', 'Active View', 'Use the current view.'),
    ActionChoice('choose', 'Choose Views', 'Select views in the caller.')],
    switches=[CommandSwitch('details', 'Include Details'),
              CommandSwitch('preview', 'Preview Only', checked=True)], owner=owner_handle)
if result.action == 'accept':
    command_key = result.value['command']
    switch_states = result.value['switches']
```

`ActionChoice(key, label, description='', enabled=True)` and
`CommandSwitch(key, label, checked=False, enabled=True)` require unique hashable
non-None keys within each collection. The floating panel has prompt/search,
wrapping immediate command buttons and optional toggle pills. No corner x,
standard header/footer or Continue action. KLCode colors/roles come from
[KLCodeCommandSwitch.xaml](../Resources/KLCodeCommandSwitch.xaml), which merges
Components and defines opt-in styles. No upstream XAML/assets are copied.

Initial focus rests on the neutral panel; search is neither focused nor selected
on open. Typing moves to search and filters command labels/descriptions; optional toggles
stay visible and keep cloned state. Tab traverses, Space toggles. Enter chooses
the focused enabled command or sole enabled match while search is focused;
Enter on a toggle never chooses a command. Escape clears search first, then
cancels when empty. Blank panel clicks do not dismiss. Height
fits content up to 500, then scrolls. Button descriptions are tooltips/help text.
The result is `{'command': key, 'switches': {key: bool}}`; caller commands never run.

## KLC-Rename

`RenameField(key, label, find='', replace='', prefix='', suffix='',
allow_case=True)` describes a property group. `create_rename(title, fields,
version=None, owner=None, navigate=None)` constructs the window; `rename(...)`
shows it. One to three groups are arranged horizontally, with minimum widths
384, 712 and 1040 respectively. Each has one Find/Replace pair and Prefix/Suffix.
Optional Uppercase/Lowercase buttons are separate actions for their own field.

Rename validates and returns action `accept` with value `{'operation': 'rename',
'fields': {key: {'find': ..., 'replace': ..., 'prefix': ..., 'suffix': ...}}}`.
Enter activates Rename. Case buttons close with action `accept` and value
`{'operation': 'upper' or 'lower', 'field': key}`. Invalid rules stay open with
inline feedback. Close/Escape cancels with value None. The dialog performs no
model mutation or live before/after preview; the caller owns any later action.

## Gallery and verification

Gallery has one row per shared family, with Variant beside State. Search includes
variant names; each family's variant and state are remembered for the session.
Selection offers Sheets, Revisions, Open Documents, List Single and List Multiple.
Message offers Without Details and With Details, each with Normal, Empty, Warning,
Error, Success, Disabled and Long content; With Details keeps diagnostics in
Empty. Command Switch offers Commands only and Commands with toggles. KLC-Rename
offers Single field, Two fields and Multiple fields (three groups). Other shared
variants retain five standard states.
The duplicate Message/Selection templates are retired; Form, Options and Review
remain. Confirmation/Parameter previews remain removed. Action choice retains its
current highlighted-row/Continue and default-key behavior pending future work.

Run the Python suite and Windows probe in
[DESIGNSYSTEM.md](../../../docs/DESIGNSYSTEM.md#validation). Probes check actual
controls, bounded layout, regression cases and results without showing windows.
Direct keyboard-handler dispatch does not prove live input/focus. Revit data,
owner/modal lifetime, pointer-driven resize flicker, keyboard traversal and DPI
remain explicitly identified host acceptance checks.

The opt-in `-ShowFocusProbe` Windows run briefly opens two owned fictional
windows: UIA identifies the search field, initial Command Switch focus stays on
the neutral panel, and programmatically focused buttons/checks retain their
normal borders. This does not establish physical keyboard/pointer routing or
Revit ownership. Shared button/check/radio/toggle styles use no focus adorner;
there is no light-green frame around the focused control/checkbox text and no
white underline/square-border override. Keyboard operation is retained.
