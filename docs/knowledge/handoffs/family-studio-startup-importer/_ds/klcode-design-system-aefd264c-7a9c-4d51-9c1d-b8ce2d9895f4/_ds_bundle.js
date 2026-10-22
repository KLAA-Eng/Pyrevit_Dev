/* @ds-bundle: {"format":4,"namespace":"KLAToolsDesignSystem_aefd26","components":[{"name":"WindowFooter","sourcePath":"components/chrome/WindowFooter.jsx"},{"name":"WindowFrame","sourcePath":"components/chrome/WindowFrame.jsx"},{"name":"WindowHeader","sourcePath":"components/chrome/WindowHeader.jsx"},{"name":"Button","sourcePath":"components/forms/Button.jsx"},{"name":"CheckItem","sourcePath":"components/forms/CheckItem.jsx"},{"name":"FieldLabel","sourcePath":"components/forms/FieldLabel.jsx"},{"name":"FilterField","sourcePath":"components/forms/FilterField.jsx"},{"name":"GroupBorder","sourcePath":"components/forms/GroupBorder.jsx"},{"name":"ListPanel","sourcePath":"components/forms/ListPanel.jsx"},{"name":"RadioItem","sourcePath":"components/forms/RadioItem.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"SeparatorLine","sourcePath":"components/forms/SeparatorLine.jsx"},{"name":"TextField","sourcePath":"components/forms/TextField.jsx"},{"name":"AlertDialog","sourcePath":"ui_kits/ribbon/AlertDialog.jsx"},{"name":"RibbonButton","sourcePath":"ui_kits/ribbon/RibbonButton.jsx"},{"name":"RibbonPanel","sourcePath":"ui_kits/ribbon/RibbonPanel.jsx"},{"name":"RibbonStack","sourcePath":"ui_kits/ribbon/RibbonStack.jsx"},{"name":"RibbonTab","sourcePath":"ui_kits/ribbon/RibbonTab.jsx"}],"sourceHashes":{"components/chrome/WindowFooter.jsx":"edca952e6e14","components/chrome/WindowFrame.jsx":"865132bba492","components/chrome/WindowHeader.jsx":"60a4bc923a42","components/forms/Button.jsx":"4a8b655ee07e","components/forms/CheckItem.jsx":"24af18079de5","components/forms/FieldLabel.jsx":"43c19333065f","components/forms/FilterField.jsx":"4c43ffa46d14","components/forms/GroupBorder.jsx":"6e148e855841","components/forms/ListPanel.jsx":"ebee8f8391f4","components/forms/RadioItem.jsx":"7261fbaeb6d2","components/forms/Select.jsx":"d978cb73087f","components/forms/SeparatorLine.jsx":"1e660bc3b0b8","components/forms/TextField.jsx":"edae17b826f5","ui_kits/dialogs/AlertBox.jsx":"754d7ad16253","ui_kits/dialogs/BaseRename.jsx":"f2f17dc77b66","ui_kits/dialogs/CreateFromRooms.jsx":"3d7ea073dba5","ui_kits/dialogs/CustomAlert.jsx":"909a2a151255","ui_kits/dialogs/DuplicateSheets.jsx":"6fc9219d58f9","ui_kits/dialogs/Feedback.jsx":"06c94a715faa","ui_kits/dialogs/FindReplace.jsx":"ebfbe542c24f","ui_kits/dialogs/HostExtras.jsx":"9ba54608f4ad","ui_kits/dialogs/NativeChromeWindows.jsx":"16aeb6185734","ui_kits/dialogs/Pickers.jsx":"ed6e73f498ad","ui_kits/dialogs/ProtoWindows.jsx":"5821fd2253cf","ui_kits/dialogs/SelectFromDict.jsx":"98d193acdec1","ui_kits/dialogs/SheetsFindReplace.jsx":"47890245e11f","ui_kits/ribbon/AlertDialog.jsx":"4c0a8948e18f","ui_kits/ribbon/RibbonButton.jsx":"b5c5cba052ed","ui_kits/ribbon/RibbonPanel.jsx":"743b2fc7dc2d","ui_kits/ribbon/RibbonStack.jsx":"b3449ae71654","ui_kits/ribbon/RibbonTab.jsx":"10ee0890f808"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.KLAToolsDesignSystem_aefd26 = window.KLAToolsDesignSystem_aefd26 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/chrome/WindowFooter.jsx
try { (() => {
/** 25px footer band: "Prototype" link left, centred version string, "Outreach" link right. */
function WindowFooter({
  version = "Version: 1.0",
  leftLabel = "Prototype",
  leftHref = "#",
  linkLabel = "Outreach",
  linkHref = "#"
}) {
  const bar = {
    height: "24px",
    background: "var(--kl-charcoal)",
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    alignItems: "center",
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-12)"
  };
  const link = {
    color: "var(--kl-green-secondary)",
    fontWeight: 500,
    textDecoration: "underline"
  };
  const mid = {
    justifySelf: "center",
    color: "var(--kl-gray-medium)"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: bar
  }, /*#__PURE__*/React.createElement("a", {
    href: leftHref,
    style: {
      ...link,
      justifySelf: "start",
      marginLeft: "var(--space-10)"
    }
  }, leftLabel), /*#__PURE__*/React.createElement("span", {
    style: mid
  }, version), /*#__PURE__*/React.createElement("a", {
    href: linkHref,
    style: {
      ...link,
      justifySelf: "end",
      marginRight: "var(--space-10)"
    }
  }, linkLabel));
}
Object.assign(__ds_scope, { WindowFooter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/chrome/WindowFooter.jsx", error: String((e && e.message) || e) }); }

// components/chrome/WindowHeader.jsx
try { (() => {
/** Draggable 24px title band used at the top of every green-theme dialog.
    Defaults to the /KLCode Audiowide lockup (KLGreen slash, 16px); brandMark="text" gives the legacy Segoe Heavy wordmark. */
function WindowHeader({
  brand = "KLCode",
  brandMark = "audiowide",
  title = "",
  onClose,
  showClose = true
}) {
  const bar = {
    height: "24px",
    background: "var(--kl-charcoal)",
    display: "grid",
    gridTemplateColumns: "100px 1fr 66px",
    alignItems: "center",
    fontFamily: "var(--font-ui)"
  };
  const wordmark = {
    gridColumn: "1",
    gridRow: "1",
    justifySelf: "start",
    whiteSpace: "nowrap",
    marginLeft: "var(--space-5)",
    color: "var(--kl-white)",
    fontSize: "16px",
    fontWeight: "var(--weight-heavy)"
  };
  const heading = {
    gridColumn: "1 / 4",
    gridRow: "1",
    justifySelf: "center",
    color: "var(--kl-white)",
    fontSize: "14px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    maxWidth: "calc(100% - 212px)"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: bar
  }, brandMark === "audiowide" ? /*#__PURE__*/React.createElement("span", {
    style: {
      ...wordmark,
      fontFamily: "var(--font-logo)",
      fontWeight: 400,
      fontSize: "16px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--kl-green)"
    }
  }, "/"), brand) : /*#__PURE__*/React.createElement("span", {
    style: wordmark
  }, brand), /*#__PURE__*/React.createElement("span", {
    style: heading
  }, title), showClose ? /*#__PURE__*/React.createElement(CloseButton, {
    onClick: onClose
  }) : /*#__PURE__*/React.createElement("span", null));
}
function CloseButton({
  onClick
}) {
  const [hover, setHover] = React.useState(false);
  const btn = {
    gridColumn: "3",
    gridRow: "1",
    justifySelf: "center",
    alignSelf: "center",
    width: "var(--width-close)",
    height: "18px",
    border: 0,
    borderRadius: "var(--radius-lg)",
    fontFamily: "var(--font-button)",
    fontSize: "var(--text-10)",
    color: "var(--kl-pure-white)",
    cursor: "pointer",
    background: hover ? "var(--kl-green-secondary)" : "var(--kl-green-dark)"
  };
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    style: btn,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, "Close");
}
Object.assign(__ds_scope, { WindowHeader });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/chrome/WindowHeader.jsx", error: String((e && e.message) || e) }); }

// components/chrome/WindowFrame.jsx
try { (() => {
/**
 * Full borderless dialog shell: solid KLCharcoal base, 25px header band,
 * content region, optional footer band. Matches WindowStyle="None".
 * The old diagonal green wash is retired — backgrounds are flat #1A252B.
 * `bordered` adds the 1px KLGreen-dark window border the KL&A alert uses.
 */
function WindowFrame({
  title,
  width = 400,
  height,
  bordered = false,
  footer = false,
  version,
  brand,
  brandMark,
  onClose,
  children
}) {
  const shell = {
    width,
    height,
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    fontFamily: "var(--font-ui)",
    color: "var(--kl-white)",
    background: "var(--kl-charcoal)",
    border: bordered ? "var(--border-hairline) solid var(--kl-green-dark)" : "none"
  };
  const body = {
    flex: 1,
    minHeight: 0,
    display: "flex",
    flexDirection: "column"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: shell
  }, /*#__PURE__*/React.createElement(__ds_scope.WindowHeader, {
    title: title,
    brand: brand,
    brandMark: brandMark,
    onClose: onClose
  }), /*#__PURE__*/React.createElement("div", {
    style: body
  }, children), footer ? /*#__PURE__*/React.createElement(__ds_scope.WindowFooter, {
    version: version
  }) : null);
}
Object.assign(__ds_scope, { WindowFrame });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/chrome/WindowFrame.jsx", error: String((e && e.message) || e) }); }

// components/forms/Button.jsx
try { (() => {
/** Green-theme push button: KLGreen-dark fill, 8px radius, Arial, hover swap. Text 12px (WPF default); Close is 10px. */
function Button({
  size = "md",
  disabled = false,
  onClick,
  children,
  style
}) {
  const [hover, setHover] = React.useState(false);
  const sizes = {
    sm: {
      width: "var(--width-close)",
      height: "var(--control-h-sm)",
      fontSize: "var(--text-10)"
    },
    md: {
      width: "var(--width-half)",
      height: "var(--control-h-sm)",
      fontSize: "var(--text-12)"
    },
    lg: {
      width: "var(--width-main)",
      height: "var(--control-h-2xl)",
      fontSize: "var(--text-12)"
    },
    auto: {
      padding: "0 var(--space-10)",
      height: "var(--control-h-2xl)",
      fontSize: "var(--text-12)"
    }
  };
  const base = {
    border: 0,
    borderRadius: "var(--radius-lg)",
    fontFamily: "var(--font-button)",
    color: "var(--kl-pure-white)",
    cursor: disabled ? "default" : "pointer",
    opacity: disabled ? 0.45 : 1,
    background: hover && !disabled ? "var(--kl-green-secondary)" : "var(--kl-green-dark)",
    ...sizes[size],
    ...style
  };
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    disabled: disabled,
    style: base,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Button.jsx", error: String((e && e.message) || e) }); }

// components/forms/CheckItem.jsx
try { (() => {
/** 15px gradient checkbox with the exact WPF checkmark path. */
function CheckItem({
  checked = false,
  disabled = false,
  onChange,
  variant = "bullet",
  children
}) {
  const [hover, setHover] = React.useState(false);
  const system = variant === "system";
  const row = {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-4)",
    cursor: disabled ? "default" : "pointer",
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-12)",
    fontWeight: system ? 500 : 400,
    color: disabled ? "var(--kl-gray-medium)" : "var(--kl-pure-white)",
    padding: "var(--space-1) 0"
  };
  const box = {
    width: "var(--checkbox-size)",
    height: "var(--checkbox-size)",
    flex: "0 0 auto",
    borderRadius: "var(--radius-xs)",
    background: hover && !disabled ? "var(--kl-charcoal-black)" : "var(--kl-check-fill)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  };
  if (system) {
    return /*#__PURE__*/React.createElement("label", {
      style: row
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      checked: checked,
      disabled: disabled,
      onChange: onChange,
      style: {
        margin: 0,
        accentColor: "var(--kl-green-dark)"
      }
    }), /*#__PURE__*/React.createElement("span", null, children));
  }
  return /*#__PURE__*/React.createElement("label", {
    style: row,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, /*#__PURE__*/React.createElement("span", {
    style: box
  }, checked ? /*#__PURE__*/React.createElement("svg", {
    width: "9",
    height: "9",
    viewBox: "0 0 9 9",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 0 4 L 3 8 8 0",
    fill: "none",
    stroke: disabled ? "var(--kl-gray-disabled-check)" : "var(--kl-white)",
    strokeWidth: "2"
  })) : null), /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: checked,
    disabled: disabled,
    onChange: onChange,
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", null, children));
}
Object.assign(__ds_scope, { CheckItem });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/CheckItem.jsx", error: String((e && e.message) || e) }); }

// components/forms/FieldLabel.jsx
try { (() => {
/** Sage caption sitting above a field or group. WPF `Label` style. */
function FieldLabel({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--kl-green)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-12)",
      padding: "var(--space-5) var(--space-5) var(--space-2)",
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { FieldLabel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/FieldLabel.jsx", error: String((e && e.message) || e) }); }

// components/forms/GroupBorder.jsx
try { (() => {
/** Labelled 10px-radius bordered group — "Additional Settings", input clusters. */
function GroupBorder({
  label,
  labelStyle,
  children,
  style
}) {
  const box = {
    border: "var(--border-hairline) solid var(--kl-green-dark)",
    borderRadius: "var(--radius-xl)",
    padding: "var(--space-10)",
    ...style
  };
  return /*#__PURE__*/React.createElement("div", null, label ? /*#__PURE__*/React.createElement(__ds_scope.FieldLabel, {
    style: {
      padding: "0 0 var(--space-2) var(--space-2)",
      ...labelStyle
    }
  }, label) : null, /*#__PURE__*/React.createElement("div", {
    style: box
  }, children));
}
Object.assign(__ds_scope, { GroupBorder });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/GroupBorder.jsx", error: String((e && e.message) || e) }); }

// components/forms/ListPanel.jsx
try { (() => {
/** Scrollable dark list container: navy fill, forest border, 10px radius. */
function ListPanel({
  height = 350,
  children,
  style
}) {
  const id = React.useId ? React.useId().replace(/:/g, "") : "lp";
  const cls = "kl-list-" + id;
  const box = {
    height,
    overflowY: "auto",
    background: "var(--kl-charcoal)",
    border: "var(--border-hairline) solid var(--kl-green-dark)",
    borderRadius: "var(--radius-xl)",
    padding: "var(--space-5)",
    boxSizing: "border-box",
    ...style
  };
  const css = "." + cls + "::-webkit-scrollbar{width:12px}." + cls + "::-webkit-scrollbar-track{background:var(--kl-green-dark);border-radius:var(--radius-xl);margin:3px}." + cls + "::-webkit-scrollbar-thumb{background:var(--kl-black);border-radius:var(--radius-lg);border:2px solid transparent;background-clip:content-box}";
  return /*#__PURE__*/React.createElement("div", {
    className: cls,
    style: box
  }, /*#__PURE__*/React.createElement("style", null, css), children);
}
Object.assign(__ds_scope, { ListPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/ListPanel.jsx", error: String((e && e.message) || e) }); }

// components/forms/RadioItem.jsx
try { (() => {
/** Green-theme radio row (View Duplicate Options). System bullet, 12px Medium label. */
function RadioItem({
  checked = false,
  name,
  value,
  onChange,
  disabled = false,
  children
}) {
  const row = {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-5)",
    cursor: disabled ? "default" : "pointer",
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-12)",
    fontWeight: 500,
    color: disabled ? "var(--kl-gray-medium)" : "var(--kl-white)",
    padding: "var(--space-2) 0"
  };
  return /*#__PURE__*/React.createElement("label", {
    style: row
  }, /*#__PURE__*/React.createElement("input", {
    type: "radio",
    name: name,
    value: value,
    checked: checked,
    disabled: disabled,
    onChange: onChange,
    style: {
      margin: 0,
      accentColor: "var(--kl-green-dark)"
    }
  }), /*#__PURE__*/React.createElement("span", null, children));
}
Object.assign(__ds_scope, { RadioItem });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/RadioItem.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
/** Green-theme dropdown: navy field, sage 1px border, 2px radius, 20px arrow cell. */
function Select({
  value,
  options = [],
  onChange,
  width = 200,
  disabled = false
}) {
  const [open, setOpen] = React.useState(false);
  const wrap = {
    position: "relative",
    width,
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-12)"
  };
  const field = {
    display: "grid",
    gridTemplateColumns: "1fr 20px",
    alignItems: "center",
    minHeight: "var(--control-h-sm)",
    height: "var(--control-h-md)",
    background: "var(--kl-charcoal)",
    border: "var(--border-hairline) solid var(--kl-green)",
    borderRadius: "var(--radius-xs)",
    color: disabled ? "var(--kl-gray-disabled)" : "var(--kl-pure-white)",
    cursor: disabled ? "default" : "pointer"
  };
  const text = {
    padding: "0 var(--space-3)",
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis"
  };
  const arrowCell = {
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderLeft: "var(--border-hairline) solid var(--kl-green)"
  };
  const popup = {
    position: "absolute",
    top: "calc(100% + 2px)",
    left: 0,
    right: 0,
    zIndex: 5,
    background: "var(--kl-charcoal)",
    border: "var(--border-hairline) solid var(--kl-green)",
    padding: "6px 4px",
    maxHeight: 160,
    overflowY: "auto"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: wrap
  }, /*#__PURE__*/React.createElement("div", {
    style: field,
    onClick: () => !disabled && setOpen(!open)
  }, /*#__PURE__*/React.createElement("span", {
    style: text
  }, value), /*#__PURE__*/React.createElement("span", {
    style: arrowCell
  }, /*#__PURE__*/React.createElement("svg", {
    width: "8",
    height: "6",
    viewBox: "0 0 8 6",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M0,0 L0,2 L4,6 L8,2 L8,0 L4,4 z",
    fill: "var(--kl-pure-white)"
  })))), open ? /*#__PURE__*/React.createElement("div", {
    style: popup
  }, options.map(opt => /*#__PURE__*/React.createElement(SelectOption, {
    key: opt,
    label: opt,
    onPick: () => {
      setOpen(false);
      onChange && onChange(opt);
    }
  }))) : null);
}
function SelectOption({
  label,
  onPick
}) {
  const [hover, setHover] = React.useState(false);
  const row = {
    padding: "var(--space-2)",
    color: "var(--kl-pure-white)",
    cursor: "pointer",
    background: hover ? "var(--kl-charcoal-gray)" : "transparent"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: row,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    onClick: onPick
  }, label);
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/SeparatorLine.jsx
try { (() => {
/** 1px rule. Forest green in the dark theme, #DDDDDD on native surfaces. */
function SeparatorLine({
  tone = "dark",
  style
}) {
  const line = {
    height: 1,
    background: tone === "native" ? "var(--kl-rule)" : "var(--kl-green-dark)",
    margin: "var(--space-6) 0",
    ...style
  };
  return /*#__PURE__*/React.createElement("div", {
    style: line
  });
}
Object.assign(__ds_scope, { SeparatorLine });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/SeparatorLine.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextField.jsx
try { (() => {
/** Dark-theme text input: charcoal fill, sage border, 5px radius. White text by default; tone="sage" for the green-text variant. */
function TextField({
  value,
  onChange,
  placeholder,
  width,
  tone = "white",
  height = "var(--control-h-md)",
  fontSize = "var(--text-12)",
  style
}) {
  const field = {
    width,
    height,
    boxSizing: "border-box",
    padding: "0 var(--space-5)",
    background: "var(--kl-charcoal)",
    color: tone === "white" ? "var(--kl-white)" : "var(--kl-green)",
    border: "var(--border-hairline) solid var(--kl-green)",
    borderRadius: "var(--radius-md)",
    fontFamily: "var(--font-ui)",
    fontSize,
    outline: "none",
    ...style
  };
  return /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: value,
    placeholder: placeholder,
    onChange: onChange,
    style: field
  });
}
Object.assign(__ds_scope, { TextField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextField.jsx", error: String((e && e.message) || e) }); }

// components/forms/FilterField.jsx
try { (() => {
/** Magnifier glyph + filter input, the standard top row of a list dialog.
    Glyph and input text are KLWhite; the field border is KLGreen-dark (per XAML). */
function FilterField({
  value,
  onChange,
  placeholder = ""
}) {
  const row = {
    display: "flex",
    alignItems: "flex-start",
    gap: "var(--space-5)",
    padding: "var(--space-8) var(--space-10) var(--space-5) var(--space-5)"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: row
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-14)",
      lineHeight: "var(--control-h-md)",
      color: "var(--kl-white)"
    }
  }, "\uD83D\uDD0D"), /*#__PURE__*/React.createElement(__ds_scope.TextField, {
    value: value,
    onChange: onChange,
    placeholder: placeholder,
    fontSize: "var(--text-12)",
    style: {
      flex: 1,
      borderColor: "var(--kl-green-dark)"
    }
  }));
}
Object.assign(__ds_scope, { FilterField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/FilterField.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/AlertBox.jsx
try { (() => {
/** pyRevit forms.alert — TaskDialog-style message box. */
function AlertBox({
  title = "pyRevit",
  msg,
  subMsg,
  expanded,
  footer,
  warnIcon = false,
  buttons = ["OK"],
  onClose
}) {
  const [open, setOpen] = React.useState(false);
  const box = {
    width: 460,
    background: "#FFFFFF",
    border: "1px solid #767676",
    fontFamily: "var(--font-ui)",
    boxShadow: "0 4px 18px rgba(0,0,0,.35)"
  };
  const head = {
    background: "#F0F0F0",
    borderBottom: "1px solid #DDDDDD",
    padding: "8px 12px",
    fontSize: 12,
    color: "#003399"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: box
  }, /*#__PURE__*/React.createElement("div", {
    style: head
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 10,
      padding: "14px 16px"
    }
  }, warnIcon ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 22,
      color: "#D9822B",
      lineHeight: 1
    }
  }, "\u26A0") : null, /*#__PURE__*/React.createElement("div", {
    style: {
      whiteSpace: "pre-line",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 15,
      color: "#003399"
    }
  }, msg), subMsg ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "#1E1E1E",
      marginTop: 8
    }
  }, subMsg) : null, expanded && open ? /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: "8px 0 0",
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      color: "#333",
      whiteSpace: "pre-wrap"
    }
  }, expanded) : null)), footer ? /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 16px 10px",
      fontSize: 11,
      color: "#666"
    }
  }, footer) : null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      padding: "8px 12px",
      background: "#F0F0F0",
      borderTop: "1px solid #DDDDDD"
    }
  }, expanded ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "#0563C1",
      cursor: "pointer"
    },
    onClick: () => setOpen(v => !v)
  }, open ? "▴ Hide details" : "▾ Show details") : null, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }), buttons.map(b => /*#__PURE__*/React.createElement("button", {
    key: b,
    onClick: onClose,
    style: {
      minWidth: 88,
      height: 26,
      fontFamily: "var(--font-ui)",
      fontSize: 11,
      background: "#EFEFEF",
      border: "1px solid #ACACAC",
      cursor: "pointer"
    }
  }, b))));
}
window.AlertBox = AlertBox;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/AlertBox.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/BaseRename.jsx
try { (() => {
/** GUI_BaseRename — 350×235, the shared parent window for the rename tools. */
function BaseRename({
  onClose
}) {
  const {
    WindowFrame,
    GroupBorder,
    TextField,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  const [v, setV] = React.useState({
    "Find:": "",
    "Replace:": "",
    "Prefix:": "",
    "Suffix:": ""
  });
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Views: Find and Replace",
    width: 350,
    height: 235,
    footer: true,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "flex-end",
      alignItems: "center",
      flex: 1,
      padding: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      padding: "0 10px",
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--kl-green)",
      fontSize: 13,
      padding: "0 0 4px 2px"
    }
  }, "Renaming Parameters"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      height: 110,
      boxSizing: "border-box",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 10
    }
  }, /*#__PURE__*/React.createElement("div", null, Object.keys(v).map(f => /*#__PURE__*/React.createElement("div", {
    key: f,
    style: {
      display: "flex",
      alignItems: "center",
      margin: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 60,
      color: "var(--kl-white)",
      fontSize: 13
    }
  }, f), /*#__PURE__*/React.createElement(TextField, {
    width: 200,
    tone: "white",
    value: v[f],
    onChange: e => setV(s => ({
      ...s,
      [f]: e.target.value
    }))
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingTop: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "auto",
    style: {
      width: 75,
      height: 25,
      fontSize: 13
    },
    onClick: () => window.alert("Renamed 8 views.")
  }, "Rename")))));
}
window.BaseRename = BaseRename;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/BaseRename.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/CreateFromRooms.jsx
try { (() => {
const ROOM_TYPES = ["Office 3600 x 2400", "Corridor 1800", "Stair Enclosure", "Mechanical Room", "Electrical Closet", "Storage 2400 x 2400"];
function CreateFromRooms({
  onClose
}) {
  const {
    WindowFrame,
    FilterField,
    FieldLabel,
    ListPanel,
    CheckItem,
    Button,
    GroupBorder,
    TextField,
    SeparatorLine
  } = window.KLAToolsDesignSystem_aefd26;
  const [query, setQuery] = React.useState("");
  const [picked, setPicked] = React.useState("Office 3600 x 2400");
  const [offset, setOffset] = React.useState("0");
  const shown = ROOM_TYPES.filter(n => n.toLowerCase().includes(query.toLowerCase()));
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Create From Rooms",
    width: 400,
    height: 460,
    footer: true,
    version: "Version: 1.0",
    onClose: onClose
  }, /*#__PURE__*/React.createElement(FilterField, {
    value: query,
    onChange: e => setQuery(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 10px",
      display: "flex",
      flexDirection: "column",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(FieldLabel, {
    style: {
      padding: "0 0 4px 2px"
    }
  }, "Select Type:"), /*#__PURE__*/React.createElement(ListPanel, {
    height: 150
  }, shown.map(n => /*#__PURE__*/React.createElement(CheckItem, {
    key: n,
    checked: picked === n,
    onChange: () => setPicked(n)
  }, n))), /*#__PURE__*/React.createElement(SeparatorLine, {
    style: {
      margin: "20px 5px 5px"
    }
  }), /*#__PURE__*/React.createElement(GroupBorder, {
    label: "Additional Settings:",
    style: {
      padding: "10px 12px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 130,
      color: "var(--kl-white)",
      fontSize: 13
    }
  }, "Offset from level (cm):"), /*#__PURE__*/React.createElement(TextField, {
    width: 200,
    value: offset,
    onChange: e => setOffset(e.target.value.replace(/[^0-9.-]/g, ""))
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      padding: "10px 0"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "lg",
    onClick: () => window.alert("Created 12 elements from rooms at " + (offset || 0) + " cm offset.")
  }, "Create"))));
}
window.CreateFromRooms = CreateFromRooms;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/CreateFromRooms.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/CustomAlert.jsx
try { (() => {
function CustomAlert({
  onClose,
  warning = true
}) {
  const {
    WindowFrame,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  const kind = warning ? {
    glyph: "!",
    color: "var(--kl-warning-gold)",
    heading: "Warning"
  } : {
    glyph: "i",
    color: "var(--kl-info-green)",
    heading: "Information"
  };
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "KL&A Tools",
    width: 440,
    height: 255,
    bordered: true,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      margin: "20px 24px 10px",
      display: "grid",
      gridTemplateColumns: "48px 1fr",
      alignItems: "start"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 34,
      height: 34,
      boxSizing: "border-box",
      borderRadius: 17,
      border: "2px solid var(--kl-green-dark)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      color: kind.color,
      fontFamily: "var(--font-ui)"
    }
  }, kind.glyph)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 700,
      color: "var(--kl-green)",
      fontFamily: "var(--font-ui)"
    }
  }, kind.heading), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      color: "var(--kl-white)",
      fontSize: 12,
      lineHeight: 1.45,
      fontFamily: "var(--font-ui)"
    }
  }, "Model is not workshared. Open a workshared model before running this tool."))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 55,
      flexShrink: 0,
      background: "var(--kl-charcoal)",
      borderTop: "var(--border-hairline) solid var(--kl-green-dark)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    style: {
      width: 110,
      height: 28,
      fontSize: "var(--text-12)"
    },
    onClick: onClose
  }, "OK")));
}
window.CustomAlert = CustomAlert;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/CustomAlert.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/DuplicateSheets.jsx
try { (() => {
const NAMING = ["ViewName", "SheetNumber", "SheetName"];
const NAMING_FIELDS = ["Find", "Replace", "Prefix", "Suffix"];
const INCLUDE = ["Views", "Legends", "Schedules", "Images", "Lines", "Text", "Clouds", "DWGs", "Symbols", "Dimensions", "Additional revisions"];
const BROWSER_FIELDS = ["Name parameter_1", "Value parameter_1", "Name parameter_2", "Value parameter_2"];

/** Duplicate Sheets — 800×470. Naming, browser organisation, include, options. */
function DuplicateSheets({
  onClose
}) {
  const {
    WindowFrame,
    GroupBorder,
    TextField,
    CheckItem,
    RadioItem,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  const [include, setInclude] = React.useState({
    Views: true,
    Legends: true,
    Schedules: true
  });
  const [reuse, setReuse] = React.useState({
    Legends: true,
    Schedules: false
  });
  const [mode, setMode] = React.useState("Duplicate detailing");
  const label = {
    color: "var(--kl-green)",
    fontSize: 13,
    padding: "0 0 4px 2px"
  };
  const NameCol = ({
    title
  }) => /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      margin: "0 5px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: label
  }, title), NAMING_FIELDS.map(f => /*#__PURE__*/React.createElement("div", {
    key: f,
    style: {
      display: "flex",
      alignItems: "center",
      margin: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 50,
      color: "var(--kl-white)",
      fontSize: 12
    }
  }, f), /*#__PURE__*/React.createElement(TextField, {
    width: 140,
    tone: "white",
    fontSize: "var(--text-12)",
    value: "",
    onChange: () => {}
  }))));
  const BrowserCol = ({
    title
  }) => /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      margin: "0 5px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: label
  }, title), BROWSER_FIELDS.map(f => /*#__PURE__*/React.createElement("div", {
    key: f,
    style: {
      display: "flex",
      alignItems: "center",
      margin: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 125,
      color: "var(--kl-white)",
      fontSize: 12
    }
  }, f), /*#__PURE__*/React.createElement(TextField, {
    width: 110,
    tone: "white",
    fontSize: "var(--text-12)",
    value: "",
    onChange: () => {}
  }))));
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Duplicate Sheets",
    width: 800,
    height: 470,
    footer: true,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "10px 12px",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      overflowY: "auto"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: label
  }, "Naming"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      display: "flex",
      padding: 8
    }
  }, NAMING.map(n => /*#__PURE__*/React.createElement(NameCol, {
    key: n,
    title: n
  })))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: label
  }, "Project Browser"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      display: "flex",
      padding: 8
    }
  }, /*#__PURE__*/React.createElement(BrowserCol, {
    title: "View Browser Organisation"
  }), /*#__PURE__*/React.createElement(BrowserCol, {
    title: "Sheets Browser Organisation"
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: label
  }, "Include Elements"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      padding: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(6, 1fr)",
      rowGap: 2
    }
  }, INCLUDE.map(n => /*#__PURE__*/React.createElement(CheckItem, {
    key: n,
    variant: "system",
    checked: !!include[n],
    onChange: () => setInclude(s => ({
      ...s,
      [n]: !s[n]
    }))
  }, n))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: label
  }, "Use Existing [True] / Duplicate [False]"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      height: 75,
      boxSizing: "border-box",
      padding: 8
    }
  }, ["Legends", "Schedules"].map(n => /*#__PURE__*/React.createElement(CheckItem, {
    key: n,
    variant: "system",
    checked: !!reuse[n],
    onChange: () => setReuse(s => ({
      ...s,
      [n]: !s[n]
    }))
  }, n)))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: label
  }, "View Duplicate Opions"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      height: 75,
      boxSizing: "border-box",
      padding: 8
    }
  }, ["Duplicate", "Duplicate detailing", "Duplicate Dependent"].map(n => /*#__PURE__*/React.createElement(RadioItem, {
    key: n,
    name: "dup-mode",
    checked: mode === n,
    onChange: () => setMode(n)
  }, n))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingTop: 4
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "auto",
    style: {
      width: 200,
      height: 30
    },
    onClick: () => window.alert("Duplicated 6 sheets (" + mode + ").")
  }, "Duplicate selected sheets"))));
}
window.DuplicateSheets = DuplicateSheets;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/DuplicateSheets.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/Feedback.jsx
try { (() => {
/** forms.SelectFromList — SelectFromList.xaml: regex toggle, search, ListView, Check/Uncheck/Toggle All + full-width 32px Select. */
function SelectFromList({
  title = "Select Items",
  items = [],
  onOk
}) {
  const [state, setState] = React.useState(() => Object.fromEntries(items.map(i => [i, false])));
  const [q, setQ] = React.useState("");
  const shown = items.filter(i => i.toLowerCase().includes(q.toLowerCase()));
  const count = Object.values(state).filter(Boolean).length;
  const btn = {
    height: 24,
    fontSize: 11,
    fontFamily: "var(--font-ui)",
    background: "#EFEFEF",
    border: "1px solid #ACACAC",
    cursor: "pointer",
    flex: 1
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 500,
      background: "#FFFFFF",
      border: "1px solid #767676",
      fontFamily: "var(--font-ui)",
      boxShadow: "0 4px 18px rgba(0,0,0,.35)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 28,
      background: "#F0F0F0",
      borderBottom: "1px solid #DDD",
      display: "flex",
      alignItems: "center",
      fontSize: 12,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 10,
      flex: 1
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 12px",
      color: "#666"
    }
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 10,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("button", {
    title: "Toggle regex / substring search",
    style: {
      width: 24,
      height: 24,
      background: "#FFF",
      border: "1px solid #CCCCCC",
      cursor: "pointer",
      fontSize: 11,
      fontFamily: "var(--font-ui)",
      padding: 0
    }
  }, "\u25BCA"), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("input", {
    value: q,
    onChange: e => setQ(e.target.value),
    style: {
      width: "100%",
      boxSizing: "border-box",
      height: 25,
      border: "1px solid #ABADB3",
      fontSize: 12,
      padding: "0 24px 0 5px"
    }
  }), q ? /*#__PURE__*/React.createElement("span", {
    onClick: () => setQ(""),
    style: {
      position: "absolute",
      right: 6,
      top: 4,
      color: "dimgray",
      cursor: "pointer",
      fontSize: 13
    }
  }, "\u2715") : null)), /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid #ABADB3",
      height: 220,
      overflowY: "auto"
    }
  }, shown.map(i => /*#__PURE__*/React.createElement("label", {
    key: i,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 0,
      fontSize: 12,
      color: "#1E1E1E",
      padding: "2px 4px"
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: !!state[i],
    onChange: () => setState(s => ({
      ...s,
      [i]: !s[i]
    })),
    style: {
      margin: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 10
    }
  }, i)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 6,
      marginTop: 10
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: btn,
    onClick: () => setState(Object.fromEntries(items.map(i => [i, true])))
  }, "Check All"), /*#__PURE__*/React.createElement("button", {
    style: btn,
    onClick: () => setState(Object.fromEntries(items.map(i => [i, false])))
  }, "Uncheck All"), /*#__PURE__*/React.createElement("button", {
    style: btn,
    onClick: () => setState(s => Object.fromEntries(items.map(i => [i, !s[i]])))
  }, "Toggle All")), /*#__PURE__*/React.createElement("button", {
    style: {
      width: "100%",
      height: 32,
      marginTop: 10,
      fontSize: 12,
      fontFamily: "var(--font-ui)",
      background: "#EFEFEF",
      border: "1px solid #ACACAC",
      cursor: "pointer"
    },
    onClick: () => onOk && onOk(count)
  }, "Select")));
}
window.SelectFromList = SelectFromList;

