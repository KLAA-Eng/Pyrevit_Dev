# Ancillary support components — 2026-10-05

This supplement reviews the support code outside the visible-command inventory: `lib/match`, `lib/customprops`, `lib/Selection`, `lib/sbox`, `commands/make3dview_command.py`, and all 19 Python files in `lib/Snippets`. The baseline is `1562e96a5f6e23b7368c80e317868a0c059dc165`. This is a source review only. No model operations, pane registration, clipboard persistence, batch document processing, or Excel automation were executed.

The central finding is an activation distinction: most of these components are **not wired to a tracked ribbon command or startup registration**. Their defects are future integration gates, not evidence that today's production commands expose those behaviors. Four concrete dormant-component findings are recorded below as P3. Production correctness findings and GUI findings remain in their [respective](production-tools.md) [reports](design-system-and-gui.md).

## Scope and evidence

The review covered **32 Python files**, including package initializers. Consumer discovery used the tracked-file inventory and searches for imports, class/function names, startup registration, and gallery dispatch. A missing textual reference alone was not treated as proof of inactivity: the gallery's metadata and actual preview construction were traced, and package initializers were checked for activation side effects. No tracked external-registration contract was found for the dormant panes/actions. Consumers in other installed extensions or untracked scripts are outside this conclusion.

Review depth is explicit:

- **Flow review:** entry points, relevant data transformations, persistence/model writes, exception paths, and callers were read. This is not live acceptance.
- **Boundary review:** functions and their caller/transaction/document assumptions were inspected; every general-purpose snippet line was not independently proved against every Revit release.
- **Inventory:** an empty initializer or constants-only module was checked for activation and dependencies.

No additional host-free test suite was added or executed for this supplement. Findings are confirmed code paths; user-visible consequences require the stated future activation and acceptance fixtures. P3 reflects dormant reachability, not an assertion that deletion or unintended model edits would be low impact once exposed.

## Activation and component matrix

