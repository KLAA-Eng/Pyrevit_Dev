"""Opt-in shared dialogs. Importing this package does not load WPF or Revit."""
from .models import ActionChoice, DialogResult, SelectionGroup, SelectionItem


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
