# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms, script
from collections import defaultdict

# ---------------------------------------------------------------------------
# functions
# ---------------------------------------------------------------------------

def _gcd(a, b):
    """Euclidean GCD — IronPython 2.7 does not expose math.gcd."""
    while b:
        a, b = b, a % b
    return a


def get_element_length_ft(element):
    """
    Return the length of *element* in internal Revit units (decimal feet),
    or None if the element has no usable length parameter.
    """
    param = element.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH)
    if param and param.HasValue and param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    return None


def ft_to_str(decimal_feet):
    """Format a decimal-feet value as  X'- Y Y/Z\"  (feet-inches-fractions)."""
    total_inches = decimal_feet * 12.0
    feet = int(total_inches // 12)
    inches = total_inches - feet * 12

    # Round to nearest 1/16"
    sixteenths = int(round(inches * 16))
    whole_inches = sixteenths // 16
    remainder = sixteenths % 16

    feet += whole_inches // 12
    whole_inches = whole_inches % 12

    if remainder == 0:
        frac_str = ""
    else:
        g = _gcd(remainder, 16)
        frac_str = ' {}/{}"'.format(remainder // g, 16 // g)

    if feet and whole_inches:
        return "{}'- {}{}".format(feet, whole_inches, frac_str)
    elif feet:
        return "{}'- 0{}".format(feet, frac_str)
    else:
        return "0'- {}{}".format(whole_inches, frac_str)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

output = script.get_output()

# Element selection prompt
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

# revit.pick_elements() returns Element objects directly
elements = [e for e in picked_refs if e is not None]

count = len(elements)
if count == 0:
    forms.alert(
        "Could not resolve any elements from the selection.",
        title="Selection Length Reporter",
        warn_icon=True,
    )
    script.exit()

# Accumulate lengths; track elements with no length parameter
total_ft = 0.0
no_length = []

for elem in elements:
    length = get_element_length_ft(elem)
    if length is not None:
        total_ft += length
    else:
        cat_name = elem.Category.Name if elem.Category else "Unknown"
        no_length.append((elem.Id.IntegerValue, cat_name))

# Print output
output.print_md("# Selection Length Report")
output.print_md("---")
output.print_md("**Elements selected:** {}".format(count))

if total_ft > 0:
    output.print_md("**Total cumulative length:** {}".format(ft_to_str(total_ft)))
else:
    output.print_md("**Total cumulative length:** N/A *(no length parameters found)*")

if no_length:
    output.print_md("\n### Elements with no length parameter ({})".format(len(no_length)))
    output.print_md("These elements were counted but excluded from the length total:")
    by_cat = defaultdict(list)
    for eid, cat in no_length:
        by_cat[cat].append(eid)
    for cat, ids in sorted(by_cat.items()):
        output.print_md("- **{}** — {} element(s)".format(cat, len(ids)))

output.print_md("\n---\n*Lengths read from the CURVE\\_ELEM\\_LENGTH built-in parameter.*")