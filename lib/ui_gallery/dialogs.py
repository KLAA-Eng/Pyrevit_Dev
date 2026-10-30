"""Fictional scenarios over the actual opt-in GUI.dialogs factories."""
from __future__ import unicode_literals

from GUI.dialogs import (ActionChoice, SelectionItem, create_message,
                         create_selection, create_choice, create_text_prompt)


def create_dialog(launcher, state):
    identity = launcher['id']
    options = dict(version=launcher.get('tool_version'),
                   navigate=lambda uri: None)
    title = launcher.get('title', 'Shared dialog')
    long = state == 'Long content'
    if long:
        title += ' - A long fictional project and review context ' * 5
    if identity in ('dialog-message', 'dialog-confirmation'):
        message = ('This is a fictional preview. No model or file is changed.' if state != 'Empty' else '')
        if long:
            message = '\n\n'.join([message + ' Review the supplied context before continuing.'] * 32)
        window = create_message(title, message,
            buttons=('yes', 'no', 'cancel') if identity == 'dialog-confirmation' else ('ok',),
            severity='error' if state == 'Error' else ('warning' if identity == 'dialog-confirmation' else 'information'),
            details='Fictional diagnostic detail.\nNo production command is invoked.' if state != 'Empty' else '', **options)
    elif identity in ('dialog-selection', 'dialog-parameters'):
        if identity == 'dialog-parameters':
            rows = [SelectionItem('type-width', 'Width', 'type-width', 'Type parameter - Length', ('Type',)),
                    SelectionItem('instance-width', 'Width', 'instance-width', 'Instance parameter - Length', ('Instance',)),
                    SelectionItem('comments', 'Comments', 'comments', 'Instance parameter - Text', ('Instance',)),
                    SelectionItem('element-id', 'Element ID', None, 'Read-only; unavailable', ('Instance',), enabled=False)]
        else:
            rows = [SelectionItem('s101', 'S101 - General Notes', 's101', 'Sheet - Documentation', ('All Sheets', 'Issue Set A')),
                    SelectionItem('s201', 'S201 - Foundation Plan', 's201', 'Sheet - Structural', ('All Sheets', 'Issue Set A')),
                    SelectionItem('s301', 'S301 - Framing Plan', 's301', 'Sheet - Structural', ('All Sheets', 'Issue Set B')),
                    SelectionItem('placeholder', 'S901 - Placeholder', None, 'Unavailable in this fictional workflow', ('All Sheets',), enabled=False)]
        if long:
            rows += [SelectionItem('extra-' + str(index), 'Long fictional selection row ' + str(index) + ' - review context ' * 10,
                                   index, 'Additional description ' * 12, ('Additional',)) for index in range(45)]
        window = create_selection(title, [] if state == 'Empty' else rows, **options)
        if state == 'Error':
            window.accept_selection()
    elif identity == 'dialog-actions':
        rows = [ActionChoice('active', 'Use Active View', 'Continue with the current view.'),
                ActionChoice('selected', 'Choose Views', 'Open a selection workflow in a future caller.'),
                ActionChoice('unavailable', 'Unavailable Action', 'This action is disabled.', enabled=False)]
        if long:
            rows += [ActionChoice('extra-' + str(index), 'Additional action ' + str(index), 'Long explanation ' * 24) for index in range(20)]
        window = create_choice(title, [] if state == 'Empty' else rows, **options)
        if state == 'Error':
            window.accept_choice()
    else:
        prompt = 'Enter a description.' if not long else 'Enter a description for this fictional review. ' * 12
        window = create_text_prompt(title, prompt, default='' if state in ('Empty', 'Error') else ('Fictional description ' * 30 if long else 'Fictional description'),
                                    required=state == 'Error', **options)
        if state == 'Error':
            window.accept_text()
    window.preview_state = state
    window.window_body.IsEnabled = state != 'Disabled'
    return window
