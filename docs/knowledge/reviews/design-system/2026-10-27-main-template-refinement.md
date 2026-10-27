# Main template refinement after owner review

Date: 2026-10-27. Baseline: `8084d53` on `master-dev`, plus this refinement.
The owner requested a closer match to Create from rooms before migration of
other windows. [The consolidation plan](../../../plans/custom-window-consolidation.md)
continues to own task status. The [initial delivery](2026-10-27-custom-window-foundation.md)
is preserved as historical evidence.

Follow-up owner changes, based on `f19e071`: both top/bottom gaps are now 8,
the prompt is 14-unit Title Case, and rows reuse KL&A list selection's native
WPF template. All local GUI commits are retained on `dev.GUI-Clean`;
`master-dev` is returned to its existing upstream tracking tip.

## Changes and measurements

Measurements use actual isolated WPF layout, in device-independent units.

| Detail | Initial main template | Revised reference |
| --- | --- | --- |
| Gap below header | 16 | 8, per follow-up owner request (first refinement used 4) |
| Gap below last action | 16 | 8 |
| Search field | 32 high, 12-unit text | 24 high, 14-unit text; matches Create from rooms' 24-high outer shell (22-high inner TextBox plus its border) |
| Search-to-prompt gap | 16 | 8 |
| Single-line checkbox row | 26 high; padding 4 on all sides | 20 high; padding 4,1, matching Create from rooms |
| Checkbox-to-label gap | 8 | 4, matching Create from rooms |
| Prompt | 12-unit sentence case | 14-unit Title Case: Select Elements: |
| Row hover/selection | Custom green treatment | Native KL&A list-selection WPF template, including blue hover |
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
sizes and centered pair/main arrangement remain unchanged; top/bottom clearances
follow the owner's latest 8-unit request.

## Render evidence

The actual WPF content renders were visually inspected, without showing
a window or invoking production commands:

| Reference/state | Render |
| --- | --- |
| Create from rooms | [Unchanged comparison](2026-10-27-main-template-refinement-evidence/create-from-rooms-reference.png) |
| KL&A list selection | [Unchanged native-row comparison](2026-10-27-main-template-layout-evidence/list-selection-reference.png) |
| Main template Normal | [Current reference](2026-10-27-main-template-layout-evidence/main-template-normal.png) |
| Empty | [Empty](2026-10-27-main-template-layout-evidence/main-template-empty.png) |
| Error | [Error](2026-10-27-main-template-layout-evidence/main-template-error.png) |
| Disabled | [Disabled](2026-10-27-main-template-layout-evidence/main-template-disabled.png) |
| Long content | [Wrapping and scrollbar](2026-10-27-main-template-layout-evidence/main-template-long-content.png) |

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
- Follow-up WPF checks assert both 8-unit gaps, the actual 14-unit prompt/font
  and Title Case constant, and that the template's row uses the very same native
  `ControlTemplate` instance as KL&A list selection in this host. This proves
  template reuse; live pointer-hover acceptance is still pending.
- Targeted Gallery metadata validation passed. No tool/extension version advance
  is required for this refinement of the existing unreleased delivery.

Reproduce using `gui_window*test.py` and `ui_gallery*test.py` unittest discovery,
and `scripts/validate_ui_gallery_wpf.ps1` as documented in the
[template guide](../../../../lib/GUI/_templates/KLCodeMainTemplate.md).
These checks do not establish actual keyboard/hover/pressed input, dragging,
Narrator, DPI/mixed-monitor behavior, or live Revit ownership. Those limits from
the initial delivery remain unchanged. Owner acceptance of this revised
reference is still pending before migrating other windows.