/** forms.WarningBar — WarningBar.xaml: pyRevitAccentBrush #F39C12 strip. */
function WarningBar({
  title = "Pick elements"
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#F39C12",
      color: "#000",
      fontFamily: "var(--font-ui)",
      fontSize: 12,
      padding: "6px 12px",
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: .75
    }
  }, "\u2014 press Esc to cancel"));
}
window.WarningBar = WarningBar;

/** pyRevit output window — markdown/print log. */
function OutputWindow({
  lines = []
}) {
  const bar = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    background: "#F0F0F0",
    borderBottom: "1px solid #DDDDDD",
    padding: "6px 10px",
    fontSize: 12,
    fontFamily: "var(--font-ui)"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 560,
      background: "#FFFFFF",
      border: "1px solid #767676",
      boxShadow: "0 4px 18px rgba(0,0,0,.35)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: bar
  }, /*#__PURE__*/React.createElement("span", null, "pyRevit \u2014 Output"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "#666"
    }
  }, "\u2715")), /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      padding: 12,
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      lineHeight: 1.6,
      color: "#1E1E1E",
      whiteSpace: "pre-wrap",
      maxHeight: 260,
      overflowY: "auto"
    }
  }, lines.join("\n")));
}
window.OutputWindow = OutputWindow;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/Feedback.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/FindReplace.jsx
try { (() => {
function Row({
  label,
  value,
  onChange
}) {
  const {
    WindowFrame,
    GroupBorder,
    TextField,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      margin: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: "var(--width-label)",
      color: "var(--kl-white)",
      fontSize: 13
    }
  }, label), /*#__PURE__*/React.createElement(TextField, {
    width: 200,
    tone: "white",
    value: value,
    onChange: onChange
  }));
}
function FindReplace({
  onClose
}) {
  const {
    WindowFrame,
    GroupBorder,
    TextField,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  const [v, setV] = React.useState({
    find: "Level 1",
    replace: "Level 01",
    prefix: "",
    suffix: ""
  });
  const set = k => e => setV(s => ({
    ...s,
    [k]: e.target.value
  }));
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Views: Find and Replace",
    width: 350,
    height: 210,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 10px 10px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      flex: 1,
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      padding: "0 5px",
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--kl-green)",
      fontSize: 13,
      padding: "4px 0"
    }
  }, "ViewName"), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      padding: "10px 12px"
    }
  }, /*#__PURE__*/React.createElement(Row, {
    label: "Find:",
    value: v.find,
    onChange: set("find")
  }), /*#__PURE__*/React.createElement(Row, {
    label: "Replace:",
    value: v.replace,
    onChange: set("replace")
  }), /*#__PURE__*/React.createElement(Row, {
    label: "Prefix:",
    value: v.prefix,
    onChange: set("prefix")
  }), /*#__PURE__*/React.createElement(Row, {
    label: "Suffix:",
    value: v.suffix,
    onChange: set("suffix")
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "auto",
    style: {
      width: 75,
      height: 25,
      fontSize: 13
    },
    onClick: () => window.alert("Renamed 14 views.")
  }, "Rename"))));
}
window.FindReplace = FindReplace;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/FindReplace.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/HostExtras.jsx
try { (() => {
function NativeWin({
  title,
  width,
  children,
  onClose
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      boxShadow: "0 4px 18px rgba(0,0,0,.4)",
      background: "#FFFFFF",
      border: "1px solid #767676",
      fontFamily: "var(--font-ui)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 28,
      background: "#F0F0F0",
      borderBottom: "1px solid #DDD",
      display: "flex",
      alignItems: "center",
      fontSize: 12,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 10,
      flex: 1
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 12px",
      cursor: "pointer"
    },
    onClick: onClose
  }, "\u2715")), children);
}
function ProgressBarWin({
  onClose
}) {
  const [n, setN] = React.useState(12);
  React.useEffect(() => {
    const t = setInterval(() => setN(v => v >= 48 ? 12 : v + 1), 250);
    return () => clearInterval(t);
  }, []);
  return /*#__PURE__*/React.createElement(NativeWin, {
    title: "pyRevit",
    width: 420,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "#1E1E1E",
      marginBottom: 8
    }
  }, "Updating steel weight history \u2014 ", n, " of 48"), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 16,
      background: "#E6E6E6",
      border: "1px solid #BCBCBC"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      width: n / 48 * 100 + "%",
      background: "#F39C12"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "flex-end",
      marginTop: 10
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      height: 24,
      width: 80,
      background: "#EFEFEF",
      border: "1px solid #ACACAC",
      fontSize: 11,
      cursor: "pointer"
    },
    onClick: onClose
  }, "Cancel"))));
}
window.ProgressBarWin = ProgressBarWin;
function BalloonNote() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 340,
      background: "#2B2B2B",
      color: "#EEE",
      fontFamily: "var(--font-ui)",
      boxShadow: "0 6px 20px rgba(0,0,0,.5)",
      padding: "12px 14px",
      borderLeft: "3px solid var(--kl-green)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      marginBottom: 4
    }
  }, "KL&A Tools"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "#CCC"
    }
  }, "Steel weight snapshot saved. 214 members, 96.4 tons."), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "#8FA3A0",
      marginTop: 8,
      fontFamily: "var(--font-mono)"
    }
  }, "forms.show_balloon() \u2014 Windows notification area"));
}
window.BalloonNote = BalloonNote;
function HostPickerCard({
  title,
  calledBy,
  note,
  onClose
}) {
  return /*#__PURE__*/React.createElement(NativeWin, {
    title: title,
    width: 420,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 16,
      fontSize: 12,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 8
    }
  }, note), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      color: "#777"
    }
  }, calledBy), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      padding: "8px 10px",
      background: "#F5F5F5",
      border: "1px dashed #BCBCBC",
      color: "#555",
      fontSize: 11
    }
  }, "Host-supplied OS dialog \u2014 the gallery launches it live; nothing to seed.")));
}
window.HostPickerCard = HostPickerCard;
function DisabledCard({
  title,
  calledBy,
  label,
  onClose
}) {
  return /*#__PURE__*/React.createElement(NativeWin, {
    title: title,
    width: 420,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 16,
      fontSize: 12,
      color: "#666"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 8
    }
  }, "Cataloged but disabled in the UI Gallery."), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      color: "#999"
    }
  }, calledBy), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      padding: "8px 10px",
      background: "#F5F5F5",
      border: "1px solid #E0E0E0",
      fontStyle: "italic",
      fontSize: 11
    }
  }, label)));
}
window.DisabledCard = DisabledCard;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/HostExtras.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/NativeChromeWindows.jsx
try { (() => {
function ViewRangeEditor({
  onClose
}) {
  const start = {
    top: "7' 6\"",
    cut: "4' 0\"",
    bottom: "0' 0\"",
    depth: "-2' 0\""
  };
  const [vals, setVals] = React.useState(start);
  const [warning, setWarning] = React.useState("");
  const rows = [{
    key: "top",
    name: "Top Plane",
    elev: "112' 6\"",
    brush: "#4A7EBB",
    level: "combo",
    lvl: "Level 2"
  }, {
    key: "cut",
    name: "Cut Plane",
    elev: "109' 0\"",
    brush: "#3CB371",
    level: "chip",
    lvl: "Same as Top"
  }, {
    key: "bottom",
    name: "Bottom Plane",
    elev: "105' 0\"",
    brush: "#C0504D",
    level: "combo",
    lvl: "Level 1"
  }, {
    key: "depth",
    name: "View Depth",
    elev: "103' 0\"",
    brush: "#DAA520",
    level: "combo",
    lvl: "Level 1"
  }];
  const cell = {
    display: "flex",
    alignItems: "center",
    padding: "0 5px",
    fontSize: 12,
    color: "var(--kl-white)",
    fontFamily: "var(--font-ui)"
  };
  const nb = {
    height: 30,
    width: 120,
    background: "#EFEFEF",
    border: "1px solid #ACACAC",
    fontFamily: "var(--font-ui)",
    fontSize: 11,
    color: "#333",
    cursor: "pointer"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 720,
      boxShadow: "0 4px 18px rgba(0,0,0,.4)"
    }
  }, /*#__PURE__*/React.createElement(OsTitleBar, {
    title: "View Range Editor",
    onClose: onClose
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--kl-charcoal)",
      padding: 10,
      fontFamily: "var(--font-ui)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--kl-white)",
      minHeight: 40
    }
  }, "Editing view range for: Level 2 \u2014 Structural Framing Plan. Select a plan view in the project browser."), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 1,
      background: "#DDDDDD",
      opacity: .4
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "20px 110px 250px 130px 180px",
      margin: "10px 0"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: "1 / 6",
      display: "grid",
      gridTemplateColumns: "20px 110px 250px 130px 180px",
      background: "#F5F5F5"
    }
  }, /*#__PURE__*/React.createElement("span", null), /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell,
      color: "#111",
      fontWeight: 700,
      height: 26
    }
  }, "Plane"), /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell,
      color: "#111",
      fontWeight: 700
    }
  }, "Elevation (ft-in)"), /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell,
      color: "#111",
      fontWeight: 700
    }
  }, "Offset From Level"), /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell,
      color: "#111",
      fontWeight: 700
    }
  }, "Associated Level")), rows.map(r => /*#__PURE__*/React.createElement(React.Fragment, {
    key: r.key
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      height: 35,
      display: "flex",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 5,
      height: 20,
      borderRadius: 3,
      background: r.brush
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: cell
  }, r.name), /*#__PURE__*/React.createElement("span", {
    style: cell
  }, r.elev), /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell
    }
  }, /*#__PURE__*/React.createElement("input", {
    value: vals[r.key],
    onChange: e => setVals(v => ({
      ...v,
      [r.key]: e.target.value
    })),
    style: {
      width: 100,
      height: 25,
      boxSizing: "border-box",
      textAlign: "right",
      border: "1px solid #ACACAC",
      fontFamily: "var(--font-ui)",
      fontSize: 12,
      padding: "0 4px"
    }
  })), r.level === "chip" ? /*#__PURE__*/React.createElement("span", {
    style: {
      ...cell
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      background: "#E8E8E8",
      color: "#333",
      fontStyle: "italic",
      padding: "5px 8px",
      fontSize: 12,
      textAlign: "center",
      flex: 1
    }
  }, r.lvl)) : /*#__PURE__*/React.createElement("span", {
    style: cell
  }, /*#__PURE__*/React.createElement("select", {
    style: {
      width: "100%",
      height: 25,
      fontFamily: "var(--font-ui)",
      fontSize: 12
    },
    defaultValue: r.lvl
  }, /*#__PURE__*/React.createElement("option", null, "Level 1"), /*#__PURE__*/React.createElement("option", null, "Level 2"), /*#__PURE__*/React.createElement("option", null, "Roof")))))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 1,
      background: "#DDDDDD",
      opacity: .4,
      margin: "10px 0"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      gap: 10,
      margin: "10px 0"
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: nb,
    onClick: () => setWarning("Cut plane must sit between the top and bottom planes.")
  }, "Apply Changes"), /*#__PURE__*/React.createElement("button", {
    style: {
      ...nb,
      width: 130
    },
    onClick: () => {
      setVals(start);
      setWarning("");
    }
  }, "Reset to Original")), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      color: "#FF0000",
      fontSize: 11,
      minHeight: 16
    }
  }, warning)));
}
window.ViewRangeEditor = ViewRangeEditor;
function UIGallery({
  onClose
}) {
  const ROWS = [["KL&A custom", "KL&A list selection", "lib/GUI/SelectFromDict.xaml", "Carbon GWP Pull; Concrete Mix Header; …", "Seeded", "Reference list-selection chrome"], ["KL&A custom", "KL&A alert", "lib/GUI/CustomAlert.xaml", "UI Gallery", "Seeded", "Styled Warning / Information alert"], ["KL&A custom", "Find and replace", "lib/GUI/FindReplace.xaml", "UI Gallery", "Seeded", "Compact rename form"], ["KL&A custom", "Duplicate sheets", "lib/GUI/DuplicateSheets.xaml", "duplicate_sheets", "Seeded", "Large command form"], ["DevSandbox", "Steel PSF story selection", "…/Steel PSF.pushbutton/SteelPsfDialog.xaml", "Steel PSF", "Seeded", "SelectFromDict-style prototype"], ["pyRevit", "forms.alert", "(host platform)", "many", "Disabled", "Standard pyRevit dialog — external reference"]];
  const [sel, setSel] = React.useState(1);
  const [q, setQ] = React.useState("");
  const shown = ROWS.filter(r => r.join(" ").toLowerCase().includes(q.toLowerCase()));
  const nb = {
    height: 26,
    background: "#EFEFEF",
    border: "1px solid #ACACAC",
    fontFamily: "var(--font-ui)",
    fontSize: 11,
    color: "#333",
    cursor: "pointer"
  };
  const th = {
    padding: "4px 6px",
    background: "#F0F0F0",
    borderRight: "1px solid #D4D4D4",
    borderBottom: "1px solid #ACACAC",
    fontWeight: 600,
    textAlign: "left",
    whiteSpace: "nowrap"
  };
  const td = {
    padding: "3px 6px",
    borderRight: "1px solid #E4E4E4",
    borderBottom: "1px solid #EEE",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    maxWidth: 250
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 900,
      boxShadow: "0 4px 18px rgba(0,0,0,.4)"
    }
  }, /*#__PURE__*/React.createElement(OsTitleBar, {
    title: "DevSandbox UI Gallery",
    onClose: onClose
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--kl-charcoal)",
      padding: 12,
      fontFamily: "var(--font-ui)",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      height: 460,
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--kl-white)"
    }
  }, "Open KL&A dialogs and repo-used pyRevit form patterns. Seeded previews use fictional data; host/model-dependent forms are cataloged but disabled. Gallery previews never modify the Revit document."), /*#__PURE__*/React.createElement("input", {
    value: q,
    onChange: e => setQ(e.target.value),
    placeholder: "Filter by dialog family, title, or description",
    style: {
      height: 25,
      boxSizing: "border-box",
      border: "1px solid #ACACAC",
      fontFamily: "var(--font-ui)",
      fontSize: 12,
      padding: "0 6px"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: "auto",
      background: "#FFFFFF",
      fontSize: 11,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      borderCollapse: "collapse",
      width: "100%"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Family", "Window", "Relative Path", "Called By", "Data", "Description"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: th
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, shown.map((r, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      background: i === sel ? "#CDE3F7" : "#fff",
      cursor: "pointer"
    },
    onClick: () => setSel(i)
  }, r.map((c, j) => /*#__PURE__*/React.createElement("td", {
    key: j,
    style: td
  }, c))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "flex-end",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      ...nb,
      width: 155
    }
  }, "Open Selected Window"), /*#__PURE__*/React.createElement("button", {
    style: {
      ...nb,
      width: 80
    },
    onClick: onClose
  }, "Close"))));
}
window.UIGallery = UIGallery;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/NativeChromeWindows.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/Pickers.jsx
try { (() => {
/** forms.CommandSwitchWindow — rounded #23303D panel, white chips, #F39C12 accent hover (per CommandSwitchWindow.xaml). */
function CommandSwitch({
  message = "Pick an option",
  options = [],
  onPick
}) {
  const [hover, setHover] = React.useState(null);
  const shell = {
    width: 560,
    background: "#23303D",
    borderRadius: 15,
    fontFamily: "var(--font-ui)",
    color: "#FFFFFF",
    padding: 10,
    boxShadow: "0 0 15px rgba(44,62,80,.25)"
  };
  const chip = on => ({
    padding: "2px 10px",
    height: 20,
    boxSizing: "border-box",
    display: "inline-flex",
    alignItems: "center",
    fontSize: 12,
    borderRadius: 10,
    cursor: "pointer",
    background: on ? "#F39C12" : "#FFFFFF",
    color: on ? "#FFFFFF" : "#23303D",
    margin: "0 5px 5px 0"
  });
  return /*#__PURE__*/React.createElement("div", {
    style: shell
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      height: 36,
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      color: "#FFF",
      whiteSpace: "nowrap"
    }
  }, message), /*#__PURE__*/React.createElement("input", {
    placeholder: "search",
    style: {
      flex: 1,
      boxSizing: "border-box",
      height: 22,
      background: "transparent",
      border: "1px solid rgba(255,255,255,.4)",
      borderRadius: 10,
      color: "#FFF",
      padding: "0 8px",
      fontSize: 12,
      outline: "none"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 5,
      display: "flex",
      flexWrap: "wrap"
    }
  }, options.map(o => /*#__PURE__*/React.createElement("span", {
    key: o,
    style: chip(hover === o),
    onMouseEnter: () => setHover(o),
    onMouseLeave: () => setHover(null),
    onClick: () => onPick && onPick(o)
  }, o))));
}
window.CommandSwitch = CommandSwitch;

/** forms.ask_for_string — GetValueWindow.xaml: OS-chromed 400w window, 36px Courier New 24 bold centered input, full-width OK. */
function AskForString({
  title = "User Input",
  prompt = "",
  value = "",
  onChange,
  onSubmit
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 400,
      background: "#FFFFFF",
      border: "1px solid #767676",
      fontFamily: "var(--font-ui)",
      boxShadow: "0 4px 18px rgba(0,0,0,.35)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 28,
      background: "#F0F0F0",
      borderBottom: "1px solid #DDD",
      display: "flex",
      alignItems: "center",
      fontSize: 12,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 10,
      flex: 1
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 12px",
      color: "#666"
    }
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "#000",
      marginBottom: 10
    }
  }, prompt || "Enter String Value:"), /*#__PURE__*/React.createElement("input", {
    value: value,
    onChange: onChange,
    style: {
      width: "100%",
      boxSizing: "border-box",
      height: 36,
      border: "1px solid #ABADB3",
      fontFamily: "'Courier New', monospace",
      fontSize: 24,
      fontWeight: 700,
      textAlign: "center",
      padding: "0 10px"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 10px 10px"
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onSubmit,
    style: {
      width: "100%",
      height: 24,
      fontSize: 11,
      fontFamily: "var(--font-ui)",
      background: "#EFEFEF",
      border: "1px solid #ACACAC",
      cursor: "pointer"
    }
  }, "OK")));
}
window.AskForString = AskForString;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/Pickers.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/ProtoWindows.jsx
try { (() => {
function SteelPsf({
  onClose
}) {
  const {
    WindowFrame,
    TextField,
    FieldLabel,
    ListPanel,
    CheckItem,
    Button,
    SeparatorLine
  } = window.KLAToolsDesignSystem_aefd26;
  const STORIES = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Roof Low", "Roof High", "Penthouse", "Mezzanine"];
  const [q, setQ] = React.useState("");
  const [checked, setChecked] = React.useState({
    "Level 2": true
  });
  const shown = STORIES.filter(n => n.toLowerCase().includes(q.toLowerCase()));
  const setAll = on => setChecked(Object.fromEntries(shown.map(n => [n, on])));
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Steel PSF",
    width: 430,
    height: 610,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: 5,
      padding: "8px 10px 5px 5px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-12)",
      lineHeight: "22px",
      color: "var(--kl-white)",
      fontFamily: "var(--font-ui)",
      padding: "0 5px"
    }
  }, "Search"), /*#__PURE__*/React.createElement(TextField, {
    value: q,
    onChange: e => setQ(e.target.value),
    tone: "white",
    fontSize: "var(--text-14)",
    style: {
      flex: 1,
      borderColor: "var(--kl-green-dark)"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 10px 5px",
      display: "flex",
      flexDirection: "column",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(SeparatorLine, {
    style: {
      margin: "0 0 4px"
    }
  }), /*#__PURE__*/React.createElement(FieldLabel, {
    style: {
      padding: "0 0 4px 2px",
      color: "var(--kl-white)"
    }
  }, "Select stories to review:"), /*#__PURE__*/React.createElement(ListPanel, {
    height: 330
  }, shown.map(n => /*#__PURE__*/React.createElement(CheckItem, {
    key: n,
    checked: !!checked[n],
    onChange: () => setChecked(c => ({
      ...c,
      [n]: !c[n]
    }))
  }, n))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      gap: 10,
      padding: "5px 0 0"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "md",
    onClick: () => setAll(true)
  }, "Select All"), /*#__PURE__*/React.createElement(Button, {
    size: "md",
    onClick: () => setAll(false)
  }, "Select None")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      gap: 10,
      padding: "5px 0"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "md"
  }, "Initialize CSV"), /*#__PURE__*/React.createElement(Button, {
    size: "md"
  }, "Append CSV")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingBottom: 5
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "auto",
    style: {
      width: 230
    },
    onClick: onClose
  }, "Review Selected Stories"))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 25,
      flexShrink: 0,
      background: "var(--kl-charcoal)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "var(--kl-gray-medium)",
      fontSize: "var(--text-12)"
    }
  }, "DevSandbox Prototype"));
}
window.SteelPsf = SteelPsf;
function MatchRecall({
  onClose
}) {
  const {
    WindowFrame
  } = window.KLAToolsDesignSystem_aefd26;
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Match Properties Recall",
    width: 420,
    height: 320,
    bordered: true,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      margin: 10,
      border: "1px solid var(--kl-green-dark)",
      borderRadius: 10,
      padding: 10,
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--kl-green)",
      fontSize: "var(--text-12)",
      fontFamily: "var(--font-ui)",
      marginBottom: 6
    }
  }, "Recalled parameters:"), [["Workset", "S-Framing"], ["Comments", "TYP UNO"], ["Phase Created", "New Construction"], ["Fire Rating", "2 HR"], ["Top Offset", "-0' 6\""]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: "var(--text-12)",
      fontFamily: "var(--font-ui)",
      color: "var(--kl-white)",
      padding: "3px 2px",
      borderBottom: "1px solid rgba(40,96,72,.4)"
    }
  }, /*#__PURE__*/React.createElement("span", null, k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--kl-gray-medium)"
    }
  }, v)))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 25,
      flexShrink: 0,
      background: "var(--kl-charcoal)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "var(--kl-gray-medium)",
      fontSize: "var(--text-12)"
    }
  }, "KLCode"));
}
window.MatchRecall = MatchRecall;
function PreviewFixture({
  onClose
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 360,
      boxShadow: "0 4px 18px rgba(0,0,0,.4)"
    }
  }, /*#__PURE__*/React.createElement(OsTitleBar, {
    title: "UI Gallery Preview Fixture",
    onClose: onClose
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 128,
      background: "var(--kl-charcoal)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--kl-white)",
      fontSize: 12,
      fontFamily: "var(--font-ui)",
      textAlign: "center"
    }
  }, "This is a self-contained, noninteractive preview fixture.")));
}
window.PreviewFixture = PreviewFixture;

