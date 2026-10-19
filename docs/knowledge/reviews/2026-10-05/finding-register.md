# Prioritized finding register

Review date: 2026-10-05. Baseline `1562e96a5f6e23b7368c80e317868a0c059dc165`. This register indexes the detailed evidence and acceptance criteria; it does not replace them. All findings are open and no fixes were implemented by this review.

**54 findings: 6 P1, 36 P2, 12 P3.** Severity expresses the proposed order of work. Confidence and reachability are separate: DEV-11/12/13 are explicitly inferred host risks, several GUI consequences require live inspection, and SUP-01 through SUP-04 are dormant-component readiness issues. Source-confirmed does not mean reproduced in Revit.

P1: address before relying on the affected workflow. P2: bounded functional, usability or validation issue. P3: lower-priority consistency, documentation or activation prerequisite. No numeric severity score is used to imply engineering or accessibility certification.

## Urgent work

| ID | Finding | Evidence, proposed remedy and acceptance |
| --- | --- | --- |
| TOOL-01 | Stop before opening a workbook when macro security cannot be established | [Detailed finding](production-tools.md#tool-01--p1-stop-before-opening-a-workbook-when-macro-security-cannot-be-established) |
| TOOL-02 | Highlight 2D clears graphics it does not own | [Detailed finding](production-tools.md#tool-02--p1-highlight-2d-clears-graphics-it-does-not-own) |
| DEV-01 | failed Family Studio loads can resolve to unrelated same-name content | [Detailed finding](prototypes-and-family-studio.md#dev-01--p1-confirmed-failed-family-studio-loads-can-resolve-to-unrelated-same-name-content) |
| REP-01 | Startup Importer passes seed-document IDs into destination-document operations | [Detailed finding](repository-and-assets.md#rep-01--p1--startup-importer-passes-seed-document-ids-into-destination-document-operations) |
| REP-02 | Startup Importer reports success without checking transaction outcomes | [Detailed finding](repository-and-assets.md#rep-02--p1--startup-importer-reports-success-without-checking-transaction-outcomes) |
| REP-03 | Schedule import silently omits schedule semantics | [Detailed finding](repository-and-assets.md#rep-03--p1--schedule-import-silently-omits-schedule-semantics) |

## Complete register

| ID | Priority | Finding | Owning report |
| --- | --- | --- | --- |
| DEV-01 | P1 | failed Family Studio loads can resolve to unrelated same-name content | [Evidence and acceptance](prototypes-and-family-studio.md#dev-01--p1-confirmed-failed-family-studio-loads-can-resolve-to-unrelated-same-name-content) |
| REP-01 | P1 | Startup Importer passes seed-document IDs into destination-document operations | [Evidence and acceptance](repository-and-assets.md#rep-01--p1--startup-importer-passes-seed-document-ids-into-destination-document-operations) |
| REP-02 | P1 | Startup Importer reports success without checking transaction outcomes | [Evidence and acceptance](repository-and-assets.md#rep-02--p1--startup-importer-reports-success-without-checking-transaction-outcomes) |
| REP-03 | P1 | Schedule import silently omits schedule semantics | [Evidence and acceptance](repository-and-assets.md#rep-03--p1--schedule-import-silently-omits-schedule-semantics) |
| TOOL-01 | P1 | Stop before opening a workbook when macro security cannot be established | [Evidence and acceptance](production-tools.md#tool-01--p1-stop-before-opening-a-workbook-when-macro-security-cannot-be-established) |
| TOOL-02 | P1 | Highlight 2D clears graphics it does not own | [Evidence and acceptance](production-tools.md#tool-02--p1-highlight-2d-clears-graphics-it-does-not-own) |
| DEV-02 | P2 | blank Concrete Mix replacements can retain old requirements | [Evidence and acceptance](prototypes-and-family-studio.md#dev-02--p2-confirmed-and-reproduced-blank-concrete-mix-replacements-can-retain-old-requirements) |
| DEV-03 | P2 | sheet prototype transactions can escape their scope | [Evidence and acceptance](prototypes-and-family-studio.md#dev-03--p2-confirmed-sheet-prototype-transactions-can-escape-their-scope) |
| DEV-04 | P2 | Steel PSF history charts compute member PSF instead of story PSF | [Evidence and acceptance](prototypes-and-family-studio.md#dev-04--p2-confirmed-steel-psf-history-charts-compute-member-psf-instead-of-story-psf) |
| DEV-05 | P2 | Steel PSF drops checked stories hidden by a filter | [Evidence and acceptance](prototypes-and-family-studio.md#dev-05--p2-confirmed-and-reproduced-steel-psf-drops-checked-stories-hidden-by-a-filter) |
| DEV-06 | P2 | late Excel smoke failures delete the promised diagnostic assets | [Evidence and acceptance](prototypes-and-family-studio.md#dev-06--p2-confirmed-late-excel-smoke-failures-delete-the-promised-diagnostic-assets) |
| DEV-07 | P2 | unreadable comparison fields can be reported as unchanged | [Evidence and acceptance](prototypes-and-family-studio.md#dev-07--p2-confirmed-unreadable-comparison-fields-can-be-reported-as-unchanged) |
| DEV-08 | P2 | Family Studio omits failed-root warnings from Refresh Complete | [Evidence and acceptance](prototypes-and-family-studio.md#dev-08--p2-confirmed-family-studio-omits-failed-root-warnings-from-refresh-complete) |
| DEV-09 | P2 | partial Family Studio type-preview failure is silently accepted and discards prior mappings | [Evidence and acceptance](prototypes-and-family-studio.md#dev-09--p2-confirmed-partial-family-studio-type-preview-failure-is-silently-accepted-and-discards-prior-mappings) |
| DEV-10 | P2 | corrupt cached images can escape Family Studio selection handlers | [Evidence and acceptance](prototypes-and-family-studio.md#dev-10--p2-confirmed-corrupt-cached-images-can-escape-family-studio-selection-handlers) |
| DEV-11 | P2 | placed-family recent history can be lost when placement ends with Esc | [Evidence and acceptance](prototypes-and-family-studio.md#dev-11--p2-inferred-placed-family-recent-history-can-be-lost-when-placement-ends-with-esc) |
| DEV-12 | P2 | Beam Reaction collision checks read modified geometry before regeneration | [Evidence and acceptance](prototypes-and-family-studio.md#dev-12--p2-inferred-beam-reaction-collision-checks-read-modified-geometry-before-regeneration) |
| DEV-13 | P2 | Beam Reaction failure restoration is not guaranteed by rollback | [Evidence and acceptance](prototypes-and-family-studio.md#dev-13--p2-inferred-beam-reaction-failure-restoration-is-not-guaranteed-by-rollback) |
| DEV-14 | P2 | late Steel CSV write failure leaves a mismatched history set | [Evidence and acceptance](prototypes-and-family-studio.md#dev-14--p2-confirmed-late-steel-csv-write-failure-leaves-a-mismatched-history-set) |
| DEV-17 | P2 | generated prototype specifications misstate mutation, UI, and asset boundaries | [Evidence and acceptance](prototypes-and-family-studio.md#dev-17--p2-confirmed-generated-prototype-specifications-misstate-mutation-ui-and-asset-boundaries) |
| GUI-01 | P2 | shared styles remove keyboard focus feedback | [Evidence and acceptance](design-system-and-gui.md#gui-01--p2-shared-styles-remove-keyboard-focus-feedback) |
| GUI-02 | P2 | accent and muted text tokens are too dark for their actual backgrounds | [Evidence and acceptance](design-system-and-gui.md#gui-02--p2-accent-and-muted-text-tokens-are-too-dark-for-their-actual-backgrounds) |
| GUI-03 | P2 | long alert messages do not have a bounded scroll viewport | [Evidence and acceptance](design-system-and-gui.md#gui-03--p2-long-alert-messages-do-not-have-a-bounded-scroll-viewport) |
| GUI-04 | P2 | several inputs and per-row checkboxes lack explicit accessible identity | [Evidence and acceptance](design-system-and-gui.md#gui-04--p2-several-inputs-and-per-row-checkboxes-lack-explicit-accessible-identity) |
| GUI-05 | P2 | the Match Recall gallery preview discards the chrome it intends to review | [Evidence and acceptance](design-system-and-gui.md#gui-05--p2-the-match-recall-gallery-preview-discards-the-chrome-it-intends-to-review) |
| GUI-06 | P2 | the largest fixed window has no smaller-work-area strategy | [Evidence and acceptance](design-system-and-gui.md#gui-06--p2-the-largest-fixed-window-has-no-smaller-work-area-strategy) |
| REP-04 | P2 | Startup Importer's resource requirements are displayed but not validated | [Evidence and acceptance](repository-and-assets.md#rep-04--p2--startup-importers-resource-requirements-are-displayed-but-not-validated) |
| REP-05 | P2 | A dependency-load error raises a second exception and stops startup preloading | [Evidence and acceptance](repository-and-assets.md#rep-05--p2--a-dependency-load-error-raises-a-second-exception-and-stops-startup-preloading) |
| REP-06 | P2 | The consolidated release check does not exercise the compiled test projects | [Evidence and acceptance](repository-and-assets.md#rep-06--p2--the-consolidated-release-check-does-not-exercise-the-compiled-test-projects) |
| REP-07 | P2 | Preflight discovery can prompt and exit before a check is selected | [Evidence and acceptance](repository-and-assets.md#rep-07--p2--preflight-discovery-can-prompt-and-exit-before-a-check-is-selected) |
| REP-08 | P2 | Wall-naming check cancellation uses an unavailable IronPython 2 exception | [Evidence and acceptance](repository-and-assets.md#rep-08--p2--wall-naming-check-cancellation-uses-an-unavailable-ironpython-2-exception) |
| REP-09 | P2 | Several preflight checks ignore the supplied document | [Evidence and acceptance](repository-and-assets.md#rep-09--p2--several-preflight-checks-ignore-the-supplied-document) |
| TOOL-03 | P2 | Highlight 2D fails on empty views and does nothing for a valid non-red first override | [Evidence and acceptance](production-tools.md#tool-03--p2-highlight-2d-fails-on-empty-views-and-does-nothing-for-a-valid-non-red-first-override) |
| TOOL-04 | P2 | Revision schedule toggles report no-ops as changes and Shift-click does not update issued revisions | [Evidence and acceptance](production-tools.md#tool-04--p2-revision-schedule-toggles-report-no-ops-as-changes-and-shift-click-does-not-update-issued-revisions) |
| TOOL-05 | P2 | Unhide omits the second selected dependent view for the same hidden cloud | [Evidence and acceptance](production-tools.md#tool-05--p2-unhide-omits-the-second-selected-dependent-view-for-the-same-hidden-cloud) |
| TOOL-06 | P2 | Hide-cloud schedule counts increase before the sheet accepts the change | [Evidence and acceptance](production-tools.md#tool-06--p2-hide-cloud-schedule-counts-increase-before-the-sheet-accepts-the-change) |
| TOOL-07 | P2 | View Range treats relative level references as missing planes | [Evidence and acceptance](production-tools.md#tool-07--p2-view-range-treats-relative-level-references-as-missing-planes) |
| TOOL-08 | P2 | View Range can discard a requested level change and report success | [Evidence and acceptance](production-tools.md#tool-08--p2-view-range-can-discard-a-requested-level-change-and-report-success) |
| TOOL-09 | P2 | Section preview draws depth and cut faces before applying the cut-plane translation | [Evidence and acceptance](production-tools.md#tool-09--p2-section-preview-draws-depth-and-cut-faces-before-applying-the-cut-plane-translation) |
| TOOL-10 | P2 | Duplicate Sheets commits omitted viewports without an outcome report | [Evidence and acceptance](production-tools.md#tool-10--p2-duplicate-sheets-commits-omitted-viewports-without-an-outcome-report) |
| TOOL-11 | P2 | Legend copying assumes a source-to-destination ID correspondence that the API does not promise | [Evidence and acceptance](production-tools.md#tool-11--p2-legend-copying-assumes-a-source-to-destination-id-correspondence-that-the-api-does-not-promise) |
| TOOL-12 | P2 | Legend-copy completion counts selections rather than actual copies | [Evidence and acceptance](production-tools.md#tool-12--p2-legend-copy-completion-counts-selections-rather-than-actual-copies) |
| DEV-15 | P3 | Family Studio's 200-result cap is presented as the complete result count | [Evidence and acceptance](prototypes-and-family-studio.md#dev-15--p3-confirmed-family-studios-200-result-cap-is-presented-as-the-complete-result-count) |
| DEV-16 | P3 | three UI Gallery previews assume the development tab exists | [Evidence and acceptance](prototypes-and-family-studio.md#dev-16--p3-confirmed-three-ui-gallery-previews-assume-the-development-tab-exists) |
| DEV-18 | P3 | hidden starter examples contain copy-time runtime errors | [Evidence and acceptance](prototypes-and-family-studio.md#dev-18--p3-confirmed-hidden-starter-examples-contain-copy-time-runtime-errors) |
| DEV-19 | P3 | Element Takeoff omits the inches mark for integral lengths | [Evidence and acceptance](prototypes-and-family-studio.md#dev-19--p3-confirmed-element-takeoff-omits-the-inches-mark-for-integral-lengths) |
| GUI-07 | P3 | dormant CreateFromRooms silently substitutes zero after invalid input | [Evidence and acceptance](design-system-and-gui.md#gui-07--p3-dormant-createfromrooms-silently-substitutes-zero-after-invalid-input) |
| GUI-08 | P3 | the general ComboBox property tables describe a different template | [Evidence and acceptance](design-system-and-gui.md#gui-08--p3-the-general-combobox-property-tables-describe-a-different-template) |
| REP-10 | P3 | Startup Importer README contradicts its current model-writing behavior | [Evidence and acceptance](repository-and-assets.md#rep-10--p3--startup-importer-readme-contradicts-its-current-model-writing-behavior) |
| REP-11 | P3 | Ribbon palette exceptions remain undocumented at the asset level | [Evidence and acceptance](repository-and-assets.md#rep-11--p3--ribbon-palette-exceptions-remain-undocumented-at-the-asset-level) |
| SUP-01 | P3 | Custom Properties applies displayed fields rather than the user's changes | [Evidence and acceptance](support-components.md#sup-01--p3-custom-properties-applies-displayed-fields-rather-than-the-users-changes) |
| SUP-02 | P3 | Recall persistence silently preserves old selections and can truncate its existing file | [Evidence and acceptance](support-components.md#sup-02--p3-recall-persistence-silently-preserves-old-selections-and-can-truncate-its-existing-file) |
| SUP-03 | P3 | The generic region styling helper deletes its input when styling fails | [Evidence and acceptance](support-components.md#sup-03--p3-the-generic-region-styling-helper-deletes-its-input-when-styling-fails) |
| SUP-04 | P3 | Temporary section-box changes can commit without a durable restore state | [Evidence and acceptance](support-components.md#sup-04--p3-temporary-section-box-changes-can-commit-without-a-durable-restore-state) |

## Suggested implementation slices

| Slice | Findings | Completion boundary |
| --- | --- | --- |
| Excel opening security | TOOL-01 | Refuse Open when macro security cannot be established; test both COM paths and trusted macro fixture |
| Model/content identity and graphics ownership | DEV-01, TOOL-02 | No same-name fallback after failed load; preserve pre-existing graphics; host conflict/rollback/Undo fixtures |
| Startup Importer correctness | REP-01–04 | Destination identity mapping, supported schedule contract, complete preflight, committed-outcome reporting |
| Engineering data integrity | DEV-02, DEV-04/05/14 | Exact concrete blanking, stable checked selection, correct story aggregation, recoverable complete history publication |
| Revisions and view operations | TOOL-03–12, DEV-03/07/12/13 | Correct target scope and complete outcome reports; isolate geometry/transaction changes and test exact failures |
| Family Studio refresh/browser behavior | DEV-08–11/15 | Root/type/image failures visible, accurate placed history and discoverable result cap; independent follow-ups after load identity |
| GUI foundations | GUI-01–06 | Visible focus, readable enabled text, named inputs, bounded alerts, faithful preview and reachable large-window actions |
| Integration validation and diagnostic reliability | REP-05–09, DEV-06/16 | Safe preload errors, relevant compiled tests, noninteractive preflight discovery, correct-document checks, retained diagnostic assets, both tab layouts |
| Specifications and design consistency | REP-10/11, DEV-17–19, GUI-07/08 | Behavior-accurate docs, approved icon exceptions, correct notation and usable maintained templates |
| Dormant support activation | SUP-01–04 | Correct edit intent, safe recall persistence, caller-owned content preserved, durable section-box restore; only needed before activation |

Each slice needs a focused branch/PR into dev under the repository contribution policy, adjacent SPEC/tool-version treatment where applicable, the narrowest meaningful automated checks, and the relevant live acceptance from [the validation plan](validation-and-acceptance.md). Do not combine all findings into a single redesign or change imported assets without provenance review.

## Closure record template

For each chosen finding, record: approved scope, implementation PR/commit, regression fixture, automated result, exact host/version and live evidence (or explicit remaining limitation), updated contract, reviewer, and closure date. A passing source test alone cannot close a host-behavior or accessibility acceptance item.
