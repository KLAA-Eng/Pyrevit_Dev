# # -*- coding: utf-8 -*-
# import os
# from pyrevit import forms, script

# CONFIG_KEY = 'project_folder_path'

# def get_saved_folder():
#     cfg = script.get_config()
#     return getattr(cfg, CONFIG_KEY, None)

# def save_folder(path):
#     cfg = script.get_config()
#     setattr(cfg, CONFIG_KEY, path)
#     script.save_config()

# def clear_folder():
#     cfg = script.get_config()
#     if hasattr(cfg, CONFIG_KEY):
#         setattr(cfg, CONFIG_KEY, '')
#         script.save_config()

# def prompt_for_folder(default=None):
#     return forms.ask_for_string(
#         default=default or '',
#         prompt='Paste the project folder path or folder URL.',
#         title='Set Project Folder'
#     )

# def open_folder(path):
#     os.startfile(path)

# saved_folder = get_saved_folder()

# if not saved_folder:
#     user_input = prompt_for_folder()

#     if not user_input:
#         script.exit()

#     save_folder(user_input)
#     forms.alert('Project folder saved.', title='pyRevit')
#     script.exit()

# try:
#     open_folder(saved_folder)
# except Exception as ex:
#     forms.alert(
#         'Could not open the saved folder:\n{}\n\nUse Reset to update it.'.format(saved_folder),
#         title='Open Folder Failed',
#         warn_icon=True
#     )
#     choice = forms.CommandSwitchWindow.show(
#         ['Reset Link', 'Clear Link', 'Cancel'],
#         message='Saved folder could not be opened.'
#     )

#     if choice == 'Reset Link':
#         new_input = prompt_for_folder(default=saved_folder)
#         if new_input:
#             save_folder(new_input)
#             forms.alert('Project folder updated.', title='pyRevit')
#     elif choice == 'Clear Link':
#         clear_folder()
#         forms.alert('Saved folder link cleared.', title='pyRevit')

#     script.exit()

# choice = forms.CommandSwitchWindow.show(
#     ['OK', 'Reset Link', 'Clear Link'],
#     message='Folder launched.'
# )

# if choice == 'Reset Link':
#     new_input = prompt_for_folder(default=saved_folder)
#     if new_input:
#         save_folder(new_input)
#         forms.alert('Project folder updated.', title='pyRevit')
# elif choice == 'Clear Link':
#     clear_folder()
#     forms.alert('Saved folder link cleared.', title='pyRevit')

# -*- coding: utf-8 -*-
import os

from pyrevit import revit, forms, script
from Autodesk.Revit.DB import StorageType

PARAM_NAME = "Project_Folder_Path"


def get_project_info_param(doc, param_name):
    proj_info = doc.ProjectInformation
    if not proj_info:
        return None, "Project Information element not found."

    param = proj_info.LookupParameter(param_name)
    if not param:
        return None, "Parameter '{}' was not found on Project Information.".format(param_name)

    if param.StorageType != StorageType.String:
        return None, "Parameter '{}' is not a Text parameter.".format(param_name)

    return param, None


def prompt_for_path(default=None):
    return forms.ask_for_string(
        default=default or "",
        prompt="Paste the project folder path or URL.",
        title="Set Project Folder"
    )


def open_target(path):
    os.startfile(path)


doc = revit.doc
param, error = get_project_info_param(doc, PARAM_NAME)

if error:
    forms.alert(
        error + "\n\nCreate/bind a shared Text parameter on Project Information first.",
        title="Project Folder Parameter Missing",
        warn_icon=True
    )
    script.exit()

saved_path = param.AsString() or ""

if not saved_path:
    user_input = prompt_for_path()
    if not user_input:
        script.exit()

    with revit.Transaction("Set Project Folder Path"):
        param.Set(user_input)

    forms.alert(
        "Project folder path saved to Project Information.",
        title="Path Saved"
    )
    script.exit()

try:
    open_target(saved_path)
except Exception:
    forms.alert(
        "Could not open the saved path:\n{}\n\nChoose Reset to update it or Clear to remove it.".format(saved_path),
        title="Open Failed",
        warn_icon=True
    )

    choice = forms.CommandSwitchWindow.show(
        ["Reset Link", "Clear Link", "Cancel"],
        message="Saved project folder path could not be opened."
    )

    if choice == "Reset Link":
        new_input = prompt_for_path(default=saved_path)
        if new_input:
            with revit.Transaction("Update Project Folder Path"):
                param.Set(new_input)
            forms.alert("Project folder path updated.", title="Updated")
    elif choice == "Clear Link":
        with revit.Transaction("Clear Project Folder Path"):
            param.Set("")
        forms.alert("Project folder path cleared.", title="Cleared")

    script.exit()

choice = forms.CommandSwitchWindow.show(
    ["Close", "Reset Link", "Clear Link"],
    message="Folder launched."
)

if choice == "Reset Link":
    new_input = prompt_for_path(default=saved_path)
    if new_input:
        with revit.Transaction("Update Project Folder Path"):
            param.Set(new_input)
        forms.alert("Project folder path updated.", title="Updated")

elif choice == "Clear Link":
    with revit.Transaction("Clear Project Folder Path"):
        param.Set("")
    forms.alert("Project folder path cleared.", title="Cleared")