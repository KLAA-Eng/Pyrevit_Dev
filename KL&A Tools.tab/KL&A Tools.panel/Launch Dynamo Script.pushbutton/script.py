# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import clr

from pyrevit import forms, script, HOST_APP, UI

logger = script.get_logger()
bundle_dir = os.path.dirname(__file__)
dyn_file = os.path.join(bundle_dir, "MyGraph.dyn")

if not os.path.exists(dyn_file):
    forms.alert("Graph not found:\n{}".format(dyn_file), exitscript=True)

def run_graph(graph_path):
    clr.AddReference('PyRevitLoader')
    from pyrevit.runtime.types import DynamoBIMEngine, ScriptData, ScriptRuntime, ScriptRuntimeConfigs

    scriptdata = ScriptData()
    scriptdata.ScriptPath = graph_path

    config = ScriptRuntimeConfigs()
    runtime = ScriptRuntime(scriptdata, config)

    engine = DynamoBIMEngine()
    engine.Execute(runtime)

try:
    run_graph(dyn_file)

except Exception as ex:
    msg = str(ex)
    logger.error(msg)

    forms.alert(
        "Dynamo failed while initializing inside Revit.\n\n"
        "This usually means Dynamo itself cannot start cleanly in this session,\n"
        "not that the graph path is wrong.\n\n"
        "Try:\n"
        "1. Open Dynamo manually in Revit\n"
        "2. Disable Dynamo packages/custom nodes\n"
        "3. Update/Reboot Revit\n"
        "4. Test again\n\n"
        "Error:\n{}".format(msg),
        exitscript=True
    )