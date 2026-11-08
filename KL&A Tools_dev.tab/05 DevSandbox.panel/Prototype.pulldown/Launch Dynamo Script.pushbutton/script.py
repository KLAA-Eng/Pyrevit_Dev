# -*- coding: utf-8 -*-

__title__ = "Launch Dynamo\n Script"
__version__ = "v0.0"
from GUI import tool_dialogs
import os
import clr

from pyrevit import HOST_APP, forms
from Autodesk.Revit.UI import Result

bundle_dir = os.path.dirname(__file__)
dyn_path = os.path.join(bundle_dir, 'script.dyn')

if not os.path.exists(dyn_path):
    tool_dialogs.alert('Could not find script.dyn:\n{}'.format(dyn_path), exitscript=True)

uiapp = HOST_APP.uiapp
uidoc = uiapp.ActiveUIDocument

if uidoc is None or uidoc.Document is None:
    tool_dialogs.alert('Open a Revit model or family first.', exitscript=True)

try:
    clr.AddReference('DynamoRevitDS')
except:
    clr.AddReference('DynamoRevit')

from Dynamo.Applications import DynamoRevit, DynamoRevitCommandData, JournalKeys

journal_data = {
    JournalKeys.ShowUiKey: 'True',
    JournalKeys.AutomationModeKey: 'True',
    JournalKeys.DynPathKey: dyn_path,
    JournalKeys.DynPathExecuteKey: 'True',
    JournalKeys.ForceManualRunKey: 'False',
    JournalKeys.ModelShutDownKey: 'False',
    JournalKeys.ModelNodesInfo: 'True'
}

cmd = DynamoRevitCommandData()
cmd.Application = uiapp
cmd.JournalData = journal_data

result = DynamoRevit().ExecuteCommand(cmd)

tool_dialogs.alert('Dynamo launch returned: {}'.format(result))
