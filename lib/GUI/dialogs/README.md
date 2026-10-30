# Reusable shared dialogs

Use `GUI.dialogs` for new opt-in dialogs with the current shell, controls,
icons and green/gray footer. Existing tools still use their existing APIs.
The [SPEC](SPEC.md) owns behavior; [DESIGNSYSTEM.md](../../../docs/DESIGNSYSTEM.md)
owns visual choices. These are Python/IronPython WPF windows, not compiled
add-in replacements or drop-in pyRevit return types.

| Family | Construct only | Show modally and return a result | Intended future use |
| --- | --- | --- | --- |
| Message / confirmation | `create_message(title, message, **options)` | `show_message(...)` | Alerts, diagnostic details, Yes/No/Cancel, Retry/Cancel |
| Single / multiple selection | `create_selection(title, items, **options)` | `select_items(...)` | Prepared sheets, revisions, views, open documents, parameters |
| Described action choice | `create_choice(title, choices, **options)` | `choose_action(...)` | Command-switch or TaskDialog command-link workflows |
| Text prompt | `create_text_prompt(title, prompt, **options)` | `ask_text(...)` | String entry with optional validation |

All factory and modal functions accept `version=None`, `owner=None` and
`navigate=None`. Pass the caller's pure tool version, such as `v1.2`. Omission
leaves the version footer empty. An owner may be an existing shown WPF Window,
`System.IntPtr`, or an integer native window handle. The library does not infer
the active Revit owner. Supply it when adopting a dialog in a host command.
Default footer navigation opens the established destinations; Gallery supplies
a local callback instead.

Importing this package loads only host-free models. Factories lazily load WPF;
inside pyRevit they can use its framework bootstrap to resolve the installed
IronPython WPF assembly. Call factories and show windows on the host UI thread.
Bare `System.Windows.Window` classes avoid the extra Escape handler installed
by `pyrevit.forms.WPFWindow`. This does not fix legacy tools' keyboard behavior.

## Results and cancellation

Every window starts with `DialogResult(action='cancel', value=None)`. Read
`result.action`, `result.value` and `result.is_cancelled` explicitly. Do not
test the result object's truthiness; it is not a Boolean pyRevit alert result.

- Message actions are `ok`, `yes`, `no`, `retry`, `cancel`; their value is None.
- Selection and action/text confirmation return `action='accept'`.
- Multiple selection returns an ordered list of original payloads; single
  selection returns a payload, or None if optional and unchecked.
- Choice returns its stable action key. Text returns the exact string entered,
  including whitespace or an accepted empty string.
- Escape, header Close, Cancel, or closing the window without accepting returns
  cancellation. No workflow action, `sys.exit`, transaction or persistence runs.

Construct-only functions return the actual window without showing it. Call
`window.ShowDialog()` and read `window.result`, or use the modal helper. Modal
showing, real owner/focus behavior and DPI/work-area acceptance require host
review; the automated probe constructs and renders without showing windows.

## Messages

```python
from GUI.dialogs import show_message

result = show_message(__title__, 'Continue with the prepared selection?',
                      buttons=('yes', 'no', 'cancel'), severity='warning',
                      details='Caller-supplied diagnostic information.',
                      version=__version__, owner=revit_window_handle)
if result.action == 'yes':
    pass  # The caller owns any later operation.
```

Options: `buttons=('ok',)`, `severity='information'`, `details=''`,
`default_action=None`. Severity accepts information/warning/error/success.
Use one to three distinct supported buttons. Default Enter action is Cancel
when present, otherwise No when present, otherwise the first button; an
explicit `default_action` must name a displayed action. No remains distinct
from cancellation. Details starts collapsed. Message height fits content up to
640 units, then scrolls. Resizing the width refits height.

## Selection

