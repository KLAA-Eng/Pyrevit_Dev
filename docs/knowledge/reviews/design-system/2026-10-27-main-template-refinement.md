# Main template refinement after owner review

Date: 2026-10-27. Baseline: `8084d53` on `master-dev`, plus this refinement.
The owner requested a closer match to Create from rooms before migration of
other windows. [The consolidation plan](../../../plans/custom-window-consolidation.md)
continues to own task status. The [initial delivery](2026-10-27-custom-window-foundation.md)
is preserved as historical evidence.

## Changes and measurements

Measurements use actual isolated WPF layout, in device-independent units.

| Detail | Initial main template | Revised reference |
| --- | --- | --- |
| Gap below header | 16 | 4, matching Create from rooms' visible filter-shell inset |
| Search field | 32 high, 12-unit text | 24 high, 14-unit text; matches Create from rooms' 24-high outer shell (22-high inner TextBox plus its border) |
| Search-to-prompt gap | 16 | 8 |
| Single-line checkbox row | 26 high; padding 4 on all sides | 20 high; padding 4,1, matching Create from rooms |
| Checkbox-to-label gap | 8 | 4, matching Create from rooms |
| Default main-button border | Pale outline when defaulted, white outline when focused | No default outline; keyboard-focus underline |
| Footer links | Light green #9CC5AC | Existing Create from rooms link style, #407058 |
| Footer version | Light gray #B5C2BD; Version: v0.5 | Existing gray #808080; v0.5 only |
| List padding | 4 | 1; scrollbar visibility explicitly forwarded into its template |

The list remains full-width and fills the remaining height of the unchanged
432 x 576 reference. Short names therefore leave unused width; a small number
of items also leaves space below the last row. Neither is an extra text margin.
The revised long-name layout has a measured 8-unit clearance to the scrollbar.
Long words still wrap at word boundaries, which can leave natural line-end space.

Only the opt-in foundation, main template, metadata formatting, and their
tests/docs were changed. Create from rooms and other production windows were
used as references and remain unchanged. Header/footer heights, fixed action
sizes, centered pair/main arrangement, and bottom clearance remain as approved.

## Render evidence

All six actual WPF content renders were visually inspected, without showing
a window or invoking production commands:

| Reference/state | Render |
| --- | --- |
| Create from rooms | [Unchanged comparison](2026-10-27-main-template-refinement-evidence/create-from-rooms-reference.png) |
| Main template Normal | [Current reference](2026-10-27-main-template-refinement-evidence/main-template-normal.png) |
| Empty | [Empty](2026-10-27-main-template-refinement-evidence/main-template-empty.png) |
| Error | [Error](2026-10-27-main-template-refinement-evidence/main-template-error.png) |
| Disabled | [Disabled](2026-10-27-main-template-refinement-evidence/main-template-disabled.png) |
| Long content | [Wrapping and scrollbar](2026-10-27-main-template-refinement-evidence/main-template-long-content.png) |

## Verification

- Caller metadata/loader tests: 9 passed. Three expected failures first confirmed
  the old `Version:` prefix, then passed after removing it.
- Gallery suite: 50 run, 49 passed, 1 skipped for unavailable symlink privilege.
- Real IronPython/WPF: 35 Gallery entries, 66 existing custom/state constructions,
  Gallery filtering/deferred selection, and all shared-shell checks passed.
- Extended real-WPF assertions compare checkbox row height/text gap with actual
  Create from rooms, check search geometry and font size, pure version text,
  actual footer colors, transparent button border, and long-text clearance.
  Existing filtering, selection, disabled-label, simulated navigation and routed
  close checks remain passing.
- Targeted Gallery metadata validation passed. No tool/extension version advance
  is required for this refinement of the existing unreleased delivery.

Reproduce using `gui_window*test.py` and `ui_gallery*test.py` unittest discovery,
and `scripts/validate_ui_gallery_wpf.ps1` as documented in the
[template guide](../../../../lib/GUI/_templates/KLCodeMainTemplate.md).
These checks do not establish actual keyboard/hover/pressed input, dragging,
Narrator, DPI/mixed-monitor behavior, or live Revit ownership. Those limits from
the initial delivery remain unchanged. Owner acceptance of this revised
reference is still pending before migrating other windows.