| Component | Current tracked consumers / activation | Depth | Assessment and next acceptance boundary |
| --- | --- | --- | --- |
| `lib/match/clipboard.py` | Defines clipboard content, dockable panel, and Recall window. No production constructor or pane registration found. Gallery metadata names Recall, but its preview uses a separate sample construction. | Flow | Revit writes use `execute_in_revit_context`; Recall persistence needs SUP-02. Gallery cannot establish actual clipboard acceptance. |
| `lib/match/match_utils.py` | Imported by dormant clipboard and Custom Properties. | Flow | Parameter matching uses names, storage/data types, category options, and raw parameter values. Type-property writes are explicitly supported. Exceptions are logged per property. Before activation, establish document identity, parameter identity, type-change scope, and changed/skipped/failed outcomes. |
| `lib/match/filter_utils.py` | Imported by dormant clipboard and Custom Properties. | Flow | Explicitly limits rule extraction to supported simple equality rules; unsupported/compound cases can return no match. Override detection and source-color lookup were traced. This restriction is not a defect by itself. Test actual rule ordering, unsupported rules, and Revit-version compatibility before publishing. |
| `lib/match/__init__.py` | Package initializer. | Inventory | No activation side effect. |
| `lib/customprops/custom_props_pane.py` | Dockable panel class; no tracked startup registration or production construction found. | Flow | Reviewed initialization, event handlers, selection/document refresh, parameter display, dirty-state tracking, copy/paste, filtering, and Apply. SUP-01 blocks reliable edit intent. Setter results also need visible outcome reporting before activation. |
| `lib/customprops/__init__.py` | Package initializer. | Inventory | No activation side effect. |
| `lib/Selection/select_similar_category.py` | No caller outside its package found. | Boundary | Category-based selection helper. Requires an active document and a supported selected element. Test absent categories, empty selection, cancellation, and view/model modes before wiring. |
| `lib/Selection/select_similar_family.py` | No caller outside its package found. | Flow | Family-name filtering includes a Revit-version constructor branch. Its invalid-selection exit is inside a bare exception handler that refers to a variable assigned later; see readiness notes. |
| `lib/Selection/super_select.py` | No tracked caller found. | Boundary | Special-case category/type selection logic was read. A duplicate category branch needs correction before reuse; see readiness notes. |
| `lib/Selection/__init__.py` | Package initializer. | Inventory | No activation side effect. |
| `lib/sbox/sbox_actions.py` | No tracked caller found. | Flow | Reviewed toggle, hide/unhide, face alignment, and temporary box/restore flows. SUP-04 covers restore-file failure. Linked-face coordinates, document changes, cancellation, and temporary view modes need host fixtures. |
| `lib/sbox/__init__.py` | Package initializer. | Inventory | No activation side effect. |
| `commands/make3dview_command.py` | Standalone script expects injected `__models__`; no tracked launcher found. | Flow | Opens each model, creates a 3D view, and saves it. It has no per-model close/finally or failure continuation. Treat as an unfinished batch-runner boundary, not an advertised ribbon tool. |
| `lib/Snippets/_selection.py` | **Active:** production Find/Replace Views, Find/Replace Sheets, Duplicate Sheets; corresponding prototypes. | Flow for those selectors; boundary for other functions | Explicit `uidoc` determines the working document. Default arguments capture the import-time document. Active command behavior is covered in the production report; persistent-engine/document-switch reuse needs separate acceptance. |
| `lib/Snippets/_context_manager.py` | **Active:** production Find/Replace Views; corresponding prototype; dormant `_revisions`. | Flow | Exception wrappers can suppress exceptions; transaction helpers do not provide a committed-result summary. See the production Find/Replace review for reachable effects. Avoid counting this again as a separate support finding. |
| `lib/Snippets/_variables.py` | Imported by active `_selection`. | Inventory | Revit view/line class lists. No independent mutation or persistence boundary. |
| `lib/Snippets/_convert.py` | `GUI/Tools/CreateFromRooms.py`; dormant `_annotations`. Gallery loads the former with preview handlers. | Flow | Unit-conversion version branches read. Live unit parsing and API support across host releases remain unverified. CreateFromRooms validation is GUI-07. |
| `lib/Snippets/_annotations.py` | No tracked external consumer found. Imports `_convert` and `_filtered_element_collector`. | Boundary | Creates text/regions/lines; caller must own transaction and valid view/document. Importing it also imports eager document collectors. |
| `lib/Snippets/_boundingbox.py` | No tracked consumer found. | Boundary | Geometric inclusion helper; strict XY comparisons were inspected. Boundary inclusion and transformed boxes require an explicit contract before reuse. |
| `lib/Snippets/_elements.py` | No tracked consumer found. | Boundary | Example collector uses an undeclared `doc`; not an independently importable ready utility. No production failure inferred. |
| `lib/Snippets/_excel.py` | No tracked consumer found; separate from active `lib/excel_com.py`. | Boundary | Example writer refers to undeclared workbook/environment symbols and lacks a complete resource-lifetime contract. It is not the Carbon Excel boundary. |
| `lib/Snippets/_filter_examples.py` | No tracked consumer found. Example main block. | Boundary | Document globals and string-filter constructor require adaptation to the target host before use. |
| `lib/Snippets/_filtered_element_collector.py` | Imported by dormant `_annotations`. | Boundary | Performs multiple full-document/view collections at import time. These snapshots and global document references must not become a persistent-pane data source without refresh/lifetime design. |
| `lib/Snippets/_filters.py` | No tracked consumer found. | Boundary | Document-bound filter helpers; string-rule constructor lacks a host-version branch. Verify official target APIs before activation. |
| `lib/Snippets/_groups.py` | No tracked consumer found. | Boundary | Selection dialogs and attached-group operations use explicit/default `uidoc`. Caller owns valid group/view and transaction context. |
| `lib/Snippets/_lines.py` | No tracked consumer found. | Boundary | Curve-sampling loop and temporary detail-curve transaction inspected. Sampling needs a positive-step contract; line-style helper mixes passed and module-level document/view context. |
| `lib/Snippets/_overrides.py` | No tracked consumer found. | Flow | SUP-03: failure while styling a supplied region invokes deletion. Other override helpers still require caller-owned transaction and ownership policy. |
| `lib/Snippets/_revisions.py` | No tracked consumer found. | Boundary | Creates revisions and edits sheet membership; caller owns transaction. Obsolete numbering fallback is explicitly unfinished in source. This is not the dependency used by current production revision toggles. |
| `lib/Snippets/_sheets.py` | No tracked consumer found. | Boundary | Titleblock/sheet query helpers include document defaults and legacy filter construction. Not the active `_selection.get_selected_sheets` function. |
| `lib/Snippets/_vectors.py` | No tracked consumer found. | Boundary | XY vector rotation preserving Z; no independent host mutation. Validate expected angle/unit contract when reused. |
| `lib/Snippets/_views.py` | No tracked consumer found. | Boundary | View/section construction and rename-retry boundaries inspected. Caller owns transactions; naming exhaustion and geometry validity need acceptance before use. |
| `lib/Snippets/__init__.py` | Package initializer. | Inventory | No activation side effect. |