/** Default resizable WPF chrome — the drift the repo flags on the un-themed windows. */
function OsTitleBar({
  title,
  onClose
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: 30,
      background: "#F0F0F0",
      borderBottom: "1px solid #D4D4D4",
      display: "flex",
      alignItems: "center",
      fontFamily: "var(--font-ui)",
      fontSize: 12,
      color: "#1E1E1E"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 10,
      flex: 1
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 12px",
      color: "#666"
    }
  }, "\u2014"), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 12px",
      color: "#666"
    }
  }, "\u25A2"), /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "0 14px",
      cursor: "pointer"
    },
    onClick: onClose
  }, "\u2715"));
}
window.OsTitleBar = OsTitleBar;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/ProtoWindows.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/SelectFromDict.jsx
try { (() => {
const DICT_ITEMS = ["W12x26 — Wide Flange", "W16x31 — Wide Flange", "W21x44 — Wide Flange", "HSS6x6x3/8 — Hollow Section", "HSS8x8x1/2 — Hollow Section", "C10x15.3 — Channel", "L4x4x1/4 — Angle", "WT7x15 — Structural Tee", "Pipe 4" + String.fromCharCode(8243) + " Std", "PL 1/2" + String.fromCharCode(8243) + " — Plate", "24" + String.fromCharCode(8243) + " x 24" + String.fromCharCode(8243) + " Conc Column", "W8x10 — Wide Flange"];
function SelectFromDict({
  onClose
}) {
  const {
    WindowFrame,
    FilterField,
    FieldLabel,
    ListPanel,
    CheckItem,
    Button,
    SeparatorLine
  } = window.KLAToolsDesignSystem_aefd26;
  const [query, setQuery] = React.useState("");
  const [checked, setChecked] = React.useState(() => ({
    "W12x26 — Wide Flange": true
  }));
  const shown = DICT_ITEMS.filter(n => n.toLowerCase().includes(query.toLowerCase()));
  const count = Object.values(checked).filter(Boolean).length;
  const setAll = on => setChecked(Object.fromEntries(shown.map(n => [n, on])));
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Select From Dict",
    width: 400,
    height: 550,
    footer: true,
    version: "Version: 1.0",
    onClose: onClose
  }, /*#__PURE__*/React.createElement(FilterField, {
    value: query,
    onChange: e => setQuery(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 10px 5px",
      display: "flex",
      flexDirection: "column",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(SeparatorLine, {
    style: {
      margin: "0 0 4px"
    }
  }), /*#__PURE__*/React.createElement(FieldLabel, {
    style: {
      padding: "0 0 4px 2px",
      color: "var(--kl-white)"
    }
  }, "Select Elements:"), /*#__PURE__*/React.createElement(ListPanel, {
    height: 330
  }, shown.map(n => /*#__PURE__*/React.createElement(CheckItem, {
    key: n,
    checked: !!checked[n],
    onChange: () => setChecked(c => ({
      ...c,
      [n]: !c[n]
    }))
  }, n)), shown.length === 0 ? /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--kl-gray-medium)",
      fontSize: 13,
      padding: 4
    }
  }, "No matches.") : null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      gap: 10,
      padding: "5px 0"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "md",
    onClick: () => setAll(true)
  }, "Select All"), /*#__PURE__*/React.createElement(Button, {
    size: "md",
    onClick: () => setAll(false)
  }, "Select None")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingBottom: 5
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "lg",
    disabled: count === 0,
    onClick: () => window.alert(count + (count === 1 ? " element" : " elements") + " selected.")
  }, "Select"))));
}
window.SelectFromDict = SelectFromDict;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/SelectFromDict.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dialogs/SheetsFindReplace.jsx
try { (() => {
const FIELDS = ["Find:", "Replace:", "Prefix:", "Suffix:"];
function RenameGroup({
  label,
  values,
  onChange,
  labelColor
}) {
  const {
    GroupBorder,
    TextField
  } = window.KLAToolsDesignSystem_aefd26;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      margin: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: labelColor,
      fontSize: 13,
      padding: "0 0 4px 2px"
    }
  }, label), /*#__PURE__*/React.createElement(GroupBorder, {
    style: {
      height: 110,
      boxSizing: "border-box",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 10
    }
  }, /*#__PURE__*/React.createElement("div", null, FIELDS.map(f => /*#__PURE__*/React.createElement("div", {
    key: f,
    style: {
      display: "flex",
      alignItems: "center",
      margin: "2px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 60,
      color: "var(--kl-white)",
      fontSize: 13
    }
  }, f), /*#__PURE__*/React.createElement(TextField, {
    width: 200,
    tone: "white",
    value: values[f] || "",
    onChange: e => onChange(f, e.target.value)
  }))))));
}

