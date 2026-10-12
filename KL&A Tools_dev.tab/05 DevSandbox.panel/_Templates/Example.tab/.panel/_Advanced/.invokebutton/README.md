## Invoke-Button Bundle

```
extension: .invokebutton
```

Invoke buttons can call an external command (implementing **IExternalCommand**) from another dll. However, they run the external command without loading the assembly in Revit context so the dll file can be modified while Revit is running. They are a great method to incorporate your high-performance C# dlls into your pyRevit extensions. Invoke Buttons, need the parameters below defined in the bundles' metadata file.
See Bundle Metadata  for more information on these files.

```yaml
# include the key:values below in the bundle metadata file

assembly: PyRevitTestInvokeCommand.dll              # full path to dll. if the dll is included in the bundle lib/
                                                    # or the parent bundle lib/ directory just enter the full dll name
                                                    # pyRevit will find the dll in the parent lib/ directories

command_class: PyRevitTestInvokeExternalCommand     # name of the external command class
```

Invoke Buttons are also smart about the assembly types implementing the IExternalCommand interface. So if there is only one external command inside your dll assembly that implements the IExternalCommand interface, you can skip defining the `command_class` in the bundle metadata file. pyRevit will automatically find the correct type and will run the `Execute` method on it.
