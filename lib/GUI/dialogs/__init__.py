"""Opt-in shared dialogs. Importing this package does not load WPF or Revit."""
from .models import ActionChoice, DialogResult, SelectionGroup, SelectionItem
from .switch_models import CommandSwitch
from .rename_models import RenameField


def create_message(title, message, **options):
    from .windows import create_message as factory
    return factory(title, message, **options)


def create_selection(title, items, **options):
    from .windows import create_selection as factory
    return factory(title, items, **options)


def create_choice(title, choices, **options):
    from .windows import create_choice as factory
    return factory(title, choices, **options)


def create_text_prompt(title, prompt, **options):
    from .windows import create_text_prompt as factory
    return factory(title, prompt, **options)


def create_command_switch(title, choices, **options):
    from .command_switch_window import create_command_switch as factory
    return factory(title, choices, **options)


def create_rename(title, fields, version=None, owner=None, navigate=None):
    from .rename_window import create_rename as factory
    return factory(title, fields, version=version, owner=owner, navigate=navigate)


def _show(window):
    window.ShowDialog()
    return window.result


def show_message(title, message, **options):
    return _show(create_message(title, message, **options))


def select_items(title, items, **options):
    return _show(create_selection(title, items, **options))


def choose_action(title, choices, **options):
    return _show(create_choice(title, choices, **options))


def ask_text(title, prompt, **options):
    return _show(create_text_prompt(title, prompt, **options))


def command_switch(title, choices, **options):
    return _show(create_command_switch(title, choices, **options))


def rename(title, fields, version=None, owner=None, navigate=None):
    return _show(create_rename(title, fields, version=version, owner=owner, navigate=navigate))


def create_list_single(title, items, **options):
    return create_selection(title, items, multiple=False, **options)


def create_list_multiple(title, items, **options):
    return create_selection(title, items, multiple=True, **options)


def create_sheet_selector(title, items, groups=None, **options):
    options.setdefault('prompt', 'Select Sheets')
    return create_selection(title, items, groups=groups, all_label='All Sheets', **options)


def create_revision_selector(title, items, **options):
    options.setdefault('prompt', 'Select Revisions')
    return create_selection(title, items, **options)


def create_document_selector(title, items, **options):
    options.setdefault('prompt', 'Select Documents')
    return create_selection(title, items, **options)


def select_one(title, items, **options):
    return _show(create_list_single(title, items, **options))


def select_many(title, items, **options):
    return _show(create_list_multiple(title, items, **options))


def select_sheets(title, document, include_placeholders=False, filterfunc=None, **options):
    from .collectors import sheet_items
    items, groups = sheet_items(document, include_placeholders, filterfunc)
    return _show(create_sheet_selector(title, items, groups, **options))


def select_revisions(title, document, filterfunc=None, **options):
    from .collectors import revision_items
    return _show(create_revision_selector(title, revision_items(document, filterfunc), **options))


def select_open_documents(title, application, active_document, include_active=False,
                          include_families=True, filterfunc=None, **options):
    from .collectors import document_items
    items = document_items(application, active_document, include_active, include_families, filterfunc)
    return _show(create_document_selector(title, items, **options))
