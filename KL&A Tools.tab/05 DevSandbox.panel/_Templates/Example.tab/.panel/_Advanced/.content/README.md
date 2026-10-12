extension: .content

requires:
    - *.rfa        # Revit family file to be placed in Revit model when this button is clicked
    - bundle.yaml  # includes bundle metadata e.g. tooltip message
								   # metadata supported for file path to 
                   # relative path for main family: content: "..\\A.rfa"
                   # absolute path for main family: content: "C:\\Users\\Local Admin\\Documents\\GitHub\\pyRevit\\extensions\\pyRevitDevTools.extension\\pyRevitDev.tab\\Debug.panel\\Bundle Tests.pulldown\\B.rfa"
                   # relative path for alternative family (SHIFT+Click): content_alt: "..\\A.rfa"
                   # absolute path for alternative family (SHIFT+Click): content_alt: "C:\\Users\\Local Admin\\Documents\\GitHub\\pyRevit\\extensions\\pyRevitDevTools.extension\\pyRevitDev.tab\\Debug.panel\\Bundle Tests.pulldown\\B.rfa"
                   
optional:
    - *.rfa               # optional content file. Revit UI will show a ● in front of the button name e.g. "Marker ●"
                          # Shift-Clicking the button, places this content inside active Revit model
    - icon.png            # for Revit UI icons
    - icon.dark.png       # for Dark Theme Revit UI
    - tooltip.png         # for Revit UI button tooltip image
    - tooltip.mp4         # for Revit UI button tooltip video


## Content-Button Bundle

Content Bundles carry contents for Revit, and help with reducing modeling errors by making it easy to place specific contents inside Revit models. This bundle automatically places the specified Revit family file `.rfa` inside the active Revit document. 

```yaml
content: "..\\A.rfa" # absolute or relative path supported
content_alt: "C:\\Users\\Local Admin\\Documents\\GitHub\\pyRevit\\extensions\\pyRevitDevTools.extension\\pyRevitDev.tab\\Debug.panel\\Bundle Tests.pulldown\\B.rfa" # absolute or relative path supported
```

⚠️ Legacy way 

Content Bundles carry contents for Revit, and help with reducing modeling errors by making it easy to place specific contents inside Revit models. This bundle automatically places the included Revit family file `.rfa` inside the active Revit document. The current implementation only allows Revit families but this will be extended in the future to more content types. 

```
extension: .content
requires:
    - *content.rfa        # Revit family file to be placed in Revit model when this button is clicked
    - *content_XXXX.rfa   # content file for specific Revit version e.g. North Symbol_content_2020.rfa
    - bundle.yaml         # includes bundle metadata e.g. tooltip message

optional:
    - *other.rfa          # optional content file. Revit UI will show a ● in front of the button name e.g. "Marker ●"
                          # Shift-Clicking the button, places this content inside active Revit model
    - *other_XXXX.rfa     # optional content file for specific Revit version e.g. North Symbol_other_2020.rfa
    - icon.png            # for Revit UI icons
    - tooltip.png         # for Revit UI button tooltip image
    - tooltip.mp4         # for Revit UI button tooltip video
```
