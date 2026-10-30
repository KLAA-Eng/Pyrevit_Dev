"""Allowlisted shared-dialog previews; no production callers or model data."""
from __future__ import unicode_literals

DIALOG_FILES = {
    'dialog-message': 'MessageDialog.xaml',
    'dialog-confirmation': 'MessageDialog.xaml',
    'dialog-selection': 'SelectionDialog.xaml',
    'dialog-parameters': 'SelectionDialog.xaml',
    'dialog-actions': 'ActionChoiceDialog.xaml',
    'dialog-text': 'TextPromptDialog.xaml',
}

DIALOG_TITLES = {
    'dialog-message': 'Shared dialog - Message',
    'dialog-confirmation': 'Shared dialog - Confirmation',
    'dialog-selection': 'Shared dialog - Grouped selection',
    'dialog-parameters': 'Shared dialog - Parameter selection',
    'dialog-actions': 'Shared dialog - Action choice',
    'dialog-text': 'Shared dialog - Text entry',
}
