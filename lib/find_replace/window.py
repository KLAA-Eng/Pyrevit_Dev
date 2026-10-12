# -*- coding: utf-8 -*-
"""Shared result presentation for the two command-local WPF dialogs."""

from System.Windows import Visibility

from find_replace.workflow import details, summary, unresolved


def present(window, result):
    """Replace this action's result, closing only for a clean operation."""
    if not hasattr(window, "_action_results"):
        window._action_results = {}
    had_unresolved = any(unresolved(item) for item in window._action_results.values())
    window._action_results[result["action"]] = result
    pending = [item for item in window._action_results.values() if unresolved(item)]
    if not pending and (result["changed"] or result["action"] != "Rename"
                        or had_unresolved):
        window.Close()
        return

    window.result_panel.Visibility = Visibility.Visible
    if pending:
        shown = pending if result in pending else pending + [result]
        window.result_details.Visibility = Visibility.Visible
        window.result_details.Text = "\n".join(details(item) for item in shown)
        window.Height = 485 + 20 * (len(shown) - 1)
    else:
        shown = [result]
        window.result_details.Visibility = Visibility.Collapsed
        window.result_details.Text = ""
        window.Height = 340
    window.result_summary.Text = "\n".join(summary(item) for item in shown)
