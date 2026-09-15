# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms, script
from collections import defaultdict

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def _gcd(a, b):
    """Euclidean GCD — IronPython 2.7 does not expose math.gcd."""
    while b:
        a, b = b, a % b
    return a


def get_element_length_ft(element):
    """Return length in decimal feet, or None if not available."""
    param = element.get_Parameter(DB.BuiltInParameter.CURVE_ELEM_LENGTH)
    if param and param.HasValue and param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    return None


def get_element_volume_cf(element):
    """Return volume in decimal cubic feet, or None if not available."""
    param = element.get_Parameter(DB.BuiltInParameter.HOST_VOLUME_COMPUTED)
    if param and param.HasValue and param.StorageType == DB.StorageType.Double:
        return param.AsDouble()
    return None


def ft_to_str(decimal_feet):
    """Format decimal feet as  X'- Y Y/Z\" """
    total_inches = decimal_feet * 12.0
    feet = int(total_inches // 12)
    inches = total_inches - feet * 12

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


def cf_to_cy(cubic_feet):
    """Convert cubic feet to cubic yards."""
    return cubic_feet / 27.0


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
        title="Element Takeoff",
        warn_icon=True,
    )
    script.exit()

elements = [e for e in picked_refs if e is not None]

count = len(elements)
if count == 0:
    forms.alert(
        "Could not resolve any elements from the selection.",
        title="Element Takeoff",
        warn_icon=True,
    )
    script.exit()

# ---------------------------------------------------------------------------
# Accumulate lengths
# ---------------------------------------------------------------------------
total_ft = 0.0
no_length = []

for elem in elements:
    length = get_element_length_ft(elem)
    if length is not None:
        total_ft += length
    else:
        cat_name = elem.Category.Name if elem.Category else "Unknown"
        no_length.append((elem.Id.IntegerValue, cat_name))

# ---------------------------------------------------------------------------
# Accumulate volumes
# ---------------------------------------------------------------------------
total_cf = 0.0
has_volume = []   # (category_name, element_id_int) for elements that contributed
no_volume  = []   # (element_id_int, category_name) for elements without volume

for elem in elements:
    volume = get_element_volume_cf(elem)
    if volume is not None:
        total_cf += volume
        cat_name = elem.Category.Name if elem.Category else "Unknown"
        has_volume.append((cat_name, elem.Id.IntegerValue))
    else:
        cat_name = elem.Category.Name if elem.Category else "Unknown"
        no_volume.append((elem.Id.IntegerValue, cat_name))

# ---------------------------------------------------------------------------
# Print output
# ---------------------------------------------------------------------------
output.print_md("# Element Takeoff")
output.print_md("---")
output.print_md("**Elements selected:** {}".format(count))

# --- Length section ---
output.print_md("\n## Length")
if total_ft > 0:
    output.print_md("**Total cumulative length:** {}".format(ft_to_str(total_ft)))
else:
    output.print_md("**Total cumulative length:** N/A *(no length parameters found)*")

if no_length:
    output.print_md("\n*Elements excluded from length ({}) — no length parameter:*".format(len(no_length)))
    by_cat = defaultdict(list)
    for eid, cat in no_length:
        by_cat[cat].append(eid)
    for cat, ids in sorted(by_cat.items()):
        output.print_md("- **{}** — {} element(s)".format(cat, len(ids)))

# --- Volume section ---
output.print_md("\n## Volume")
if total_cf > 0:
    total_cy = cf_to_cy(total_cf)
    output.print_md("**Elements contributing to volume:** {}".format(len(has_volume)))
    output.print_md("**Total cumulative volume:** {:.2f} CF  /  {:.2f} CY".format(total_cf, total_cy))

    # List contributing elements grouped by category
    by_cat_vol = defaultdict(list)
    for cat, eid in has_volume:
        by_cat_vol[cat].append(eid)
    output.print_md("\n*Contributing elements by category:*")
    for cat, ids in sorted(by_cat_vol.items()):
        output.print_md("- **{}** — {} element(s)".format(cat, len(ids)))
else:
    output.print_md("**Total cumulative volume:** N/A *(no volume parameters found)*")

if no_volume:
    output.print_md("\n*Elements excluded from volume ({}) — no volume parameter:*".format(len(no_volume)))
    by_cat = defaultdict(list)
    for eid, cat in no_volume:
        by_cat[cat].append(eid)
    for cat, ids in sorted(by_cat.items()):
        output.print_md("- **{}** — {} element(s)".format(cat, len(ids)))

output.print_md("\n---\n*Length: CURVE\\_ELEM\\_LENGTH parameter.  Volume: HOST\\_VOLUME\\_COMPUTED parameter.*")
