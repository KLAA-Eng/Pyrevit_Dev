# -*- coding: utf-8 -*-
__title__ = "Run Dynamo"
__author__ = "Your Name"

import os
import clr

clr.AddReference('RevitAPIUI')

script_dir = os.path.dirname(__file__)
dyn_path = os.path.join(script_dir, "script.dyn")

uiapp = __revit__

try:
    if not os.path.exists(dyn_path):
        raise Exception("Cannot find script.dyn at:\n{}".format(dyn_path))

    # Dig through all loaded apps and print types to identify the right one
    dynamo_app = None
    for app in uiapp.LoadedApplications:
        full_name = app.GetType().FullName
        if "DynamoRevitApp" in full_name or "DynamoRevit" in full_name:
            dynamo_app = app
            break

    if dynamo_app is None:
        raise Exception("Could not find Dynamo application in LoadedApplications")

    # List available methods to find the right one for your version
    methods = [m for m in dir(dynamo_app) if not m.startswith("_")]
    
    from pyrevit import forms
    forms.alert("Dynamo app type:\n{}\n\nAvailable methods:\n{}".format(
        dynamo_app.GetType().FullName,
        "\n".join(methods)
    ), title="Debug Info")

except Exception as e:
    from pyrevit import forms
    forms.alert("Error:\n{}".format(str(e)), title="Dynamo Launch Failed")