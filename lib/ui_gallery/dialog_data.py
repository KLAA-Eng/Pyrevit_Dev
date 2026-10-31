"""Allowlisted shared-dialog previews; no production callers or model data."""
from __future__ import unicode_literals

MESSAGE_STATES = ('Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content')
ACTION_STATES = MESSAGE_STATES
ACTION_VARIANTS = (
    ('dialog-actions', 'Commands'), ('dialog-actions-details', 'Commands + Details'),
    ('dialog-actions-checkbox', 'Commands + Checkbox'), ('dialog-actions-full', 'Full Content'),
    ('dialog-actions-buttons', 'Standard Buttons'))
ACTION_IDS = tuple(identity for identity, unused in ACTION_VARIANTS)

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
DIALOG_FILES.update((identity, 'ActionChoiceDialog.xaml') for identity in ACTION_IDS)

# Family rows are explicit; sharing a XAML source alone never groups callers.
DIALOG_FAMILIES = (
    ('dialog-message', 'Shared dialog - Message', (
        ('dialog-message-plain', 'Without Details'), ('dialog-message', 'With Details'))),
    ('dialog-selection', 'Shared dialog - Selection', (
        ('dialog-sheets', 'Sheets'), ('dialog-revisions', 'Revisions'),
        ('dialog-documents', 'Open Documents'), ('dialog-list-single', 'List Single'),
        ('dialog-list-multiple', 'List Multiple'))),
    ('dialog-actions', 'Shared dialog - Action choice', ACTION_VARIANTS),
    ('dialog-text', 'Shared dialog - Text entry', (('dialog-text', 'Default'),)),
    ('dialog-command-switch', 'Shared dialog - Command Switch', (
        ('dialog-command-switch-plain', 'Commands only'),
        ('dialog-command-switch', 'Commands with toggles'))),
    ('dialog-rename', 'KLC-Rename', (
        ('dialog-rename', 'Single field'), ('dialog-rename-two', 'Two fields'),
        ('dialog-rename-three', 'Multiple fields'))),
)
