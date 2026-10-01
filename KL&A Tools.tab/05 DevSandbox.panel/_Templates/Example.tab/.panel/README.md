## Panel UI Bundle

This bundle creates a Panel in a Ribbon Tab with the bundle name.

```
extension: .panel
can_contain: All other command and UI bundle types
```

### Panel Background

You can set the background color for main, title, and slideout parts of a panel in the bundle metadata file. The colors are in CSS style and can be in ARGB or RGB format. Note that colors need to be wrapped in quotes since # is a comment character in YAML

# set background for all parts
background: '#ff0000'                   # or ARGB e.g. #ff0000ff

# or for individual parts
background:
  panel: '#ff0000'
  title: '#00ff00'
  slideout: '#0000ff'

### Collapsing Panels By Default

If you have a lot of panels on your tab, you might want to set some of those tabs to be collapsed by default so they don't take space on the tab bar. Users can hover over the panels to see the tools. Set the option below in the Panel bundle file.

```yaml
collapsed: true
```

This is how the panels would show up (collaped) and expand when user hovers over the panel.

![](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/4e2279f2-3620-4e26-99a5-eb300a924e8b/66415326-338e7200-e9b0-11e9-8c18-2c4b1c6ba2bd.gif)

##
