# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms, script

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def get_element_length_ft(element):
    """
    Return the length of *element* in internal Revit units (decimal feet),
    or None if the element has no usable length parameter.

    Priority order:
      1. Built-in CURVE_ELEM_LENGTH  (framing, walls, MEP runs …)
      2. Built-in CURVE_ELEM_LENGTH on the host (shouldn't be needed often)
    """
    param = element.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH)
    if param and param.HasValue and param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    return None


def ft_to_str(decimal_feet):
    """Format a decimal-feet value as  X'-Y  Y/Z\"  (feet-inches-fractions)."""
    total_inches = decimal_feet * 12.0
    feet = int(total_inches // 12)
    inches = total_inches - feet * 12

    # Round to nearest 1/16"
    sixteenths = round(inches * 16)
    whole_inches = sixteenths // 16
    remainder = sixteenths % 16

    feet += whole_inches // 12
    whole_inches = whole_inches % 12

    if remainder == 0:
        frac_str = ""
    else:
        # Reduce fraction
        from math import gcd
        g = gcd(remainder, 16)
        frac_str = ' {}/{}"'.format(remainder // g, 16 // g)

    if feet and whole_inches:
        return "{}'- {}{}".format(feet, whole_inches, frac_str)
    elif feet:
        return "{}'- 0{}".format(feet, frac_str)
    else:
        return '0\'- {}{}'.format(whole_inches, frac_str)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

output = script.get_output()
logger = script.get_logger()

#Prompt user to pick elements
with revit.ErrorSwallower():
    try:
        picked_refs = revit.pick_elements(
            message="Select elements to measure — press Finish or Escape when done"
        )
    except Exception:
        picked_refs = None

if not picked_refs:
    forms.alert(
        "No elements were selected.",
        title="Selection Length Reporter",
        warn_icon=True,
    )
    script.exit()

# Resolve element references
doc = revit.doc
elements = [doc.GetElement(ref) for ref in picked_refs if ref is not None]
elements = [e for e in elements if e is not None]

count = len(elements)
if count == 0:
    forms.alert(
        "Could not resolve any elements from the selection.",
        title="Selection Length Reporter",
        warn_icon=True,
    )
    script.exit()

# append lengths and filter out elements without length parameter
total_ft = 0.0
no_length = []   # (id, category) for elements without a length param

for elem in elements:
    length = get_element_length_ft(elem)
    if length is not None:
        total_ft += length
    else:
        cat_name = elem.Category.Name if elem.Category else "Unknown"
        no_length.append((elem.Id.IntegerValue, cat_name))

#print output
output.print_md("# Selection Length Report")
output.print_md("---")
output.print_md("**Elements selected:** {}".format(count))

if total_ft > 0:
    # Feet-inches display
    fi_str = ft_to_str(total_ft)
    output.print_md(
        "**Total cumulative length:** {}  *(= {:.0f} mm / {:.3f} m)*".format(fi_str)
    )
else:
    output.print_md("no length parameters found")

if no_length:
    output.print_md("\n### Elements with no length parameter ({})".format(len(no_length)))
    output.print_md(
        "These elements were counted but excluded from the length total:"
    )
    #group by category for readability
    from collections import defaultdict
    by_cat = defaultdict(list)
    for eid, cat in no_length:
        by_cat[cat].append(eid)
    for cat, ids in sorted(by_cat.items()):
        output.print_md(
            "- **{}** — {} element(s)".format(cat, len(ids))
        )

output.print_md("\n---\n*Lengths read from the CURVE\\_ELEM\\_LENGTH built-in parameter.*")
