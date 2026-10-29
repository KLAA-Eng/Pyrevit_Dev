# -*- coding: utf-8 -*-
__title__ = "Base class for KL&A custom WPF windows."
__author__ = "Erik Frits"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
# ==================================================
from pyrevit import forms  # Needed for the wpf import to work.

import clr
clr.AddReference("System")
import wpf
from System.Windows import Window


# ╦ ╦╔═╗╔═╗  ╔╗ ╔═╗╔═╗╔═╗
# ║║║╠═╝╠╣   ╠╩╗╠═╣╚═╗║╣
# ╚╩╝╩  ╚    ╚═╝╩ ╩╚═╝╚═╝ WINDOW BASE
# ==================================================
class my_WPF(Window):
    """Base class for KL&A windows.

    Shared chrome (header Close, Escape, drag, footer links) is bound by
    ``GUI.window_chrome.load_window``; the legacy ``WPF_styles.xaml`` loader
    and the per-window chrome handlers were removed on 2026-10-29.
    """
