# -*- coding: utf-8 -*-
__title__ = "Open\n KL&A Revit Standards Onenote Notebook"

import subprocess

onenote_uri = r"onenote:https://klaa.sharepoint.com/Shared%20Documents/Revit%20Notebook/"

subprocess.Popen(['cmd', '/c', 'start', '', onenote_uri], shell=False)

##NOTES