"""Fictional scenarios over actual dialogs; collectors/production tools never run."""
from __future__ import unicode_literals

from GUI.dialogs import (ActionChoice, CommandSwitch, SelectionItem, create_message,
                         create_list_single, create_list_multiple, create_sheet_selector,
                         create_revision_selector, create_document_selector,
                         create_choice, create_text_prompt, create_command_switch,
                         RenameField, create_rename)
from .dialog_data import ACTION_IDS


def _selection_rows(identity):
    if identity == 'dialog-sheets':
        return [SelectionItem('s101', 'S101 - General Notes', 's101', 'Sheet - Documentation', ('Issue Set A',)),
                SelectionItem('s201', 'S201 - Foundation Plan', 's201', 'Sheet - Structural', ('Issue Set A',)),
                SelectionItem('s301', 'S301 - Framing Plan', 's301', 'Sheet - Structural', ('Issue Set B',))]
    if identity == 'dialog-revisions':
        return [SelectionItem('rev1', '1 - Issued for Review', 'rev1', '2026-09-12 | Issued'),
                SelectionItem('rev2', '2 - Coordination Update', 'rev2', '2026-10-02 | Unissued'),
                SelectionItem('rev3', '3 - Construction Update', 'rev3', '2026-10-29 | Unissued')]
    if identity == 'dialog-documents':
        return [SelectionItem('project1', 'Office Tower', 'project1', 'Project document | C:/Fictional/Project A/Office Tower.rvt'),
                SelectionItem('project2', 'Office Tower', 'project2', 'Project document | C:/Fictional/Project B/Office Tower.rvt'),
                SelectionItem('family1', 'Rectangular Column', 'family1', 'Family document | No file path')]
    return [SelectionItem('notes', 'General Notes', 'notes', 'Documentation', ('Architecture',)),
            SelectionItem('detail1', 'Typical Detail', 'detail1', 'Steel framing', ('Structural',)),
            SelectionItem('detail2', 'Typical Detail', 'detail2', 'Concrete foundation', ('Structural',)),
            SelectionItem('blocked', 'Unavailable Example', None, 'Unavailable in this fictional workflow', enabled=False)]


def create_dialog(launcher, state):
    from System.Windows import Visibility

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
        window = create_message(title, message, severity=severity,
            details='Fictional diagnostic detail.\nNo production command is invoked.' if identity == 'dialog-message' else '', **options)
    elif identity in ('dialog-sheets', 'dialog-revisions', 'dialog-documents', 'dialog-list-single', 'dialog-list-multiple'):
        rows = _selection_rows(identity)
        if is_long:
            rows += [SelectionItem('extra-' + str(index), 'Long fictional selection row ' + str(index) + ' - review context ' * 10,
                                   index, 'Additional description ' * 12, ('Additional',)) for index in range(45)]
        factory = {'dialog-sheets': create_sheet_selector, 'dialog-revisions': create_revision_selector,
                   'dialog-documents': create_document_selector, 'dialog-list-single': create_list_single,
                   'dialog-list-multiple': create_list_multiple}[identity]
        window = factory(title, [] if state == 'Empty' else rows, **options)
        if state == 'Error':
            window.accept_selection()
    elif identity in ACTION_IDS:
        with_details = identity in ('dialog-actions-details', 'dialog-actions-full')
        with_checkbox = identity in ('dialog-actions-checkbox', 'dialog-actions-full')
        rows = [ActionChoice('hide', 'Hide in the selected views', 'Hide the supplied elements in the chosen views.'),
                ActionChoice('unhide', 'Unhide in the selected views', 'Restore visibility for the supplied elements.'),
                ActionChoice('unavailable', 'Unavailable action', 'This fictional action is disabled.', enabled=False)]
        instruction = 'How should the selected elements be displayed?'
        body = 'Choose an action. This preview uses fictional data and changes no model.'
        details = 'Fictional diagnostic detail.\nNo production command is invoked.' if with_details else ''
        if is_long:
            instruction += ' Review the supplied project context before continuing.'
            body = '\n\n'.join([body + ' Additional review context. ' * 8] * 18)
            rows = [ActionChoice(row.Key, row.Label, row.Description + ' Supporting explanation. ' * 14,
                                 enabled=row.CanSelect) for row in rows]
            if with_details:
                details = 'Long diagnostic detail.\n' * 48
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
            checkbox_text='Apply this option to the selected views' if with_checkbox else '',
            help_text='Read the fictional workflow guide' if identity == 'dialog-actions-full' else '',
            help_uri='https://example.com/klcode/action-choice' if identity == 'dialog-actions-full' else None,
            **options)
    elif identity in ('dialog-command-switch', 'dialog-command-switch-plain'):
        rows = [ActionChoice('active', 'Use Active View', 'Continue with the current view.'),
                ActionChoice('selected', 'Choose Views', 'Open a selection workflow in a future caller.'),
                ActionChoice('unavailable', 'Unavailable Action', 'This action is disabled.', enabled=False)]
        if is_long:
            rows += [ActionChoice('extra-' + str(index), 'Additional command ' + str(index) + ' - detailed context ' * 6,
                                  'Long explanation ' * 24) for index in range(30)]
        switches = [CommandSwitch('details', 'Include Details'), CommandSwitch('preview', 'Preview Only', checked=True)]
        window = create_command_switch(title, [] if state == 'Empty' else rows,
                                        switches=switches if identity == 'dialog-command-switch' else (), **options)
        if state == 'Error':
            window.status_text.Text = 'Fictional feedback: choose an available command.'
            window.status_text.Visibility = Visibility.Visible
            window.fit_height()
    elif identity in ('dialog-rename', 'dialog-rename-two', 'dialog-rename-three'):
        count = {'dialog-rename': 1, 'dialog-rename-two': 2, 'dialog-rename-three': 3}[identity]
        names = ['Name'] if count == 1 else ['Number', 'Name', 'Description'][:count]
        fields = [RenameField('field-' + str(index), label, find='' if state in ('Empty', 'Error') else 'Existing',
                              replace='Replacement' if state == 'Error' and index == 0 else
                                      ('' if state == 'Empty' else 'Updated'),
                              prefix='Review context ' * 12 if is_long else '', allow_case=label != 'Number')
                  for index, label in enumerate(names)]
        window = create_rename(title, fields, **options)
        if state == 'Error':
            window.accept_rename()
    else:
        prompt = 'Enter a description.' if not is_long else 'Enter a description for this fictional review. ' * 12
        window = create_text_prompt(title, prompt, default='' if state in ('Empty', 'Error') else ('Fictional description ' * 30 if is_long else 'Fictional description'),
                                    required=state == 'Error', **options)
        if state == 'Error':
            window.accept_text()
    window.preview_state = state
    window.window_body.IsEnabled = state != 'Disabled'
    return window