/** Sheets: Find and Replace — 620×250, two rename groups side by side. */
function SheetsFindReplace({
  onClose
}) {
  const {
    WindowFrame,
    Button
  } = window.KLAToolsDesignSystem_aefd26;
  const [num, setNum] = React.useState({
    "Find:": "A-",
    "Replace:": "S-"
  });
  const [name, setName] = React.useState({});
  return /*#__PURE__*/React.createElement(WindowFrame, {
    title: "Sheets: Find and Replace",
    width: 620,
    height: 250,
    footer: true,
    onClose: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingTop: 30
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex"
    }
  }, /*#__PURE__*/React.createElement(RenameGroup, {
    label: "SheetNumber",
    values: num,
    onChange: (k, v) => setNum(s => ({
      ...s,
      [k]: v
    })),
    labelColor: "var(--kl-green)"
  }), /*#__PURE__*/React.createElement(RenameGroup, {
    label: "SheetName",
    values: name,
    onChange: (k, v) => setName(s => ({
      ...s,
      [k]: v
    })),
    labelColor: "var(--kl-green)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center",
      paddingTop: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "auto",
    style: {
      width: 150,
      height: 25,
      fontSize: 13
    },
    onClick: () => window.alert("Renamed 22 sheets.")
  }, "Rename")))));
}
window.SheetsFindReplace = SheetsFindReplace;
window.RenameGroup = RenameGroup;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dialogs/SheetsFindReplace.jsx", error: String((e && e.message) || e) }); }

