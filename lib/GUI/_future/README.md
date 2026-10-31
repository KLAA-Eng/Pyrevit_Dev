# Dormant windows

These windows have no production caller. They are kept for possible future
tools, not maintained as shipped UI: Create From Rooms
(`KLC-CreateFromRooms.xaml`, `CreateFromRooms.py`) and the Match Properties
recall windows under `match/` with their eight locale dictionaries.

- The UI Gallery still previews them through its reviewed adapters.
- `scripts/check_ui_scale.py` does not scan this folder.
- `CreateFromRooms.py` reads `__revit__` at import time; import it only inside
  a running pyRevit command.

Wire a window to a tool, or delete it with its Gallery entry, through the
[consolidation plan](../../../docs/plans/custom-window-consolidation.md)
(GUI-42).
