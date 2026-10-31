# Action Choice delivery — 2026-10-30

Baseline: `3c34d69`, with the owner's subsequent recorded grilling answers.
The owner confirmed the complete design and explicitly requested implementation.
The [consolidation ledger](../../../plans/custom-window-consolidation.md) owns
GUI-40/41; the [shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) and
[API guide](../../../../lib/GUI/dialogs/README.md) own current behavior and usage.

Action Choice replaces its unused select-row/Continue interface with immediate
command links and optional standard buttons. It follows the instruction/body/
command-link/action hierarchy documented by
[Autodesk TaskDialog](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/853afb57-7455-a636-9881-61a391118c16.htm),
using existing KLCode typography, colors, severity roles and window chrome.
The caller title remains; the standard navigation/version footer is omitted.
Caller help text/link, Details, severity and checkbox sections are optional.

The pure state validates/clones up to four command links and canonical common
buttons, resolves caller defaults or the first available action, and returns
exact command/button keys with checkbox snapshots. No, Cancel and Close are
distinct. Disabled actions cannot activate. A configuration with no enabled
action and no cancellation is rejected rather than trapping the user.

Enter activates actions; Space only toggles the checkbox. Cancellation defaults
on, may be disabled when Cancel is absent, and respects explicit Cancel override.
Escape and native/chrome Close use distinct result paths. The WPF adapter
detaches the shared Escape handler so it cannot override this contract.

Content fits initially up to 640. Details grows the bottom and reverses its
growth without drift; manual width changes retain height. Long optional
checkbox/help sections have bounded scroll viewers. All six common buttons fit
as four plus two at minimum width, with an eight-unit row gap. Empty command
descriptions reserve no blank line. These edge cases were addressed during
implementation/review and retain persistent regression assertions.

Gallery keeps one Action Choice family row: Commands, Commands + Details,
Commands + Checkbox, Full Content and Standard Buttons. Each offers Normal,
Empty, Warning, Error, Success, Disabled and Long content. Search and session
variant/state memory are checked through the actual Gallery controls.

Verification:

- Python suite: 421 tests, 420 passed and one existing skip.
- Pure ChoiceState: 20 test-first cases, 100% statement and branch coverage as
  measured by the model implementer, including exact caller-key identity,
  snapshots, defaults, cancellation and invalid configurations.
- Installed IronPython 2.7.12/Windows WPF: 39 catalog entries, 24 Window sources,
  160 custom/state constructions and 104 shared layouts. All 35 Action Choice
  variant/state combinations construct and lay out at their supported bounds.
- Dedicated WPF checks cover severity, immediate/disabled actions, all six common
  buttons, help callback, optional sections, Details expansion/collapse and cap,
  manual sizing, empty fallback, oversized optional text and invalid inputs.
- Owned shown fixtures verify caller-default focus/UIA, real routed key-down/
  key-up sequences, checkbox Space toggling, blocked Space command activation,
  Enter activation, native Close policy and Cancel override.
- Existing Message, Rename, shared focus and Switch pointer-capture checks pass.
- Scale audit: zero strict violations, 88 existing/advisory consumer literals.
- Documentation integrity/local links and Git whitespace checks pass.
- Independent read-only review found no remaining runtime defect. Its general
  result-documentation contradiction was corrected before completion.

No production command adopted this API, no model/settings operation was added,
and no compiled resource or packaged assembly changed. Physical Tab/Alt+F4,
Revit ownership and DPI remain host acceptance checks; routed events and owned
Window.Close calls do not establish those physical-input claims. No live Revit
session or user document was controlled.

Inspected renders: [Commands](2026-10-30-action-choice-evidence/commands.png),
[Full Content / Warning](2026-10-30-action-choice-evidence/full-warning.png),
[Standard Buttons](2026-10-30-action-choice-evidence/buttons.png), and
[long expanded Details](2026-10-30-action-choice-evidence/long-details.png).
