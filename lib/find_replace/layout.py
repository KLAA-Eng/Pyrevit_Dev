# -*- coding: utf-8 -*-
"""Window heights of the Core Find and Replace dialogs (host-free; shared with the UI Gallery adapter).

The XAML opens at 313; after an action the result panel shows and the window grows to RESULTS_HEIGHT, plus one
RESULT_ROW_HEIGHT per additional unresolved result when the details readout is shown.
"""
SUMMARY_HEIGHT = 340
RESULTS_HEIGHT = 485
RESULT_ROW_HEIGHT = 20


def results_height(shown_results, with_details):
    """Height for ``shown_results`` results, ``with_details`` when the readout is visible."""
    if with_details:
        return RESULTS_HEIGHT + RESULT_ROW_HEIGHT * (max(shown_results, 1) - 1)
    return SUMMARY_HEIGHT
