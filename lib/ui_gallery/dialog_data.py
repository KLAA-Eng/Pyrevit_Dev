"""Allowlisted shared-dialog previews; no production callers or model data."""
from __future__ import unicode_literals

MESSAGE_STATES = ('Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content')

DIALOG_FILES = {
    'dialog-message': 'MessageDialog.xaml',
    'dialog-message-plain': 'MessageDialog.xaml',
    'dialog-sheets': 'SelectionDialog.xaml',
    'dialog-revisions': 'SelectionDialog.xaml',
    'dialog-documents': 'SelectionDialog.xaml',
    'dialog-list-single': 'SelectionDialog.xaml',
    'dialog-list-multiple': 'SelectionDialog.xaml',
    'dialog-actions': 'ActionChoiceDialog.xaml',
    'dialog-text': 'TextPromptDialog.xaml',
    'dialog-command-switch': 'CommandSwitchDialog.xaml',
    'dialog-command-switch-plain': 'CommandSwitchDialog.xaml',
    'dialog-rename': 'RenameDialog.xaml',
    'dialog-rename-two': 'RenameDialog.xaml',
    'dialog-rename-three': 'RenameDialog.xaml',
}

# Family rows are explicit; sharing a XAML source alone never groups callers.
DIALOG_FAMILIES = (
    ('dialog-message', 'Shared dialog - Message', (
        ('dialog-message-plain', 'Without Details'), ('dialog-message', 'With Details'))),
    ('dialog-selection', 'Shared dialog - Selection', (
        ('dialog-sheets', 'Sheets'), ('dialog-revisions', 'Revisions'),
        ('dialog-documents', 'Open Documents'), ('dialog-list-single', 'List Single'),
        ('dialog-list-multiple', 'List Multiple'))),
    ('dialog-actions', 'Shared dialog - Action choice', (('dialog-actions', 'Default'),)),
    ('dialog-text', 'Shared dialog - Text entry', (('dialog-text', 'Default'),)),
    ('dialog-command-switch', 'Shared dialog - Command Switch', (
        ('dialog-command-switch-plain', 'Commands only'),
        ('dialog-command-switch', 'Commands with toggles'))),
    ('dialog-rename', 'KLC-Rename', (
        ('dialog-rename', 'Single field'), ('dialog-rename-two', 'Two fields'),
        ('dialog-rename-three', 'Multiple fields'))),
)