```python
from GUI.dialogs import SelectionItem, SelectionGroup, select_items

rows = [SelectionItem('type-width', 'Width', type_parameter,
                      description='Type parameter', groups=('type',)),
        SelectionItem('instance-width', 'Width', instance_parameter,
                      description='Instance parameter', groups=('instance',)),
        SelectionItem('read-only', 'Element ID', id_parameter,
                      description='Read-only', enabled=False)]
result = select_items(__title__, rows, multiple=True,
    groups=[SelectionGroup('type', 'Type'), SelectionGroup('instance', 'Instance')],
    prompt='Select Parameters', required=True, version=__version__,
    owner=revit_window_handle)
if result.action == 'accept':
    selected_parameters = result.value
```

`SelectionItem(key, label, value=None, description='', groups=(), checked=False,
enabled=True)` requires a unique, hashable, non-None key. Labels may repeat.
Input order and payload identity are retained; check state is cloned. No first
row is checked implicitly. `multiple=False` permits at most one initial check
and enforces exclusive checking. Clicking a list row highlights it; the
checkbox checks it. Space toggles a focused checkbox. Enter validates/accepts.

`groups=None` derives group names from item memberships in input order. Supply
`SelectionGroup(key, label)` rows for separate display names. None is reserved
for All Items. An item can belong to several groups. Search matches label and
description, ignoring case. Group/search filters intersect. Hidden checks stay
checked. All Visible / None Visible touches visible eligible rows only; the
accepted result includes hidden checked rows too. These batch buttons are
hidden in single-selection mode. Disabled rows cannot be checked/accepted.

Options: `multiple=True`, `groups=None`, `prompt='Select Items'`, `required=True`.
Required selection shows inline feedback when nothing is checked. Optional
multiple selection can accept an empty list; inspect action for cancellation.

Callers collect and prepare Revit data. For example, preserve revision sequence
order and issued rules; build sheet-set memberships and placeholder eligibility;
label document/view/parameter rows and decide availability before opening.
The library contains no model-query wrappers. Native pickers and progress or
interactive-selection overlays remain their existing implementations.

## Action choice and text

```python
from GUI.dialogs import ActionChoice, choose_action, ask_text

choice = choose_action(__title__, [
    ActionChoice('active', 'Active View', 'Use the current view.'),
    ActionChoice('choose', 'Choose Views', 'Select views in the caller.'),
    ActionChoice('blocked', 'Unavailable', 'Explain why.', enabled=False)],
    version=__version__, owner=revit_window_handle)

text = ask_text(__title__, 'Enter a description.', default='', required=False,
    validator=lambda value: 'Use 100 characters or fewer.' if len(value) > 100 else None,
    version=__version__, owner=revit_window_handle)
if text.action == 'accept':
    entered_text = text.value  # May legitimately be ''.
```

`ActionChoice(key, label, description='', enabled=True)` requires unique,
hashable, non-None keys. Nothing starts selected. Continue stays disabled until
an enabled choice is selected. Confirming returns its key; no action runs.
Choice accepts `prompt='Choose an Action'`.

Text accepts `default=''`, `required=False`, `validator=None`. Required checks
whitespace without altering the returned input. A validator receives raw text
and returns an error string or None. It should be pure and quick; unexpected
exceptions propagate as caller/programming errors. Validation errors remain
inline with the window open. Editing clears prior feedback. Initial text focus
selects the supplied default when the window loads.

## Gallery and verification

In UI Gallery, search **Shared dialog**. Six variants each offer Normal, Empty,
Error, Disabled and Long content. Parameter selection deliberately includes two
Width labels with distinct stable keys. Fictional rows never query Revit.
The four XAML bodies use shared resources and opt-in `KlaDialogCheck`,
`KlaDialogDescription` and `KlaDialogListItem` compositions.

Run the Python contracts and Windows probe listed in
[DESIGNSYSTEM.md](../../../docs/DESIGNSYSTEM.md#validation). The probe checks
actual controls, results, layout at normal/minimum sizes and scrolling. It
dispatches the Escape handler directly; live keyboard input, owner/modal
lifetime, focus and DPI remain the owner's Revit checks.
