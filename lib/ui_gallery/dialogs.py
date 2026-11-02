"""Fictional scenarios over actual dialogs; collectors/production tools never run."""
from __future__ import unicode_literals

from GUI.dialogs import (ActionChoice, CommandSwitch, SelectionItem, create_message,
                         create_list_single, create_list_multiple, create_sheet_selector,
                         create_revision_selector, create_document_selector,
                         create_choice, create_text_prompt, create_command_switch,
                         RenameField, create_rename, sheet_fields, view_fields)
from .dialog_data import ACTION_IDS
from .scenarios import sample


def _item(key, label, value=None, description='', groups=(), enabled=True):
    """Selection row whose Gallery-supplied label and description carry the sample marker."""
    return SelectionItem(key, sample(label), value, sample(description), groups, enabled=enabled)


def _action(key, label, description='', enabled=True):
    return ActionChoice(key, sample(label), sample(description), enabled=enabled)


def _selection_rows(identity):
    # Follow-up: KLCodeWPF's F5 Selection trial now reads its editable JSONC
    # setups instead of these Gallery samples. Reconcile the pyRevit Gallery's
    # Selection scenarios with a shared sample source if the trial is adopted;
    # the Revit Gallery still uses this function and must remain functional.
    # Group keys double as the group dropdown labels, so they carry the marker too.
    if identity == 'dialog-sheets':
        return [_item('s101', 'S101 - General Notes', 's101', 'Sheet - Documentation', (sample('Issue Set A'),)),
                _item('s201', 'S201 - Foundation Plan', 's201', 'Sheet - Structural', (sample('Issue Set A'),)),
                _item('s301', 'S301 - Framing Plan', 's301', 'Sheet - Structural', (sample('Issue Set B'),))]
    if identity == 'dialog-revisions':
        return [_item('rev1', '1 - Issued for Review', 'rev1', '2026-09-12 | Issued'),
                _item('rev2', '2 - Coordination Update', 'rev2', '2026-10-02 | Unissued'),
                _item('rev3', '3 - Construction Update', 'rev3', '2026-10-29 | Unissued')]
    if identity == 'dialog-documents':
        return [_item('project1', 'Office Tower', 'project1', 'Project document | C:/Fictional/Project A/Office Tower.rvt'),
                _item('project2', 'Office Tower', 'project2', 'Project document | C:/Fictional/Project B/Office Tower.rvt'),
                _item('family1', 'Rectangular Column', 'family1', 'Family document | No file path')]
    return [_item('notes', 'General Notes', 'notes', 'Documentation', (sample('Architecture'),)),
            _item('detail1', 'Typical Detail', 'detail1', 'Steel framing', (sample('Structural'),)),
            _item('detail2', 'Typical Detail', 'detail2', 'Concrete foundation', (sample('Structural'),)),
            _item('blocked', 'Unavailable Example', None, 'Unavailable in this fictional workflow', enabled=False)]


# Command Switch fake rows. The Gallery and the Visual Studio designer (its
# Windows export and Samples.py) all show these: add, remove or edit a line.
COMMAND_SWITCH_COMMANDS = (
    # (key, label, description, enabled)
    ('active', 'Use Active View', 'Continue with the current view.', True),
    ('selected', 'Choose Views', 'Open a selection workflow in a future caller.', True),
    ('unavailable', 'Unavailable Action', 'This action is disabled.', False),
)
COMMAND_SWITCH_SWITCHES = (
    # (key, label, checked, enabled); only the "Commands with toggles" variant shows them.
    ('details', 'Include Details', False, True),
    ('preview', 'Preview Only', True, True),
)


def _command_switch_rows(identity, state='Normal'):
    """(commands, switches) for a Command Switch variant and state."""
    rows = [_action(key, label, description, enabled)
            for key, label, description, enabled in COMMAND_SWITCH_COMMANDS]
    if state == 'Long content':
        rows += [_action('extra-' + str(index), 'Additional command ' + str(index) + ' - detailed context ' * 6,
                         'Long explanation ' * 24) for index in range(30)]
    switches = [CommandSwitch(key, sample(label), checked=checked, enabled=enabled)
                for key, label, checked, enabled in COMMAND_SWITCH_SWITCHES]
    return ([] if state == 'Empty' else rows,
            switches if identity == 'dialog-command-switch' else [])


