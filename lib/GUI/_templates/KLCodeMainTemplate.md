# KLCode Main Template

This is the first opt-in reference for the approved custom-window foundation.
Open **KLCode main template** in UI Gallery to review it with fictional data.
The [consolidation plan](../../../docs/plans/custom-window-consolidation.md)
owns delivery status; [DESIGNSYSTEM.md](../../../docs/DESIGNSYSTEM.md#custom-window-foundation)
owns the shared design rules. Other production windows still use their existing
resources and layouts until the owner reviews this reference.

## Responsibilities

| Source | Owns |
| --- | --- |
| `KLCodeMainTemplate.xaml` | Workflow body: search, sample list, selection controls and centered action arrangement |
| `../Resources/KLCodeFoundation.xaml` | Reusable `KlaWindowShell`, header/footer composition, and explicitly named control styles |
| `../Resources/KLCodeFoundationTokens.xaml` | Typed WPF spacing, typography, sizes, readable semantic brushes, and `KlaIconSearch` |
| `../window_metadata.py` | Caller title/pure version and the two shared footer destinations; host-independent |
| `../window_chrome.py` | Opt-in Python loading and shared close/drag/navigation events; does not show the window |

The foundation reuses the legacy dictionary's palette, vector wordmark and
scrollbars. It does not edit that dictionary or change existing consumers.
`Tag` on `window_shell` is reserved for `WindowMetadata`; the body retains its
own `DataContext`. Do not copy header/footer markup into a new form.

## Reference geometry

Values are WPF device-independent units, not physical screen pixels.

| Part | Reference |
| --- | --- |
| Window | 432 wide x 576 high; fixed by the reference style, centered on screen |
| Header and footer | 24 high each |
| Header | 86 / flexible / 86 columns; existing 70 x 12 outlined wordmark, centered title, Close button |
| Title | Segoe UI 14; uses the available center lane, with ellipsis and no tooltip |
| Close | 60 x 18, Segoe UI 10; one-unit upward optical text adjustment in the shared style |
| Body | 16 horizontal padding; 8 below header and last action; list uses remaining height rather than a fixed height |
| Search | 24-high visible field, matching Create from rooms; 14-unit text and existing 16-unit icon |
| Typography | Segoe UI 12 body/controls; 14 main action |
| Selection prompt | 14, matching KL&A list selection; constant labels use Title Case (`Select Elements:`) |
| Section / label / related gaps | 16 / 4 / 8; compact search-to-prompt gap is 8 |
| Checkbox rows | 20 high for single-line items, matching Create from rooms; 4 between box and label |
| Row interaction | Native WPF row template, matching KL&A list selection's blue hover/selection |
| Select All / Select None | 104 x 28 each, 8 apart, centered |
| Main action | 216 x 32, centered, 8 below the pair, 8 before footer |
| Footer | Prototype left, pure caller version such as v0.5 center, Outreach right; same green/gray as Create from rooms |

The pair still matches the main action width: 104 + 8 + 104 = 216. Main and
secondary actions retain their arrangement. Long item names wrap and scroll;
long titles trim instead of increasing the header height. No full-title hover
text is added. Buttons use fixed role widths; future wider variants must be
shared named styles rather than unexplained per-window values.

The default Select button has no outline. Keyboard focus uses a small underline
instead of an enclosing white border. The list has 1-unit inner padding and
compact row padding; wrapped text uses the available width to within 8 units
of the scrollbar. Short labels naturally leave unused horizontal width, and
few rows leave unused vertical space because the reference remains 432 x 576.

## Create a window

Use a normal WPF `Window` or a compatible host window. Supply a body XAML
following this template, keeping `window_shell` as its named ContentControl.
The loader merges the foundation before resolving XAML static resources.

```python
from System.Windows import Window
from GUI.window_chrome import load_window

class ExampleWindow(Window):
    def __init__(self, body_path, title, version):
        load_window(self, body_path, title, version)
        # Supply workflow data and body event handlers here.

window = ExampleWindow(body_path, __title__, __version__)
window.ShowDialog()  # The caller chooses modal/modeless behavior.
```

Pass a pure tool version such as `v1.3`. A missing/blank version leaves the
footer center empty. Version text has no `Version:` prefix. The loader does not infer an extension version, use a
placeholder, access a document, or show the window. The body supplies only
its own workflow event handlers. Existing command-specific close behavior
must be reviewed before migration; this reference's close simply closes.

For a Gallery preview, supply a `navigate(uri)` callback to simulate links.
Ordinary callers omit it to use the existing OS navigation behavior. Gallery
passes its own `__version__` as caller metadata; none is hardcoded in XAML.

## Verification

Run the existing isolated probe from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/validate_ui_gallery_wpf.ps1
```

This process-only execution-policy override does not change machine settings.
An optional `-OutputDirectory` saves the Gallery renders and five template
state renders. Actual WPF bindings/geometry and routed click/navigation events
are checked without showing a window or using a Revit document. The pyRevit
loader/alert boundary is a stand-in; keyboard/focus, dragging, native ownership,
external navigation and DPI acceptance still require live-host checks.
