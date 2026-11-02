# Superseded windows

These windows still run, but a shared dialog in [`lib/GUI/dialogs`](../dialogs/README.md)
now covers what they do. They sit here, out of the component review, until each
calling tool switches to its replacement; then the window and its adapter are deleted.
They receive reference fixes only, not design work.

| Window | Replacement | Still opened by |
| --- | --- | --- |
| `CustomAlert.xaml` / `CustomAlert.py` | Message dialog (`GUI.dialogs` message) | No tool; the UI Gallery and tests only |
| `SelectFromDict.xaml` / `SelectFromDict.py` | Selection dialog (`GUI.dialogs` selection) | Every tool that calls `GUI.forms.select_from_dict` |

The Find/Replace Views and Sheets tool windows are superseded by the Rename dialog
too, but their XAML lives in the tools' own pushbutton folders, so it stays there
until those tools are reworked.
