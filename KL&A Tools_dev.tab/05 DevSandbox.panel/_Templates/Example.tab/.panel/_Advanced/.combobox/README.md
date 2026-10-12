## **ComboBox Bundle**

```yaml
extension: .combobox
```

ComboBox bundles create dropdown selection controls in the Revit ribbon. Unlike buttons, ComboBoxes do not execute commands directly. Instead, they provide a selection mechanism that scripts can respond to via events. ComboBoxes are useful for:

- Selecting options or settings
- Switching between modes or views
- Choosing from a list of predefined items

### **Bundle Structure**

```yaml
MyComboBox.combobox/
    bundle.yaml       # Required: configuration and members
    script.py         # Optional: initialization and event handling
    icon.png          # Optional: ComboBox icon (16x16 or 32x32)
    icon.dark.png     # Optional: dark theme icon

```

###

**ComboBox Properties**

| **Property** | **Type** | **Description** |
| --- | --- | --- |
| `title` | string | Display title for the ComboBox |
| `tooltip` | string | Short tooltip text |
| `tooltip_ext` | string | Extended tooltip description |
| `help_url` | string | URL for contextual help (F1) |
| `members` | list | List of member definitions |

**Member Properties**

| **Property** | **Aliases** | **Description** |
| --- | --- | --- |
| `id` | `name` | Unique identifier for the member |
| `text` | `title` | Display text shown in dropdown |
| `icon` | - | Path to icon image (16x16 PNG, relative to bundle) |
| `group` | `groupName` | Group name for organizing members visually |
| `tooltip` | - | Short tooltip for the member |
| `longDescription` | `tooltip_ext` | Extended tooltip description |
| `tooltipImage` | `tooltip_image` | Path to tooltip preview image |

**Member Formats**

Members can be defined in multiple formats:

# String format (id and text are the same)
members:
  - Option A
  - Option B

# List/tuple format
members:
  - [option_a, "Option A"]
  - [option_b, "Option B"]

# Dictionary format (recommended for rich metadata)
members:
  - id: option_a
    text: Option A
    icon: option_a.png
    group: My Group

  ### **Script Integration**
  
  ComboBox bundles can include a `script.py` with a `__selfinit__` function that runs during UI creation. This function allows you to:
  
  <aside>
  💡
  
  > IMPORTANT: Do not use print() inside event handlers! While print() works in __selfinit__, it causes silent failures inside event handlers (e.g., on_current_changed). Use TaskDialog.Show() from Autodesk.Revit.UI for feedback in event handlers.
  > 
  </aside>
  
  - Subscribe to ComboBox events
  - Dynamically add members
  - Configure the ComboBox based on conditions
  
  def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
      """Initialize the ComboBox.
  
      Args:
          script_cmp: The ComboBoxGroup component object (bundle metadata)
          ui_button_cmp: The _PyRevitRibbonComboBox wrapper instance
          __rvt__: The Revit UIApplication object
  
      Returns:
          bool: Return True if successful, False to deactivate the ComboBox
      """
      # Get the underlying Revit API ComboBox
      combobox = ui_button_cmp.get_rvtapi_object()
  
      # Subscribe to events
      combobox.CurrentChanged += on_selection_changed
  
      return True

### **Events**

The Revit API ComboBox supports three events that can be subscribed to in `__selfinit__`:

**CurrentChanged**

Fired when the user selects a different item.

```python
from pyrevit.forms import alert

def on_current_changed(sender, args):
    selected = sender.Current
    if selected:
        alert(
            "Selected: {}\nID: {}".format(selected.ItemText, selected.Name), 
            "Selection Changed"
        )

combobox.CurrentChanged += on_current_changed
```

**DropDownOpened**
Fired when the dropdown is opened (before items are shown). Avoid showing modal dialogs (like `TaskDialog`) in this handler as it blocks the dropdown expansion.

<aside>
💡

> Note: This event is useful for refreshing items or updating state before the user sees the dropdown, but not for showing UI feedback. Standard `print()` won't produce visible output in this context.
> 
</aside>

```python
def on_dropdown_opened(sender, args):
    # Useful for refreshing dynamic items or updating enabled states
    # Do NOT use TaskDialog here - it blocks the dropdown
    pass

combobox.DropDownOpened += on_dropdown_opened
```

**DropDownClosed**
Fired when the dropdown is closed.

```python
from pyrevit.forms import alert

def on_dropdown_closed(sender, args):
    current = sender.Current
    alert(
		    "Current selection: {}".format(current.ItemText if current else "None"),
        "Dropdown Closed"
    )

combobox.DropDownClosed += on_dropdown_closed
```

