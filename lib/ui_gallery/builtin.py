"""Real pyRevit/native dialogs with fictional inputs and discarded results."""
from __future__ import unicode_literals

import os


_PICKER_NAMES = {
    'pyrevit-select-list': ['A101 - Floor Plan', 'A201 - Building Section', 'S101 - Foundation'],
    'pyrevit-select-list-single': ['A101 - Floor Plan', 'A201 - Building Section', 'S101 - Foundation'],
    'pyrevit-select-views': ['Floor Plan: Level 01', 'Section: Building A', 'Drafting: Typical detail'],
    'pyrevit-select-sheets': ['A101 - Floor Plan', 'S201 - Framing Plan', 'A601 - Door Schedule'],
    'pyrevit-select-revisions': ['01 - Coordination', '02 - Permit', '03 - Construction'],
    'pyrevit-select-open-docs': ['Fictional Project A.rvt', 'Fictional Project B.rvt'],
    'pyrevit-select-parameters': ['Mark [Instance]', 'Comments [Instance]', 'Type Mark [Type]'],
}


def picker_names(identity, state):
    """Sample labels for shared picker layouts; no model-query wrapper is called."""
    names = list(_PICKER_NAMES[identity])
    if state == 'Empty':
        return []
    if state == 'Long content':
        return ['{} - {}'.format(name, 'Long coordination description ' * 8)
                for name in names] * 15
    if state == 'Error':
        return ['Preview issue: fictional source is unavailable', 'Retry with another sample']
    return names


class SampleParameter(object):
    """Fictional presentation fields expected by pyRevit's parameter template."""
    def __init__(self, name, index):
        self.name = name
        self.istype = index % 2 == 1
        self.isreadonly = index == 2
        self.isunit = index == 1
        self.isshared = index == 0
        self.paramid = 'Sample {}'.format(index + 1)
        self.grouptype = 'Identity Data'
        self.storagetype = 'String' if index != 1 else 'Double'
        self.displayvalue = 'Fictional value {}'.format(index + 1)
        self.hasvalue = True


def _sample_list(forms, launcher, state):
    multiple = launcher['id'] != 'pyrevit-select-list-single'
    names = picker_names(launcher['id'], state)
    options = [forms.TemplateListItem(name, checked=False) for name in names]
    kwargs = dict(title=launcher['title'] + ' - Gallery', width=500, height=500,
                  multiselect=multiple, button_name='Use sample selection')
    if launcher['id'] == 'pyrevit-select-parameters':
        parameters = [SampleParameter(name, index) for index, name in enumerate(names)]
        options = [forms.TemplateListItem(item, checked=False, name_attr='name')
                   for item in parameters]
        options = {'All Parameters': options,
                   'Instance Parameters': [row for row in options if not row.item.istype],
                   'Type Parameters': [row for row in options if row.item.istype]}
        from pyrevit.forms import utils
        kwargs['item_template'] = utils.load_ctrl_template(
            os.path.join(forms.XAML_FILES_DIR, 'ParameterItemStyle.xaml'))
        kwargs['group_selector_title'] = 'Parameter Filters:'
        kwargs['default_group'] = 'All Parameters'
    elif launcher['id'] == 'pyrevit-select-sheets':
        options = {'All Sheets': options, 'Fictional Coordination Set': options[:2]}
        kwargs['group_selector_title'] = 'Sheet Sets:'
        kwargs['default_group'] = 'All Sheets'
    dialog = forms.SelectFromList(options, **kwargs)
    if state == 'Disabled':
        dialog.list_lb.IsEnabled = False
        dialog.select_b.IsEnabled = False
    dialog.ShowDialog()
    return 'Sample selection discarded. No model data was queried or changed.'


def launch_builtin(launcher, state='Normal'):
    """Open only explicit known form families; never invoke their calling tools."""
    if not launcher.get('can_launch') or state not in launcher.get('states', ['Normal']):
        raise ValueError('This preview or state is unavailable.')
    from pyrevit import forms
    identity = launcher['id']
    if identity in _PICKER_NAMES:
        return _sample_list(forms, launcher, state)
    message = ('Fictional validation issue. Correct the sample input and try again.'
               if state == 'Error' else 'Gallery preview: fictional data only.')
    if state == 'Long content':
        message = '\n'.join('Sample detail {}: {}'.format(index, 'Long project note ' * 5)
                            for index in range(1, 16))
    if identity == 'pyrevit-alert':
        forms.alert(message, title='Gallery - pyRevit alert', warn_icon=state == 'Error', cancel=True)
    elif identity == 'pyrevit-ask-for-string':
        forms.ask_for_string(default=message, prompt='Edit this fictional value:', title='Gallery - text input')
    elif identity == 'pyrevit-command-switch':
        forms.CommandSwitchWindow.show(['Review sample', 'Retry sample', 'Cancel preview'], message=message)
    elif identity == 'pyrevit-ask-for-color':
        forms.ask_for_color()
    elif identity == 'pyrevit-pick-file':
        forms.pick_file(file_ext='rvt', title='Gallery - choose a path (discarded)')
    elif identity == 'pyrevit-pick-folder':
        forms.pick_folder(title='Gallery - choose a folder (discarded)')
    elif identity == 'native-open-file':
        from Microsoft.Win32 import OpenFileDialog
        dialog = OpenFileDialog()
        dialog.Title = 'Gallery - choose a path (discarded)'
        dialog.ShowDialog()
    elif identity == 'native-revit-task-dialog':
        from Autodesk.Revit.UI import TaskDialog, TaskDialogCommandLinkId, TaskDialogCommonButtons
        dialog = TaskDialog('Gallery - Revit task dialog')
        dialog.MainInstruction = 'Choose a fictional action'
        dialog.MainContent = message
        dialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, 'Review fictional items')
        dialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink2, 'Skip fictional items')
        dialog.CommonButtons = TaskDialogCommonButtons.Cancel
        dialog.Show()
    else:
        raise ValueError('Unsupported built-in Gallery entry: {}'.format(identity))
    return 'Preview closed. Any selected value or path was discarded.'
