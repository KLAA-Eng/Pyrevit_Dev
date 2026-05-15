# -*- coding: utf-8 -*-
import os
import clr

from Autodesk.Revit.UI import Result
from pyrevit import revit, forms

bundle_dir = os.path.dirname(__file__)
dyn_path = os.path.join(bundle_dir, 'script.dyn')

if not os.path.exists(dyn_path):
    forms.alert('Could not find script.dyn:\n{}'.format(dyn_path), exitscript=True)

try:
    clr.AddReference('DynamoRevitDS')
except:
    try:
        clr.AddReference('DynamoRevit')
    except Exception as ex:
        forms.alert('Could not load DynamoRevit assembly.\n\n{}'.format(ex), exitscript=True)

from Dynamo.Applications import DynamoRevit, DynamoRevitCommandData, JournalKeys

cmd_data = DynamoRevitCommandData()
cmd_data.Application = __revit__

journal_data = {
    JournalKeys.ShowUiKey: 'False',
    JournalKeys.AutomationModeKey: 'True',
    JournalKeys.DynPathKey: dyn_path,
    JournalKeys.DynPathExecuteKey: 'True',
    JournalKeys.ForceManualRunKey: 'False',
    JournalKeys.ModelShutDownKey: 'True',
    JournalKeys.ModelNodesInfo: 'False'
}

cmd_data.JournalData = journal_data

dynamo = DynamoRevit()
result = dynamo.ExecuteCommand(cmd_data)

if result != Result.Succeeded:
    forms.alert('Dynamo did not return Result.Succeeded.\nReturned: {}'.format(result))