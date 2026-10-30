"""Allowlisted shared-dialog previews; no production callers or model data."""
from __future__ import unicode_literals

MESSAGE_STATES = ('Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content')

DIALOG_FILES = {
    'dialog-message': 'MessageDialog.xaml',
    'dialog-sheets': 'SelectionDialog.xaml',
    'dialog-revisions': 'SelectionDialog.xaml',
    'dialog-documents': 'SelectionDialog.xaml',
    'dialog-list-single': 'SelectionDialog.xaml',
    'dialog-list-multiple': 'SelectionDialog.xaml',
    'dialog-actions': 'ActionChoiceDialog.xaml',
    'dialog-text': 'TextPromptDialog.xaml',
    'dialog-command-switch': 'CommandSwitchDialog.xaml',
}

DIALOG_TITLES = {
    'dialog-message': 'Shared dialog - Message',
    'dialog-sheets': 'Shared dialog - Sheets',
    'dialog-revisions': 'Shared dialog - Revisions',
    'dialog-documents': 'Shared dialog - Open documents',
    'dialog-list-single': 'Shared dialog - List single',
    'dialog-list-multiple': 'Shared dialog - List multiple',
    'dialog-actions': 'Shared dialog - Action choice',
    'dialog-text': 'Shared dialog - Text entry',
    'dialog-command-switch': 'Shared dialog - Command Switch',
}