// ui_kits/ribbon/AlertDialog.jsx
try { (() => {
/** pyRevit `forms.alert` — native TaskDialog-style message box. */
function NativeButton({
  children,
  onClick,
  style
}) {
  const [hover, setHover] = React.useState(false);
  const btn = {
    height: 28,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "0 8px",
    fontFamily: "var(--font-ui)",
    fontSize: 11,
    color: "#333333",
    background: hover ? "#DCECFC" : "#EFEFEF",
    border: "1px solid " + (hover ? "#3C7FB1" : "#ACACAC"),
    cursor: "pointer",
    ...style
  };
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    style: btn,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, children);
}
function AlertDialog({
  title,
  body,
  onClose
}) {
  const back = {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,.25)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 50
  };
  const box = {
    width: 460,
    background: "#FFFFFF",
    border: "1px solid #767676",
    fontFamily: "var(--font-ui)",
    boxShadow: "0 4px 18px rgba(0,0,0,.35)"
  };
  const head = {
    background: "#F0F0F0",
    borderBottom: "1px solid #DDDDDD",
    padding: "8px 12px",
    fontSize: 12,
    color: "#003399"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: back,
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    style: box,
    onClick: e => e.stopPropagation()
  }, /*#__PURE__*/React.createElement("div", {
    style: head
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "14px 16px",
      fontSize: 12,
      color: "#1E1E1E",
      whiteSpace: "pre-line",
      lineHeight: 1.5
    }
  }, body), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "flex-end",
      gap: 6,
      padding: "10px 12px",
      background: "#F0F0F0",
      borderTop: "1px solid #DDDDDD"
    }
  }, /*#__PURE__*/React.createElement(NativeButton, {
    onClick: onClose,
    style: {
      minWidth: 80
    }
  }, "OK"))));
}
Object.assign(__ds_scope, { AlertDialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/ribbon/AlertDialog.jsx", error: String((e && e.message) || e) }); }

// ui_kits/ribbon/RibbonButton.jsx
try { (() => {
/** Ribbon pushbutton: 32px icon over a wrapped label. Large or small. */
function RibbonButton({
  label,
  icon,
  size = "large",
  dropdown = false,
  active = false,
  tooltip,
  onClick
}) {
  const [hover, setHover] = React.useState(false);
  const large = size === "large";
  const btn = {
    display: "flex",
    flexDirection: large ? "column" : "row",
    alignItems: "center",
    justifyContent: large ? "flex-start" : "flex-start",
    gap: large ? 4 : 6,
    width: large ? 74 : "auto",
    minHeight: large ? 78 : 22,
    padding: large ? "6px 2px 4px" : "2px 6px 2px 2px",
    background: active ? "#CDE3F7" : hover ? "#DCECFC" : "transparent",
    border: "var(--border-hairline) solid " + (hover || active ? "#7DA2CE" : "transparent"),
    cursor: "pointer",
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-11)",
    color: "#1E1E1E",
    textAlign: "center"
  };
  const img = {
    width: large ? "var(--icon-ribbon)" : 16,
    height: large ? "var(--icon-ribbon)" : 16,
    objectFit: "contain"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: btn,
    title: tooltip,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, icon ? /*#__PURE__*/React.createElement("img", {
    src: icon,
    alt: "",
    style: img
  }) : null, /*#__PURE__*/React.createElement("span", {
    style: {
      lineHeight: 1.15,
      whiteSpace: "pre-line"
    }
  }, label, dropdown ? " ▾" : ""));
}
Object.assign(__ds_scope, { RibbonButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/ribbon/RibbonButton.jsx", error: String((e && e.message) || e) }); }

// ui_kits/ribbon/RibbonPanel.jsx
try { (() => {
/** Ribbon panel: button row above a centred panel title, divider on the right. */
function RibbonPanel({
  title,
  children
}) {
  const panel = {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: 96,
    padding: "2px 6px 0",
    borderRight: "var(--border-hairline) solid #D4D4D4",
    background: "transparent"
  };
  const row = {
    display: "flex",
    alignItems: "flex-start",
    gap: 2,
    flex: 1
  };
  const cap = {
    textAlign: "center",
    fontFamily: "var(--font-ui)",
    fontSize: "var(--text-11)",
    color: "#4D4D4D",
    padding: "2px 0 3px"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: panel
  }, /*#__PURE__*/React.createElement("div", {
    style: row
  }, children), /*#__PURE__*/React.createElement("div", {
    style: cap
  }, title));
}
Object.assign(__ds_scope, { RibbonPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/ribbon/RibbonPanel.jsx", error: String((e && e.message) || e) }); }

// ui_kits/ribbon/RibbonStack.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Three small buttons stacked vertically inside one ribbon slot. */
function RibbonStack({
  items = []
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 1,
      paddingTop: 4
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement(__ds_scope.RibbonButton, _extends({
    key: it.label + i,
    size: "small"
  }, it))));
}
Object.assign(__ds_scope, { RibbonStack });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/ribbon/RibbonStack.jsx", error: String((e && e.message) || e) }); }

// ui_kits/ribbon/RibbonTab.jsx
try { (() => {
const ICON = n => "../../assets/icons/bundles/" + n + ".png";
const PROTO = "../../assets/icons/lib/drill_96px_orange.png";
const PULLDOWNS = {
  "Rename": [{
    label: "FindReplace - Views",
    icon: ICON("findreplace-views")
  }, {
    label: "FindReplace_Sheets",
    icon: ICON("findreplace-sheets")
  }],
  "Revision": [{
    label: "Find All Revised Sheets",
    icon: ICON("find-revised-sheets")
  }, {
    label: "Find All Revision Clouds On Views",
    icon: ICON("find-revision-clouds")
  }, {
    sep: true
  }, {
    label: "Set Revision On Sheets",
    icon: ICON("set-revision")
  }, {
    label: "Remove Revision From Sheets",
    icon: ICON("remove-revision")
  }, {
    label: "Turn Off All Revisions",
    icon: ICON("turn-off-revisions")
  }],
  "Prototypes": ["Carbon GWP Pull", "Steel PSF", "Highlight Changed Elements", "Create Detail Folders", "Element Takeoff", "Launch Dynamo Script", "FindReplace - Views-proto", "FindReplace_Sheets-proto", "Open Keynote File", "Hide Revision Clouds", "Concrete Mix Header", "Inspect Schedule Header", "UI Gallery"].map(l => ({
    label: l,
    icon: PROTO
  }))
};
function RibbonTab() {
  const {
    RibbonPanel,
    RibbonButton,
    AlertDialog
  } = window.KLAToolsDesignSystem_aefd26;
  const [openMenu, setOpenMenu] = React.useState(null);
  const [alert, setAlert] = React.useState(null);
  const [notesHidden, setNotesHidden] = React.useState(true);
  const [override2d, setOverride2d] = React.useState(false);
  const tabStrip = {
    display: "flex",
    alignItems: "flex-end",
    gap: 2,
    background: "#2B2B2B",
    padding: "6px 10px 0",
    fontSize: 12,
    color: "#D6D6D6"
  };
  const tab = on => ({
    padding: "5px 12px",
    background: on ? "#F0F0F0" : "transparent",
    color: on ? "#1E1E1E" : "#D6D6D6",
    cursor: "pointer"
  });
  const menu = {
    position: "absolute",
    top: "100%",
    left: 0,
    zIndex: 20,
    background: "#F0F0F0",
    border: "1px solid #ACACAC",
    minWidth: 250,
    padding: "2px 0",
    boxShadow: "0 2px 6px rgba(0,0,0,.3)"
  };
  const item = {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "4px 10px",
    fontSize: 12,
    color: "#1E1E1E",
    cursor: "pointer"
  };
  const Pull = ({
    name,
    icon,
    tooltip
  }) => /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    },
    onMouseLeave: () => setOpenMenu(null)
  }, /*#__PURE__*/React.createElement(RibbonButton, {
    label: name,
    icon: icon,
    dropdown: true,
    tooltip: tooltip,
    onClick: () => setOpenMenu(openMenu === name ? null : name)
  }), openMenu === name ? /*#__PURE__*/React.createElement("div", {
    style: menu
  }, PULLDOWNS[name].map((b, i) => b.sep ? /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      height: 1,
      background: "#D4D4D4",
      margin: "2px 6px"
    }
  }) : /*#__PURE__*/React.createElement("div", {
    key: b.label,
    style: item,
    onClick: () => {
      setOpenMenu(null);
      setAlert({
        title: b.label,
        body: b.label + " ran on the active document."
      });
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: b.icon,
    alt: "",
    style: {
      width: 16,
      height: 16,
      objectFit: "contain"
    }
  }), b.label))) : null);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: tabStrip
  }, /*#__PURE__*/React.createElement("div", {
    style: tab(false)
  }, "Structure"), /*#__PURE__*/React.createElement("div", {
    style: tab(false)
  }, "Annotate"), /*#__PURE__*/React.createElement("div", {
    style: tab(false)
  }, "View"), /*#__PURE__*/React.createElement("div", {
    style: tab(false)
  }, "pyRevit"), /*#__PURE__*/React.createElement("div", {
    style: tab(true)
  }, "KL&A Tools_dev")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      background: "#F0F0F0",
      borderBottom: "1px solid #D4D4D4",
      padding: "4px 0",
      alignItems: "stretch"
    }
  }, /*#__PURE__*/React.createElement(RibbonPanel, {
    title: "KL&A Resources"
  }, /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Gen Notes\nTYP DTLS",
    icon: ICON("gen-notes"),
    tooltip: "Launches KL&A's General Notes, Typical Details and Graphic Style Guide Bluebeam Studio Session.",
    onClick: () => setAlert({
      title: "Gen Notes TYP DTLS",
      body: "Opening the Bluebeam Studio Session…"
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "RVT Stds\nOnenote",
    icon: ICON("rvt-stds"),
    tooltip: "Launches KL&A's Revit Onenote.",
    onClick: () => setAlert({
      title: "RVT Stds Onenote",
      body: "Opening the KL&A Revit Onenote…"
    })
  })), /*#__PURE__*/React.createElement(RibbonPanel, {
    title: "KL&A Tools"
  }, /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Hide/Unhide\nEng Notes",
    icon: ICON(notesHidden ? "hide-notes-on" : "hide-notes-off"),
    active: notesHidden,
    tooltip: "Changes Engineering Note Visibility on Sheet",
    onClick: () => setNotesHidden(v => !v)
  })), /*#__PURE__*/React.createElement(RibbonPanel, {
    title: "Core Tools"
  }, /*#__PURE__*/React.createElement(Pull, {
    name: "Rename",
    icon: ICON("rename"),
    tooltip: "Find and replace on view and sheet names"
  }), /*#__PURE__*/React.createElement(Pull, {
    name: "Revision",
    icon: ICON("revision"),
    tooltip: "Set, remove and audit revisions across sheets"
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Highlight 2D",
    icon: ICON(override2d ? "override2d-on" : "override2d-off"),
    active: override2d,
    tooltip: "Higlight 2D elements in red",
    onClick: () => setOverride2d(v => !v)
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "duplicate_sheets",
    icon: ICON("duplicate-sheets"),
    tooltip: "Duplicate selected sheets with their views",
    onClick: () => setAlert({
      title: "Duplicate Sheets",
      body: "Select the sheets to duplicate."
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Show View Range",
    icon: ICON("view-range"),
    tooltip: "Tool to illustrate the view range of plan views in a 3D view using colored planes. Open a 3D view and select the plan views to illustrate in the project browser.",
    onClick: () => setAlert({
      title: "Show View Range",
      body: "Open a 3D view first."
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Copy legends\nto others documents",
    icon: ICON("copy-legends"),
    tooltip: "Copy legends to others documents",
    onClick: () => setAlert({
      title: "Copy Legends",
      body: "No Legend Views selected."
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Who did that??",
    icon: ICON("who-did-that"),
    tooltip: "Figure out who made specific changes in the model.",
    onClick: () => setAlert({
      title: "Who did that??",
      body: "Creator: jsmith\nLast Changed By: alee\nOwner: <none>"
    })
  })), /*#__PURE__*/React.createElement(RibbonPanel, {
    title: "Outreach/Feedback"
  }, /*#__PURE__*/React.createElement(RibbonButton, {
    label: "About\nKL&A Tools",
    icon: ICON("about"),
    tooltip: "Shows the loaded KL&A Tools extension version, build metadata, and extension path.",
    onClick: () => setAlert({
      title: "About KL&A Tools",
      body: "Extension: KL&A Tools\nVersion: 0.0.0.beta\nChannel: stable\npyRevit Version: 5.0.1\nRevit Version: Autodesk Revit 2024"
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Suggestions/Bugs\nFeedback",
    icon: ICON("suggestions"),
    tooltip: "Opens the KL&A feedback form for bug reporting, tool suggestions, or general feedback.",
    onClick: () => setAlert({
      title: "Feedback subject",
      body: "Add a short subject for the form subject line."
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Prototype\nRequest",
    icon: ICON("prototype-request"),
    tooltip: "Opens the KL&A prototype form.",
    onClick: () => setAlert({
      title: "Prototype Request",
      body: "Opening the KL&A prototype form…"
    })
  })), /*#__PURE__*/React.createElement(RibbonPanel, {
    title: "Dev-Sandbox"
  }, /*#__PURE__*/React.createElement(Pull, {
    name: "Prototypes",
    icon: ICON("prototypes"),
    tooltip: "Development prototypes for evaluation in DevSandbox."
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "Launch\nDyn Player",
    icon: ICON("dyn-player"),
    tooltip: "Prototype: opens Dynamo Player. Supports Revit 2021's Playlist command and Revit 2022 or later's Dynamo Player command.",
    onClick: () => setAlert({
      title: "Launch Dyn Player",
      body: "Open a Revit model or family first."
    })
  }), /*#__PURE__*/React.createElement(RibbonButton, {
    label: "URL Button",
    icon: ICON("trial"),
    tooltip: "URL Button",
    onClick: () => setAlert({
      title: "URL Button",
      body: "Opens https://forms.cloud.microsoft/r/HjuggSZqyU"
    })
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 190,
      background: "linear-gradient(#7E8B99,#5C6873)"
    }
  }), alert ? /*#__PURE__*/React.createElement(AlertDialog, {
    title: alert.title,
    body: alert.body,
    onClose: () => setAlert(null)
  }) : null);
}
Object.assign(__ds_scope, { RibbonTab });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/ribbon/RibbonTab.jsx", error: String((e && e.message) || e) }); }

__ds_ns.WindowFooter = __ds_scope.WindowFooter;

__ds_ns.WindowFrame = __ds_scope.WindowFrame;

__ds_ns.WindowHeader = __ds_scope.WindowHeader;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.CheckItem = __ds_scope.CheckItem;

__ds_ns.FieldLabel = __ds_scope.FieldLabel;

__ds_ns.FilterField = __ds_scope.FilterField;

__ds_ns.GroupBorder = __ds_scope.GroupBorder;

__ds_ns.ListPanel = __ds_scope.ListPanel;

__ds_ns.RadioItem = __ds_scope.RadioItem;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.SeparatorLine = __ds_scope.SeparatorLine;

__ds_ns.TextField = __ds_scope.TextField;

__ds_ns.AlertDialog = __ds_scope.AlertDialog;

__ds_ns.RibbonButton = __ds_scope.RibbonButton;

__ds_ns.RibbonPanel = __ds_scope.RibbonPanel;

__ds_ns.RibbonStack = __ds_scope.RibbonStack;

__ds_ns.RibbonTab = __ds_scope.RibbonTab;

})();
