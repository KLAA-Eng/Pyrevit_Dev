# Footerless Message and Custom Alert — 2026-10-30

The owner requested removal of the footer from shared Message and KL&A Custom
Alert. Baseline: `5ee31b9`. GUI-35 in the
[consolidation plan](../../../plans/custom-window-consolidation.md) owns status.

Both Message variants, the real legacy CustomAlert constructor and its Gallery
adapter call the existing per-instance `hide_footer()` before fitting height.
The footer is collapsed and its grid row is zero; the shared shell resource is
unchanged. Title/Close, Message OK, optional Details and other windows' footers
remain. Legacy alert APIs and caller workflows retain their existing contracts.

Verification: 25 focused Python tests pass. Installed IronPython/WPF passes 135
custom/variant/state constructions, 74 shared layouts, 45 production layouts and
the eight Message severity/details checks. The affected windows explicitly
assert collapsed footer, zero footer-row height and zero rendered footer height.
Details alignment/expansion, manual resizing and bounded long-content scrolling
still pass. Renders below were visually inspected.

- [Without Details](2026-10-30-footerless-alerts-evidence/message-without-details.png)
- [Expanded Details](2026-10-30-footerless-alerts-evidence/message-expanded-details.png)
- [Custom Alert](2026-10-30-footerless-alerts-evidence/custom-alert.png)

No shared resources or compiled assemblies changed. Live Revit acceptance remains
with the owner; the Windows probe uses fictional data without a model.