Active-consumer anchors: [Find/Replace Views](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/script.py#L13>), [Find/Replace Sheets](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/script.py#L15>), and [Duplicate Sheets](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/script.py#L20>). The [gallery's Recall metadata](../../../lib/ui_gallery/launchers.py#L130) is not production activation; GUI-05 traces the separate preview content replacement.

## Findings requiring correction before activation

### SUP-01 — P3: Custom Properties applies displayed fields rather than the user's changes

**Confidence: confirmed source behavior; dormant component.** Evidence: [numeric display](../../../lib/customprops/custom_props_pane.py#L499), lines 499–503; [Apply](../../../lib/customprops/custom_props_pane.py#L1376), lines 1376–1391; [pending collection](../../../lib/customprops/custom_props_pane.py#L1393), lines 1393–1450.

`_collect_pending()` collects every non-empty editable field without consulting the existing dirty-state comparison. Doubles are first converted to display units and rounded to six decimals. Applying an unrelated edit therefore sends unchanged numeric fields through the setter using their rounded display values. The collector also skips empty strings, so intentionally clearing an editable string cannot be distinguished from leaving a field untouched. It strips leading/trailing spaces from every text value regardless of edit intent.

**Trigger if activated:** display a writable double whose value needs more than six display-unit decimals, change another field, then Apply; or clear a string field and Apply. **Consequence:** unrelated numeric precision can change, while the requested string clearing is omitted. There is no current production exposure established by this review.

**Remedy:** represent untouched, set-value, and clear-value separately. Use actual dirty-state tracking to build pending edits, preserve raw numeric values until intentionally changed, and define normalization by parameter type. Capture per-element setter results rather than discarding them at [lines 1452–1460](../../../lib/customprops/custom_props_pane.py#L1452).

**Acceptance:** an unrelated edit leaves exact numeric values unchanged; blanking a writable string clears it; unchanged and mixed fields produce no writes; deliberate zero/false values apply; pasted values obey the destination units and parameter type; rejected writes appear in an explicit failed outcome. Run multi-selection, type/instance, read-only, workset, and document-switch fixtures before enabling the pane.

### SUP-02 — P3: Recall persistence silently preserves old selections and can truncate its existing file

**Confidence: confirmed source behavior; dormant component.** Evidence: [close/save path](../../../lib/match/clipboard.py#L478), lines 478–506.

`_save_recall()` returns immediately when no items are selected. If the memory file previously held selections, clearing every checkbox and closing leaves those selections on disk. Non-empty saves open the existing path with `wb` before serialization; a serialization or write failure can truncate that file, and the catch suppresses the failure entirely.

**Trigger if activated:** clear all items after an earlier saved selection, or encounter a failed serialization/write while overwriting a memory file. **Consequence:** stale recall contents or loss of the prior usable recall payload, without a visible persistence error. This module does not itself load that file; the downstream reload contract must be established when wiring it.

**Remedy:** define empty recall as an intentional persisted empty state or explicit deletion. Serialize and validate before replacing the previous file, use a temporary file in the same directory with a safe replacement strategy for the supported runtime, and report failure while retaining the previous usable data. Establish a versioned payload and caller-owned file path. Do not treat arbitrary pickle data as a safe external interchange format.

**Acceptance:** save/reload selected items; clear all/save/reload; simulate serialization, permission, and partial-write failures; confirm the previous valid data survives failed replacement and errors are visible. No assertion of currently exploitable untrusted deserialization is made: an external input boundary was not established.

### SUP-03 — P3: The generic region styling helper deletes its input when styling fails

**Confidence: confirmed source behavior; no tracked caller.** Evidence: [override helper](../../../lib/Snippets/_overrides.py#L3), lines 3–38.

`override_graphics_region()` accepts an existing `region` and documents a graphics operation. Its bare exception handler calls `doc.Delete(region.Id)` for any error raised while building or applying overrides. The helper neither creates the supplied region nor establishes ownership of it.

**Trigger if reused:** an override setter or `SetElementOverrides` rejects a value while the caller has an open writable transaction. **Consequence:** the helper attempts to delete the supplied region instead of reporting that its appearance could not be updated. Whether deletion succeeds depends on the host and transaction; no live deletion was attempted.

**Remedy:** return/raise a styling failure without deleting caller-owned content. A workflow that creates a disposable region should own its rollback or cleanup explicitly, within the creation transaction.

**Acceptance:** inject failures at each override construction/application step and assert no delete is requested. In a disposable model, a rejected pattern or unsupported view leaves an existing region intact and reports the failure. Keep this helper unexposed until the ownership contract is corrected.

### SUP-04 — P3: Temporary section-box changes can commit without a durable restore state

**Confidence: confirmed operation ordering; dormant component.** Evidence: [temporary-box flow](../../../lib/sbox/sbox_actions.py#L201), lines 201–229; [restore flow](../../../lib/sbox/sbox_actions.py#L175), lines 175–194.

The initial temporary-box branch commits the new box before opening/writing the restore cache. If that write fails, the model has already changed while the prior box exists only in local memory. The exception is logged and the function returns no successful state. The restore branch likewise commits the restored model before rewriting the cache; failed cache cleanup can leave an already-consumed restore entry. Subsequent load errors are treated as an empty cache.

**Trigger if activated:** denied, interrupted, or failed restore-cache writes after a successful model transaction. **Consequence:** the next invocation cannot reliably distinguish a new temporary operation from restoration, or it reuses stale restore state. Undo remains a possible host recovery mechanism; this finding does not claim irreversible model loss.

**Remedy:** validate and durably stage recovery data before committing the temporary change, make cache replacement atomic where supported, and define compensation/reconciliation for failures between file and model updates. Include document identity in the persistence contract; the current entry key contains only a view ID and relies on the caller to scope the filename correctly. Report recovery instructions when consistency cannot be maintained.

**Acceptance:** inject file-open/serialize/replace failures before and after model changes; restarting the command must preserve or explicitly recover the original state. Test restore cleanup failure, corrupt cache, cancelled selection, switching documents with coincident view IDs, deleted views, inactive/active original boxes, and Undo. Verify in a disposable model before wiring a command.

## Additional readiness notes, not production defect findings

- **Selection cancellation:** [family selection](../../../lib/Selection/select_similar_family.py#L44) wraps the invalid-selection `exitscript=True` alert in a bare catch, then refers to `selected_element` before its assignment at line 50. A terminating exit/error before that assignment can become a second unbound-local error. Separate validation/cancellation from supported-element error handling before reuse.
- **Special-case selection:** `lib/Selection/super_select.py` repeats the Plan Region category value in the following MatchLine branch. Confirm the intended category and host behavior before connecting this selector; the current branch cannot provide its intended distinct match-line behavior.
- **Batch lifetime:** [the standalone 3D-view script](../../../commands/make3dview_command.py#L1) opens and saves documents without a close/finally policy, existing-name policy, per-model result, or continuation strategy. Its injected `__models__` execution contract is unspecified in this checkout. Do not advertise it as a supported batch command without an owner and fixtures.
- **Event lifecycle:** Custom Properties subscribes selection/document/view events on construction and unsubscribes on `Unloaded`. Reload/resubscribe behavior, callback ownership across document changes, and stale element references need live pane lifecycle tests. No current registered pane was found, so a live event leak or lost subscription is not asserted.
- **Cross-document clipboard:** raw ElementId values and displayed parameter values are not portable identity/unit contracts. Before allowing paste across documents, define compatible parameter identity, destination-unit conversion, category/type scope, and invalid-ID rejection. The present repository does not establish a production cross-document workflow.
- **Snippet reuse:** the examples intentionally contain global host context, caller-owned transactions, legacy API forms, and incomplete utilities. Preserve their provenance and distinguish examples from supported library APIs. Refactoring all snippets or treating hidden template placeholders as current production failures is not justified by this review.

## Acceptance and handoff

Resolve SUP-01 through SUP-04 when their components are selected for activation. A future integration change should add explicit launch/registration ownership, document/transaction lifetime rules, cancellation and failure outcomes, persisted-data contracts, and targeted host-free tests for the deterministic branches. Live Revit acceptance must then cover the actual registered command or pane rather than the UI Gallery preview.

The active consumers listed above remain part of the [production review](production-tools.md) and [overall validation record](validation-and-acceptance.md). No new active-production P1/P2 finding was established in this supplemental pass. Absence of such a finding is not certification that every dormant utility supports every Revit release.