def create_dialog(launcher, state):
    identity = launcher['id']
    options = dict(version=launcher.get('tool_version'), navigate=lambda uri: None)
    title = launcher.get('title', 'Shared dialog')
    is_long = state == 'Long content'
    if is_long:
        title += ' - A long fictional project and review context ' * 5
    if identity in ('dialog-message', 'dialog-message-plain'):
        message = 'This is a fictional preview. No model or file is changed.' if state != 'Empty' else ''
        if is_long:
            message = '\n\n'.join([message + ' Review the supplied context before continuing.'] * 32)
        severity = {'Warning': 'warning', 'Error': 'error', 'Success': 'success'}.get(state, 'information')
        window = create_message(title, sample(message), severity=severity,
            details=sample('Fictional diagnostic detail.\nNo production command is invoked.') if identity == 'dialog-message' else '', **options)
    elif identity in ('dialog-sheets', 'dialog-revisions', 'dialog-documents', 'dialog-list-single', 'dialog-list-multiple'):
        rows = _selection_rows(identity)
        if is_long:
            rows += [_item('extra-' + str(index), 'Long fictional selection row ' + str(index) + ' - review context ' * 10,
                           index, 'Additional description ' * 12, (sample('Additional'),)) for index in range(45)]
        factory = {'dialog-sheets': create_sheet_selector, 'dialog-revisions': create_revision_selector,
                   'dialog-documents': create_document_selector, 'dialog-list-single': create_list_single,
                   'dialog-list-multiple': create_list_multiple}[identity]
        window = factory(title, [] if state == 'Empty' else rows, **options)
        if state == 'Error':
            window.accept_selection()
    elif identity in ACTION_IDS:
        with_details = identity in ('dialog-actions-details', 'dialog-actions-full')
        with_checkbox = identity in ('dialog-actions-checkbox', 'dialog-actions-full')
        rows = [_action('hide', 'Hide in the selected views', 'Hide the supplied elements in the chosen views.'),
                _action('unhide', 'Unhide in the selected views', 'Restore visibility for the supplied elements.'),
                _action('unavailable', 'Unavailable action', 'This fictional action is disabled.', enabled=False)]
        instruction = 'How should the selected elements be displayed?'
        body = 'Choose an action. This preview uses fictional data and changes no model.'
        details = 'Fictional diagnostic detail.\nNo production command is invoked.' if with_details else ''
        if is_long:
            instruction += ' Review the supplied project context before continuing.'
            body = '\n\n'.join([body + ' Additional review context. ' * 8] * 18)
            rows = [_action(row.Key, row.Label, row.Description + ' Supporting explanation. ' * 14,
                            enabled=row.CanSelect) for row in rows]
            if with_details:
                details = 'Long diagnostic detail.\n' * 48
        instruction, body, details = sample(instruction), sample(body), sample(details)
        if state == 'Empty':
            rows, instruction, body = [], '', ''
        buttons = ('yes', 'no', 'cancel') if identity == 'dialog-actions-buttons' else ('cancel',)
        if identity == 'dialog-actions-buttons' or state == 'Empty':
            rows = []
        if state == 'Empty':
            buttons = ()  # An empty task dialog supplies Close as its fallback.
        severity = {'Warning': 'warning', 'Error': 'error', 'Success': 'success'}.get(state, 'information')
        window = create_choice(title, rows, prompt=instruction, content=body, buttons=buttons,
            severity=severity if state != 'Empty' else None, details=details,
            checkbox_text=sample('Apply this option to the selected views') if with_checkbox else '',
            help_text=sample('Read the fictional workflow guide') if identity == 'dialog-actions-full' else '',
            help_uri='https://example.com/klcode/action-choice' if identity == 'dialog-actions-full' else None,
            **options)
    elif identity in ('dialog-command-switch', 'dialog-command-switch-plain'):
        rows, switches = _command_switch_rows(identity, state)
        window = create_command_switch(title, rows, switches=switches, **options)
    elif identity in ('dialog-rename', 'dialog-rename-sheets', 'dialog-rename-generic'):
        presets = {'dialog-rename': view_fields(), 'dialog-rename-sheets': sheet_fields(),
                   'dialog-rename-generic': [RenameField('mark', 'Mark')]}
        fields = presets[identity]
        for index, field in enumerate(fields):
            field.Label = sample(field.Label)
            field.Find = '' if state in ('Empty', 'Error') else sample('Existing')
            field.Replace = (sample('Replacement') if state == 'Error' and index == 0 else
                             ('' if state == 'Empty' else sample('Updated')))
            field.Prefix = sample('Review context ' * 12) if is_long else ''
        window = create_rename(title, fields, **options)
        if state == 'Error':
            window.accept_rename()
    else:
        prompt = 'Enter a description.' if not is_long else 'Enter a description for this fictional review. ' * 12
        window = create_text_prompt(title, sample(prompt), default='' if state in ('Empty', 'Error') else sample('Fictional description ' * 30 if is_long else 'Fictional description'),
                                    required=state == 'Error', **options)
        if state == 'Error':
            window.accept_text()
    window.preview_state = state
    window.window_body.IsEnabled = state != 'Disabled'
    return window
