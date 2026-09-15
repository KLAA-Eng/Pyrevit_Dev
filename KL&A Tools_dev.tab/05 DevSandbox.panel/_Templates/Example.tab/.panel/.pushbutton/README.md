extension: .pushbutton

requires:
    - *script.*           # note the wildcard. BuildWall_script.py or Analyse-script.cs are both acceptable names
    - bundle.yaml         # includes bundle metadata e.g. tooltip message
                          # OPTIONAL for python scripts only.
                          # python scripts can use the __var__ convention to set bundle metadata

optional:
    - *config.*           # optional config scripts. Revit UI will show a ● in front of the button name e.g. "Match ●"
                          # Shift-Clicking the button, launches this config.* script instead
    - icon.png            # for Revit UI icons
    - icon.png            # for Revit UI icons in Dark mode
    - tooltip.png         # for Revit UI button tooltip image
    - tooltip.mp4         # for Revit UI button tooltip video
    - *help.*             # for Revit UI button help, opening with F1 key
    - lib/                # can include a lib/ directory that hosts modules required by the bundle code
    - bin/                # can include a bin/ directory that hosts binaries required by the bundle code

## Push-Button Bundle

Push Button bundles include a script that is executed fresh, every time the user clicks on the button. They are the most used bundle in pyRevit.

### IronPython Scripts

Push-Button bundles can contain a IronPython  `*.py` file as their main script. pyRevit will run the script with the active IronPython engine.

See Anatomy of IronPython Scripts  for more detail on IronPython scripts.

See Configure pyRevit for more information about setting the active IronPython engine version.

### CPython Scripts

Push-Button bundles can contain a CPython  `*.py` file as their main script. pyRevit will run the script with the active CPython engine.

See Anatomy of CPython Scripts  for more detail on CPython scripts.

See Configure pyRevit for more information about setting the active CPython engine version.

### C#, VB.NET Scripts

Push-Button bundles can contain a C#  `*.cs` , or a VB.NET `*.vb` file as their main script. pyRevit will compile and run the script.

See Anatomy of .NET (C#, VB) Scripts  for more detail on CPython scripts.

### DynamoBIM Scripts

Push-Button bundles can contain a DynamoBIM `*.dyn` file as their main script. pyRevit will launch the installed DynamoBIM on the host Revit and asks to run the bundle script.

**DynamoBIM Engine Configs**

Dynamo has an option to shutdown the executor after running the dynamo script. This means that scripts take longer to run since it has to load dynamo first (and if dynamo needs to check for updates or do other startup tasks that is also added to the script execution time)

You can specify whether to use a clean dynamo engine or keep it in memory for the next executions. Set the option below in your bundle file.

```yaml
engine:
  clean: false
```

Similarly, the Dynamo **Automation** mode. If Dynamo **Automation** is on, dynamo runtime will remain in memory for faster execution. This however causes issues with Dynamo definitions that create windows and GUI to get/report information from/to the user. Since the dynamo definition is initialized once in **Automation** mode, the GUIs only pop up once on the first execution and will not be opened after. For dynamo scripts containing GUI, the `automate` engine option must be `false`

```yaml
engine:
  automate: false
```

You can also set the other Dynamo Journal Keys in the bundle yaml file

```yaml
engine:
  dynamo_path: String
  dynamo_path_check_existing: Boolean
  dynamo_force_manual_run: Boolean
  dynamo_model_nodes_info: String
```

### Grasshopper Scripts

Push-Button bundles can contain a Grasshopper *.gh file as their main script. pyRevit will launch the installed Rhino.Inside.Revit on the host Revit and asks to run the bundle script.
