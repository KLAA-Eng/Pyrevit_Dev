"""Launcher metadata for the DevSandbox UI Gallery.

The gallery uses these stable identifiers to open known dialog families with
sample data.  Keeping the list host-independent allows it to be tested outside
of Revit and prevents filesystem XAML discovery from becoming executable.
"""
from __future__ import unicode_literals


_LAUNCHERS = (
    {
        'id': 'kla-create-from-rooms',
        'category': 'KL&A custom',
        'title': 'Create from rooms',
        'relative_path': 'lib/GUI/Tools/CreateFromRooms.xaml',
        'called_by': 'lib/GUI/Tools/CreateFromRooms.py',
        'description': 'Shared room-driven creation form with fictional room types.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-custom-alert',
        'category': 'KL&A custom',
        'title': 'KL&A alert',
        'relative_path': 'lib/GUI/CustomAlert.xaml',
        'called_by': 'lib/GUI/CustomAlert.py show_alert()',
        'description': 'Branded informational and warning dialog.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-duplicate-sheets',
        'category': 'KL&A custom',
        'title': 'Duplicate sheets',
        'relative_path': 'KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml',
        'called_by': 'KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/script.py',
        'description': 'Sheet duplication form with fictional selections.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-find-replace',
        'category': 'KL&A custom',
        'title': 'Find and replace',
        'relative_path': 'lib/GUI/FindReplace.xaml',
        'called_by': 'lib/GUI/FindReplace.py',
        'description': 'Branded rename form in safe preview mode.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-find-replace-sheets',
        'category': 'KL&A custom',
        'title': 'Find and replace sheets',
        'relative_path': 'KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml',
        'called_by': 'KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/script.py',
        'description': 'Sheet rename form with fictional names and numbers.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-find-replace-sheets-proto',
        'category': 'KL&A custom',
        'title': 'Find and replace sheets prototype',
        'relative_path': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml',
        'called_by': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/script.py',
        'description': 'DevSandbox sheet rename prototype with fictional names and numbers.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-find-replace-views',
        'category': 'KL&A custom',
        'title': 'Find and replace views',
        'relative_path': 'lib/Renaming/GUI_BaseRename.xaml',
        'called_by': 'KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/script.py via BaseRenaming.start()',
        'description': 'View rename form with fictional drawing names.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-find-replace-views-proto',
        'category': 'KL&A custom',
        'title': 'Find and replace views prototype',
        'relative_path': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml',
        'called_by': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/script.py',
        'description': 'DevSandbox view rename prototype with fictional drawing names.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-match-properties-recall',
        'category': 'KL&A custom',
        'title': 'Match properties recall',
        'relative_path': 'lib/match/clipboard_window.xaml',
        'called_by': 'lib/match/clipboard.py RecallWindow',
        'description': 'Modeless recall window with fictional match parameters.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-select-from-dict',
        'category': 'KL&A custom',
        'title': 'KL&A list selection',
        'relative_path': 'lib/GUI/SelectFromDict.xaml',
        'called_by': 'lib/GUI/SelectFromDict.py select_from_dict()',
        'description': 'Branded selectable list with sample family types.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-steel-psf',
        'category': 'KL&A custom',
        'title': 'Steel PSF story selection',
        'relative_path': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
        'called_by': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py',
        'description': 'DevSandbox branded story selector with sample levels.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'kla-view-range',
        'category': 'KL&A custom',
        'title': 'View range editor',
        'relative_path': 'KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
        'called_by': 'KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py',
        'description': 'View range form with fictional levels and elevations.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'pyrevit-alert',
        'category': 'pyRevit standard',
        'title': 'Alert',
        'relative_path': '',
        'called_by': 'pyrevit.forms.alert()',
        'description': 'Standard pyRevit notification dialog.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'pyrevit-ask-for-string',
        'category': 'pyRevit standard',
        'title': 'Text input',
        'relative_path': '',
        'called_by': 'pyrevit.forms.ask_for_string()',
        'description': 'Standard pyRevit single-value text prompt.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'pyrevit-command-switch',
        'category': 'pyRevit standard',
        'title': 'Command switch',
        'relative_path': '',
        'called_by': 'pyrevit.forms.CommandSwitchWindow.show()',
        'description': 'Standard pyRevit action picker with sample commands.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'pyrevit-select-list',
        'category': 'pyRevit standard',
        'title': 'List selection (multi-select)',
        'relative_path': '',
        'called_by': 'pyrevit.forms.SelectFromList.show(multiselect=True)',
        'description': 'Standard pyRevit list selector with seeded names.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'pyrevit-select-list-single',
        'category': 'pyRevit standard',
        'title': 'List selection (single-select)',
        'relative_path': '',
        'called_by': 'pyrevit.forms.SelectFromList.show(multiselect=False)',
        'description': 'Standard pyRevit single-choice list with seeded names.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'ui-gallery',
        'category': 'DevSandbox',
        'title': 'UI Gallery',
        'relative_path': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
        'called_by': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py',
        'description': 'This gallery window, opened as a nested safe preview.',
        'uses_seed_data': True,
        'can_launch': True,
    },
    {
        'id': 'ui-gallery-preview-fixture',
        'category': 'DevSandbox',
        'title': 'UI Gallery preview fixture',
        'relative_path': 'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml',
        'called_by': 'tests/ui_gallery_catalog_test.py fixture allowlist',
        'description': 'Safe test fixture for catalog preview checks.',
        'uses_seed_data': True,
        'can_launch': True,
    },
)


def gallery_launchers():
    """Return independent launcher dictionaries ordered by identifier."""
    return [dict(launcher) for launcher in _LAUNCHERS]


def launcher_by_id(launcher_id):
    """Return a launcher definition for an exact identifier, if available."""
    for launcher in _LAUNCHERS:
        if launcher['id'] == launcher_id:
            return dict(launcher)
    return None
