# -*- coding: utf-8 -*-
import os
from pyrevit import forms, script

CONFIG_KEY = 'project_folder_path'

def get_saved_folder():
    cfg = script.get_config()
    return getattr(cfg, CONFIG_KEY, None)

def save_folder(path):
    cfg = script.get_config()
    setattr(cfg, CONFIG_KEY, path)
    script.save_config()

def clear_folder():
    cfg = script.get_config()
    if hasattr(cfg, CONFIG_KEY):
        setattr(cfg, CONFIG_KEY, '')
        script.save_config()

def prompt_for_folder(default=None):
    return forms.ask_for_string(
        default=default or '',
        prompt='Paste the project folder path or folder URL.',
        title='Set Project Folder'
    )

def open_folder(path):
    os.startfile(path)

saved_folder = get_saved_folder()

if not saved_folder:
    user_input = prompt_for_folder()

    if not user_input:
        script.exit()

    save_folder(user_input)
    forms.alert('Project folder saved.', title='pyRevit')
    script.exit()

try:
    open_folder(saved_folder)
except Exception as ex:
    forms.alert(
        'Could not open the saved folder:\n{}\n\nUse Reset to update it.'.format(saved_folder),
        title='Open Folder Failed',
        warn_icon=True
    )
    choice = forms.CommandSwitchWindow.show(
        ['Reset Link', 'Clear Link', 'Cancel'],
        message='Saved folder could not be opened.'
    )

    if choice == 'Reset Link':
        new_input = prompt_for_folder(default=saved_folder)
        if new_input:
            save_folder(new_input)
            forms.alert('Project folder updated.', title='pyRevit')
    elif choice == 'Clear Link':
        clear_folder()
        forms.alert('Saved folder link cleared.', title='pyRevit')

    script.exit()

choice = forms.CommandSwitchWindow.show(
    ['OK', 'Reset Link', 'Clear Link'],
    message='Folder launched.'
)

if choice == 'Reset Link':
    new_input = prompt_for_folder(default=saved_folder)
    if new_input:
        save_folder(new_input)
        forms.alert('Project folder updated.', title='pyRevit')
elif choice == 'Clear Link':
    clear_folder()
    forms.alert('Saved folder link cleared.', title='pyRevit')