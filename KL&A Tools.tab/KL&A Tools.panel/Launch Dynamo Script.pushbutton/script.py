# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import clr

from pyrevit import script, forms

logger = script.get_logger()

# Get the current pushbutton folder
BUNDLE_DIR = os.path.dirname(__file__)
DYN_FILE = os.path.join(BUNDLE_DIR, "script.dyn")

if not os.path.exists(DYN_FILE):
    forms.alert("Dynamo graph not found:\n{}".format(DYN_FILE), exitscript=True)

try:
    # pyRevit runtime types
    clr.AddReference('PyRevitLoader')
    from pyrevit.runtime.types import DynamoBIMEngine, ScriptData, ScriptRuntime, ScriptRuntimeConfigs

    scriptdata = ScriptData()
    scriptdata.ScriptPath = DYN_FILE

    config = ScriptRuntimeConfigs()
    runtime = ScriptRuntime(scriptdata, config)

    engine = DynamoBIMEngine()
    engine.Execute(runtime)

except Exception as ex:
    logger.error("Failed to execute Dynamo graph: {}".format(ex))
    forms.alert("Failed to execute Dynamo graph.\n\n{}".format(ex), exitscript=True)