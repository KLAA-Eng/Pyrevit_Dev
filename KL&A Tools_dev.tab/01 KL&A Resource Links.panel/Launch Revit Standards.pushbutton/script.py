# -*- coding: utf-8 -*-
__title__ = "RVT Stds\nOnenote"
__version__ = "v1.0"

import subprocess

onenote_uri = r"onenote:https://klaa.sharepoint.com/Shared%20Documents/Revit%20Notebook/"

subprocess.Popen(['cmd', '/c', 'start', '', onenote_uri], shell=False)

##NOTESgit
