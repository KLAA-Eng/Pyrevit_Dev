## Link-Button Bundle

```
extension: .linkbutton
```

Link buttons can call an external command (implementing **IExternalCommand**) from another loaded Addin. Link buttons are good for adding shortcuts to other addin functionality in your pyRevit extensions to improve user experience. Link Buttons, need the parameters below defined in the bundles metadata file.
See Bundle Metadata  for more information on these files.

<aside>
<img src="https://s3-us-west-2.amazonaws.com/secure.notion-static.com/13493b74-af2d-40fa-83f0-91d77d4b53f4/alert.png" alt="https://s3-us-west-2.amazonaws.com/secure.notion-static.com/13493b74-af2d-40fa-83f0-91d77d4b53f4/alert.png" width="40px" /> **Note:** For Link Buttons to work properly, the target addin assembly must be already loaded when this button is being created, otherwise Revit can not tie the UI button to the assembly that is not already loaded.

</aside>

```yaml
# include the key:values below in the bundle metadata file

assembly: PyRevitTestLinkCommand.dll                # full path to dll. if the dll is included in the bundle lib/
                                                    # or the parent bundle lib/ directory just enter the full dll name
                                                    # pyRevit will find the dll in the parent lib/ directories

command_class: PyRevitTestLinkExternalCommand       # name of the external command class
```

As of pyRevit 4.8.5,you can also add Accessibility types to the link bundle file. Since Link buttons points to a completely different assembly, pyRevit can not assign its internal zero-doc or other automatic context filters to these buttons. If that is desired, it is better to use Invoke buttons instead.

```yaml
availability_class: PyRevitTestLinkExternalCommandAvail
```

The Link buttons assembly needs to implement an instance of the availability class. For example:

```csharp
public class PyRevitTestLinkExternalCommandAvail : IExternalCommandAvailability {
    public PyRevitTestLinkExternalCommandAvail() {}
    public bool IsCommandAvailable(UIApplication uiApp, CategorySet selectedCategories) {
        return true;
    }
}
```

Link Buttons can also define the link target inside the `script.py` file. This feature is to support legacy design and will not be supported in the future.

```python
__assembly__ = 'Addin assembly name'
__commandclass__ = 'Class name for the command'
```

For example to call the Interactive Python Shell from RevitPythonShell addin:

```python
__assembly__ = 'RevitPythonShell'
__commandclass__ = 'IronPythonConsoleCommand'
```
