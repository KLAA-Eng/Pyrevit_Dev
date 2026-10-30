# Confirmed dialog refinement — 2026-10-29

The owner confirmed the four-round grilling outcome with "confirmed, implement".
Starting baseline: `afe63c1` on `dev.GUI-Clean`. The
[consolidation plan](../../../plans/custom-window-consolidation.md) owns tasks;
[dialog SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns acceptance;
[API guide](../../../../lib/GUI/dialogs/README.md) owns usage. This supersedes
the current-behavior portions of the [initial delivery record](2026-10-29-shared-dialogs.md),
which remains historical evidence.

## Implemented behavior and boundaries

- Message is OK-only. Details grows the bottom after its WPF template updates,
  preserving the message viewport until capped; expanded minimum height protects
  content/actions. Manual width changes do not refit height. Repeated expansion
  and collapse restores height without drift. Long message/details scroll.
- Text is compact with a 36-high, FontSize 24, centered Segoe UI Bold field,
  inline validation and Cancel/OK. Its title/Close remains; only its footer row
  is removed through an opt-in method on the chrome instance. Other footers
  keep their green/gray colors. Required/optional raw-text semantics remain.
- Five selector presets share the checkbox body: Sheets, Revisions, Open
  Documents, List Single and List Multiple. Both require Select; Enter and
  double-click do not accept. One/many checking, hidden checks, stable identity,
  disabled rows, visible-only batch actions and source order are preserved.
- Separate read-only collectors prepare sheet/set membership, revision labels
  and open-document rows. They import Revit lazily and take explicit context.
  No transaction/mutation is introduced; Gallery never calls them.
- A separate floating Command Switch uses KLCode roles and original compact
  WPF styling, with search, wrapping command pills, optional persistent toggles,
  corner x, bounded scrolling and explicit key/state results. It runs no chosen
  command. No upstream implementation or assets were copied.
- Action choice's XAML/controller behavior is unchanged. Its long-content
  sample remains the original data. Independent redesign stays future GUI-22.

Production command scripts/dialog calls, CustomAlert/SelectFromDict, the five
reference templates, native pickers/overlays, packaged DLLs and unrelated GUI-14
work remain unchanged. Only UI Gallery SPEC/tooltip metadata changes among
command bundles. Gallery now has 45 entries / 26 Window sources, including nine
shared-dialog entries with five states each; five compiled previews stay deferred.

## Regression evidence

Before implementation, the in-memory real-WPF diagnostic measured a short
Message at Height=240/message area=101. Expanding Details left Height=240,
shrinking that area to 26 while Details took 128. The width handler replaced a
manual Height=400 with 344. These are observed sizing failures; the diagnostic
did not reproduce physical pointer-driven flicker. A new actual-control test
failed on expansion layout before the fix, then passed with deferred sizing.

The revised probe asserts growth, preserved message area, three expansion/
collapse cycles, no height override at widths 480/640, capped long overflow,
footer isolation, exact input typography and fully visible validation feedback.
Render inspection caught and corrected a clipped validation line in the first
compact Text implementation; its natural fields/actions now drive fitting,
rather than the constrained ScrollViewer's reported viewport.

## Checks performed

| Check | Result / scope |
| --- | --- |
| Complete CPython suite | 380 run; 379 passed, one existing symlink-related skip |
| New collector tests | 11 pass; immutable boundary objects, consistent eligibility/groups, per-project/per-sheet revision numbering, duplicate titles/hash collisions, explicit context, empty/error paths and disposal |
| Command-switch state tests | Seven pass; host-free import, key validation, clone/filter/eligibility, Enter policy and result snapshots |
| Installed IronPython 2.7.12 WPF probe | 45 entries; 116 custom/state constructions; 45 shared-dialog state layouts at normal/minimum sizes, plus prior 25 template and 45 production layout regressions |
| WPF interaction checks | Message sizing/manual-height, four severities/OK/cancel, footerless Text validation/blank/raw input, exact 36/24 Bold typography, all five presets, explicit Select, hidden/disabled/exclusive checks, command filtering/toggle clones/results/Close/Escape handlers |
| C# source tests | 17 passed |
| net48 / net8.0-windows desktop smoke | Seven existing compiled instances across five classes passed on each runtime |
| Scale / generated artwork | Zero strict violations; 85 unchanged advisory consumer literals; 17 icon roles and exact wordmark generation unchanged |
| Independent review | Read-only review of Message/Text/Selection, floating switch, exports and footer isolation found no blocking defect; reviewer independently ran seven switch and ten dialog-model tests |
| Diff / scope review | No ActionChoiceDialog.xaml diff or production-script migration; whitespace check passes |
| Documentation integrity | Deterministic audit passed; all local Markdown links resolve. Existing progressive-adoption role/ADR/test-registry warnings remain advisory under repository ownership. |

Commands are the existing suite and Windows/compiled checks in
[DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md#validation). No new dependency or
test framework was installed. Collector stdlib trace measured 83/101 executable
lines (82.2%, excluding import-time execution). An aggregate changed-code
percentage across CPython and embedded IronPython WPF was not measured; the
actual boundary/interaction evidence above defines the local proof.

## API reference verification

Read-only collector APIs were checked against installed Autodesk SDK XML for
Revit 2024/2025/2026/2027 (API file versions 24.3.60.12, 25.5.0.57, 26.5.0.55,
27.3.0.28), covering 16 used members. Revit 2024 metadata confirms inherited
FilteredElementCollector.Dispose. Installed pyRevit is 6.5.3.26176+2017.

RevisionNumber is not a project-wide value in per-sheet numbering; the collector
uses SequenceNumber there. See Autodesk's
[Revisions guide](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Views/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Views_Revisions_html.html)
and [Application.Documents reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/8a32ffe0-7e80-e85c-78aa-1af48ace4d74.htm).
These references and SDK checks do not prove collection against a live model.

## Inspected renders

| Surface | Evidence |
| --- | --- |
| Message expansion | [Message remains visible](2026-10-29-dialog-refinement-evidence/dialog-message-details-expanded.png) |
| Large Text / validation | [Normal](2026-10-29-dialog-refinement-evidence/dialog-text-normal.png), [error](2026-10-29-dialog-refinement-evidence/dialog-text-error.png) |
| Checkbox list modes | [Single](2026-10-29-dialog-refinement-evidence/dialog-list-single-normal.png), [multiple](2026-10-29-dialog-refinement-evidence/dialog-list-multiple-normal.png) |
| Sheets | [All Sheets and set groups](2026-10-29-dialog-refinement-evidence/dialog-sheets-normal.png) |
| Revisions | [Sequence/date/issued information](2026-10-29-dialog-refinement-evidence/dialog-revisions-normal.png) |
| Open documents | [Duplicate titles with type/path](2026-10-29-dialog-refinement-evidence/dialog-documents-normal.png) |
| Command Switch | [Normal](2026-10-29-dialog-refinement-evidence/dialog-command-switch-normal.png), [minimum width](2026-10-29-dialog-refinement-evidence/dialog-command-switch-minimum.png), [long content](2026-10-29-dialog-refinement-evidence/dialog-command-switch-long-content.png) |

## Remaining host acceptance

Windows were constructed/rendered without showing a window or opening Revit.
Keyboard assertions dispatch handlers directly; they do not establish actual
focus/default-button routing, Tab/Space traversal, access keys or pointer input.
The owner retains live Revit review for those interactions, native-handle/WPF
ownership and modal lifetime, resize flicker, Details under live layout, DPI/
work-area placement, contrast/accessibility and real read-only collectors on
representative projects/families/sheet sets/revision numbering modes.

No native-owner/modal, model-data or deployed DLL acceptance is claimed. Local
source checks do not close GUI-08, GUI-14 or the separate compiled-tools plan.
Rollback the new package portions, opt-in resources, Gallery routes, tests and
docs together; no model/data migration or production call-site rollback exists.