> Important: Keep references to event handlers on the `ui_button_cmp` object to prevent garbage collection:
> 
> 
> ```python
> ui_button_cmp._my_handler = on_current_changed
> ```
> 

### **Dynamic Members**

Members can be added programmatically in `__selfinit__`:

```python
from Autodesk.Revit.UI import ComboBoxMemberData

def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    # Add a separator
    ui_button_cmp.add_separator()

    # Add single item
    member = ComboBoxMemberData("item_id", "Item Text")
    member.GroupName = "Dynamic Items"
    ui_button_cmp.add_item(member)

    # Add multiple items
    items = [
        ComboBoxMemberData("item_1", "Item 1"),
        ComboBoxMemberData("item_2", "Item 2"),
    ]
    ui_button_cmp.add_items(items)

    return True
```

### **Wrapper API Reference**

The `ui_button_cmp` parameter provides these methods and properties:

**Methods**

| **Method** | **Description** |
| --- | --- |
| `get_rvtapi_object()` | Get underlying Revit API ComboBox |
| `add_item(member_data)` | Add a single ComboBoxMemberData |
| `add_items(member_data_list)` | Add multiple members at once |
| `add_separator()` | Add a separator line in dropdown |
| `get_items()` | Get list of ComboBoxMember objects |
| `get_title()` | Get display title |
| `set_title(title)` | Set display title |
| `set_contexthelp(url)` | Set F1 help URL |
| `get_contexthelp()` | Get contextual help object |
| `activate()` | Show and enable the ComboBox |
| `deactivate()` | Hide and disable the ComboBox |

**Properties**

| **Property** | **Type** | **Description** |
| --- | --- | --- |
| `current` | `ComboBoxMember` | Get/set currently selected member |
| `enabled` | `bool` | Enable/disable the control |
| `visible` | `bool` | Show/hide the control |
| `name` | `str` | ComboBox identifier |

### **Complete Example**

**bundle.yaml**

```
title: View Scale
tooltip: Select view scale
tooltip_ext: Changes the scale of the active view
help_url: https://docs.example.com/view-scale

members:
  - id: "1:1"
    text: "1:1"
    group: Detail Scales

  - id: "1:2"
    text: "1:2"
    group: Detail Scales

  - id: "1:50"
    text: "1:50"
    group: Plan Scales

  - id: "1:100"
    text: "1:100"
    group: Plan Scales
```

**script.py**

from pyrevit import revit
from Autodesk.Revit.UI import ComboBoxMemberData

def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    combobox = ui_button_cmp.get_rvtapi_object()

    def on_scale_changed(sender, args):
        selected = sender.Current
        if not selected:
            return

        scale_text = selected.Name  # e.g., "1:100"
        scale_value = int(scale_text.split(":")[1])

        doc = revit.doc
        view = revit.active_view

        if view and hasattr(view, 'Scale'):
            with revit.Transaction("Set View Scale"):
                view.Scale = scale_value

    combobox.CurrentChanged += on_scale_changed
    ui_button_cmp._scale_handler = on_scale_changed

    return True

### **Icon Specifications**

| **Icon Type** | **Size** | **Format** | **Purpose** |
| --- | --- | --- | --- |
| `icon.png` | 16x16 or 32x32 | PNG | Main ComboBox icon |
| `icon.dark.png` | 16x16 or 32x32 | PNG | Dark theme variant |
| Member `icon` | 16x16 | PNG | Individual dropdown item icon |
| `tooltipImage` | ~200-300px wide | PNG | Tooltip preview image |

### **Troubleshooting**

**ComboBox not appearing**

1. Check that the bundle directory ends with `.combobox`
2. Verify `bundle.yaml` is valid YAML syntax
3. Check pyRevit logs for parsing errors
4. Ensure `__selfinit__` returns `True` (not `False`)
5. **Do not use `print()` inside event handlers** - it causes silent failures. Use `TaskDialog.Show()` instead. (`print()` works fine in `__selfinit__` itself.)

**Members not showing**

1. Verify `members` key exists in `bundle.yaml`
2. Check member format matches supported formats
3. Look for errors in pyRevit output window

**Events not firing**

1. Ensure event handlers are subscribed in `__selfinit__`
2. Keep handler references on `ui_button_cmp` to prevent garbage collection
3. Check for exceptions in event handlers (they may be swallowed silently)

**Icons not displaying**

1. Check icon file path is relative to bundle directory
2. Verify icon file exists and is a valid PNG
3. Use 16x16 pixels for member icons
