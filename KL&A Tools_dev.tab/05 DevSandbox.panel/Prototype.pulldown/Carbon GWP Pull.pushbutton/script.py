# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Carbon GWP Pull"  # Name of the button displayed in Revit
__author__ = "KL&A"
__version__ = 'DevSandbox Prototype'
__doc__ = """Version: DevSandbox Prototype
_____________________________________________________________________
Description:

Export selected Carbon GWP schedules to Excel, read the post-processed
Export worksheet, and write those values to Carbon Pie.JMP family type
parameters in the active Revit model.
_____________________________________________________________________
How-to:

-> Click the button
-> Select exactly three schedules
-> Select the export container workbook
-> Select the post-processing workbook
-> Review the pyRevit output report
_____________________________________________________________________
Prototype limits:
- Requires Microsoft Excel COM interop on the Revit workstation
- Does not run workbook macros directly
- Stops before Revit writes if required schedules, workbooks, or family
  data are missing
_____________________________________________________________________
Author: KL&A"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
# ==================================================================
import os
import sys
import traceback

from pyrevit import DB, forms, revit, script


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
# ==================================================================
COMMAND_TITLE = __title__


def _extension_root(path):
    """Return the pyRevit extension root folder for this script path."""
    # Start from the file path that launched the command.
    # The script can live several folders below the extension root.
    current = os.path.abspath(path)

    # Walk up the folder tree until the pyRevit ".extension" folder is found.
    # If it is not found, fall back to the original absolute path.
    while True:
        if current.lower().endswith('.extension'):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from GUI.forms import select_from_dict
from carbon_gwp.workflow import (
    CARBON_PIE_FAMILY_NAME,
    DEFAULT_EXPORT_CONTAINER_PATH,
    DEFAULT_POST_PROCESSING_PATH,
    DEFAULT_SCHEDULE_NAMES,
    EXPORT_WORKSHEET_NAME,
    normalize_grid,
    parameter_value_pairs_from_export_rows,
    uniquify_worksheet_names,
    validate_parameter_value_pairs,
    worksheet_name_for_schedule,
)


# Compatibility for IronPython and CPython text checks.
try:
    TEXT_TYPES = (unicode,)
except NameError:
    TEXT_TYPES = (str,)


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
# ==================================================================
# General helpers
# ------------------------------------------------------------------
def _element_id_value(element_id):
    """Return a Revit ElementId as an integer when one is available."""
    # Revit versions expose element id values through different properties.
    # Try both known names and ignore failures from unavailable properties.
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _element_name(element, default='Unnamed'):
    """Read a Revit element name with fallbacks for API differences."""
    # Guard against missing elements before calling Revit API accessors.
    # This keeps output labels usable even when a lookup returns None.
    if element is None:
        return default

    # Prefer the Revit API name accessor, then fall back to the direct
    # element.Name property used by some pyRevit/Revit object wrappers.
    try:
        name = DB.Element.Name.GetValue(element)
    except Exception:
        try:
            name = element.Name
        except Exception:
            name = None
    return name or default


def _safe_text(value):
    """Convert Excel and Revit values to report-friendly text."""
    # Treat missing values as blank cells.
    # Excel COM commonly returns None for empty worksheet cells.
    if value is None:
        return ''

    # Return existing text unchanged so labels and parameter names keep
    # their original spelling and spacing.
    if isinstance(value, TEXT_TYPES):
        return value

    # Convert whole-number floats to integer-looking strings.
    # This avoids reporting or writing values like "5.0" when "5" is intended.
    try:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
    except Exception:
        pass

    # Convert the remaining value to text and make one more cleanup pass
    # for numeric strings that came through Excel with a trailing ".0".
    text = str(value)
    if text.endswith('.0'):
        try:
            return str(int(float(text)))
        except Exception:
            pass
    return text


# Revit schedule selection and extraction
# ------------------------------------------------------------------
def _schedule_options(document):
    """Build the schedule selector choices from non-template schedules."""
    # Collect all ViewSchedule elements from the active model.
    # Template and titleblock revision schedules are filtered out below.
    schedules = DB.FilteredElementCollector(document).OfClass(DB.ViewSchedule)
    options = {}

    # Build a display-name-to-schedule dictionary for the selection UI.
    # Duplicate schedule names get an ElementId suffix to keep labels unique.
    for schedule in schedules:
        if getattr(schedule, 'IsTemplate', False):
            continue
        if getattr(schedule, 'IsTitleblockRevisionSchedule', False):
            continue
        label = _element_name(schedule)
        if label in options:
            label = '{} ({})'.format(label, _element_id_value(schedule.Id))
        options[label] = schedule
    return options


def _select_schedules(document):
    """Prompt for the three schedules required by the Carbon GWP workflow."""
    # Gather the available model schedules before opening the selector.
    # If there are none, stop before showing an empty dialog.
    options = _schedule_options(document)
    if not options:
        forms.alert('No schedules were found in the active model.', title=COMMAND_TITLE, warn_icon=True)
        return None

    # Show the established green multi-select UI and pre-check the default
    # Carbon GWP schedules when they are present in the active model.
    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select exactly three schedules to export:',
        button_name='Use Schedules',
        version='DevSandbox Prototype',
        SelectMultiple=True,
        initial_checked_names=DEFAULT_SCHEDULE_NAMES,
    )

    # Normalize the selector result into a list.
    # The helper can return None, a single item, or a list depending on input.
    if not selected:
        return None
    if not isinstance(selected, list):
        selected = [selected]

    # This workflow expects exactly three schedules because the downstream
    # workbook links and Dynamo replacement logic are based on three exports.
    if len(selected) != 3:
        forms.alert(
            'Select exactly three schedules. You selected {}.'.format(len(selected)),
            title=COMMAND_TITLE,
            warn_icon=True)
        return None
    return selected


# Excel workbook helpers
# ------------------------------------------------------------------
def _pick_workbook(title, default_path):
    """Prompt for an Excel workbook, preferring the supplied default folder."""
    # Use the configured default workbook folder when it exists.
    # Otherwise let the file picker open with its normal default location.
    init_dir = os.path.dirname(default_path) if default_path and os.path.isdir(os.path.dirname(default_path)) else None

    # Prefer normal Excel workbooks first, then allow macro-enabled workbooks.
    # The second picker keeps xlsm files available without changing behavior.
    picked = forms.pick_file(file_ext='xlsx', init_dir=init_dir, title=title)
    if picked:
        return picked
    picked = forms.pick_file(file_ext='xlsm', init_dir=init_dir, title=title)
    return picked


def _load_excel_application():
    """Create a Microsoft Excel COM application instance."""
    # Load the Excel interop assembly through pythonnet.
    # Some workstations resolve the simple name while others need the full name.
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')

    # Return a new Excel application instance for the caller to manage.
    # Callers are responsible for closing workbooks and quitting Excel.
    from Microsoft.Office.Interop import Excel
    return Excel.ApplicationClass()


def _worksheet_by_name(workbook, worksheet_name):
    """Return the worksheet with the matching name from an open workbook."""
    # Excel COM collections are one-based, so the loop starts at 1.
    # Return the first worksheet whose visible name matches exactly.
    for index in range(1, workbook.Worksheets.Count + 1):
        worksheet = workbook.Worksheets[index]
        if worksheet.Name == worksheet_name:
            return worksheet
    return None


def _ensure_worksheet(workbook, worksheet_name):
    """Return an existing worksheet or create it at the end of the workbook."""
    # Reuse an existing worksheet when this export has already been run.
    # That keeps formulas or workbook references pointed at the same sheet name.
    worksheet = _worksheet_by_name(workbook, worksheet_name)
    if worksheet is not None:
        return worksheet

    # Add a new worksheet at the end of the workbook when the export sheet
    # does not already exist, then assign the cleaned schedule-based name.
    worksheet = workbook.Worksheets.Add(After=workbook.Worksheets[workbook.Worksheets.Count])
    worksheet.Name = worksheet_name
    return worksheet


def _clear_worksheet(worksheet):
    """Clear worksheet contents before writing fresh schedule data."""
    # Prefer clearing all cells so stale rows and formatting-related values
    # are removed before the new schedule grid is written.
    try:
        worksheet.Cells.Clear()
    except Exception:
        # UsedRange is a fallback for Excel objects that do not expose
        # the broader Cells.Clear call reliably through COM.
        worksheet.UsedRange.Clear()


def _write_grid_to_worksheet(worksheet, grid):
    """Write a rectangular grid of values to the worksheet cells."""
    # Clear the target worksheet first so old export data does not remain
    # below or beside a smaller current export.
    _clear_worksheet(worksheet)

    # Stop early when there is no schedule data to write.
    # This prevents max-column calculations on an empty grid.
    if not grid:
        return
    row_count = len(grid)
    column_count = max([len(row) for row in grid] or [0])
    if column_count == 0:
        return

    # Write each grid value into Excel using one-based row and column indexes.
    # Missing cells in shorter rows are padded with blank strings.
    for row_index, row in enumerate(grid, start=1):
        for column_index in range(1, column_count + 1):
            value = row[column_index - 1] if column_index - 1 < len(row) else ''
            worksheet.Cells[row_index, column_index].Value2 = value

    # Auto-fit columns for readability when the workbook is opened later.
    # A failure here should not stop the export.
    try:
        worksheet.Columns.AutoFit()
    except Exception:
        pass


def _schedule_cell_text(schedule, section_type, section, row, column):
    """Read one schedule cell as text with Revit API fallbacks."""
    # Use the ViewSchedule cell reader first because it returns the visible
    # schedule text for many normal schedule cells.
    try:
        return _safe_text(schedule.GetCellText(section_type, row, column))
    except Exception:
        pass

    # Fall back to section-level readers for API/version combinations where
    # the schedule-level call is unavailable or fails for a cell.
    for method_name in ('GetCellText', 'GetCellCalculatedValue'):
        try:
            value = getattr(section, method_name)(row, column)
            return _safe_text(value)
        except Exception:
            pass
    return ''


def _section_rows(schedule, section_type):
    """Read all rows from one Revit schedule table section."""
    # Get the requested table section from the schedule.
    # Missing or unsupported sections are treated as empty.
    try:
        section = schedule.GetTableData().GetSectionData(section_type)
    except Exception:
        return []

    # Read the section bounds exposed by Revit.
    # If any bound is unavailable, the section cannot be exported safely.
    first_row = getattr(section, 'FirstRowNumber', None)
    last_row = getattr(section, 'LastRowNumber', None)
    first_column = getattr(section, 'FirstColumnNumber', None)
    last_column = getattr(section, 'LastColumnNumber', None)
    if None in (first_row, last_row, first_column, last_column):
        return []

    # Walk every cell in the section and preserve the same row/column shape
    # that Revit displays in the schedule table.
    rows = []
    for row in range(int(first_row), int(last_row) + 1):
        values = []
        for column in range(int(first_column), int(last_column) + 1):
            values.append(_schedule_cell_text(schedule, section_type, section, row, column))
        rows.append(values)
    return rows


def _schedule_table_grid(schedule):
    """Return the combined header and body rows for a Revit schedule."""
    # Export the schedule header first and body second.
    # The downstream workbook expects the visible schedule table order.
    rows = []
    rows.extend(_section_rows(schedule, DB.SectionType.Header))
    rows.extend(_section_rows(schedule, DB.SectionType.Body))

    # Normalize the rows so later Excel writing receives rectangular data.
    return normalize_grid(rows)


def _export_schedules_to_workbook(workbook_path, schedules):
    """Export selected Revit schedule grids into the target workbook."""
    # Start Excel hidden and disable alerts so overwrite/save prompts do not
    # interrupt the pyRevit command.
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    exports = []

    # Open the existing export workbook or create it if the selected path
    # does not exist yet.
    try:
        if not os.path.isfile(workbook_path):
            workbook = excel.Workbooks.Add()
            workbook.SaveAs(workbook_path)
        else:
            workbook = excel.Workbooks.Open(workbook_path)

        # Convert Revit schedule names into valid Excel worksheet names and
        # uniquify them before writing any schedule data.
        raw_sheet_names = [worksheet_name_for_schedule(_element_name(schedule)) for schedule in schedules]
        sheet_names = uniquify_worksheet_names(raw_sheet_names)

        # Export each selected Revit schedule to its corresponding worksheet
        # and collect metadata for the pyRevit output report.
        for schedule, sheet_name in zip(schedules, sheet_names):
            grid = _schedule_table_grid(schedule)
            worksheet = _ensure_worksheet(workbook, sheet_name)
            _write_grid_to_worksheet(worksheet, grid)
            exports.append({
                'schedule_name': _element_name(schedule),
                'worksheet_name': sheet_name,
                'rows': len(grid),
                'columns': max([len(row) for row in grid] or [0]),
            })

        # Save the workbook after all schedule tabs have been refreshed.
        workbook.Save()
        return exports
    finally:
        # Always close Excel resources so the workbook is not left locked.
        # Close with save=True because this function owns the export changes.
        if workbook is not None:
            workbook.Close(True)
        excel.Quit()


# Excel export worksheet reader
# ------------------------------------------------------------------
def _com_range_values_to_rows(values, row_count, column_count):
    """Convert Excel COM range values into normalized Python row data."""
    # Empty Excel ranges are normalized to an empty grid.
    # A single cell comes through as a scalar, so handle that separately.
    if values is None:
        return normalize_grid([])
    if row_count == 1 and column_count == 1:
        return normalize_grid([[values]])

    # Excel COM arrays can have different lower bounds depending on runtime.
    # Default to one-based bounds, then read actual bounds when available.
    rows = []
    row_lower_bound = 1
    column_lower_bound = 1
    try:
        row_lower_bound = int(values.GetLowerBound(0))
        column_lower_bound = int(values.GetLowerBound(1))
    except Exception:
        pass

    # Copy each COM array item into normal Python row lists.
    # Missing or unreadable cells are kept as None and normalized later.
    for row_index in range(1, row_count + 1):
        row = []
        for column_index in range(1, column_count + 1):
            try:
                if hasattr(values, 'GetValue'):
                    row.append(values.GetValue(
                        row_lower_bound + row_index - 1,
                        column_lower_bound + column_index - 1))
                else:
                    row.append(values[
                        row_lower_bound + row_index - 1,
                        column_lower_bound + column_index - 1])
            except Exception:
                row.append(None)
        rows.append(row)
    return normalize_grid(rows)


def _read_export_rows(workbook_path):
    """Refresh and read the post-processing workbook Export worksheet."""
    # Open the post-processing workbook read-only because this command only
    # needs the calculated values from its Export worksheet.
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Open(workbook_path, ReadOnly=True)

        # Ask Excel to refresh workbook links and calculations.
        # Each call is optional because workbook behavior varies by file.
        try:
            workbook.RefreshAll()
        except Exception:
            pass
        try:
            excel.CalculateUntilAsyncQueriesDone()
        except Exception:
            pass
        try:
            excel.CalculateFullRebuild()
        except Exception:
            try:
                excel.Calculate()
            except Exception:
                pass

        # Locate the required Export worksheet that contains parameter names
        # and values prepared by the post-processing workbook.
        worksheet = _worksheet_by_name(workbook, EXPORT_WORKSHEET_NAME)
        if worksheet is None:
            raise ValueError('Worksheet not found: {}'.format(EXPORT_WORKSHEET_NAME))

        # Read the used range into Python row data for downstream validation.
        used_range = worksheet.UsedRange
        row_count = int(used_range.Rows.Count)
        column_count = int(used_range.Columns.Count)
        rows = _com_range_values_to_rows(used_range.Value2, row_count, column_count)
        return rows
    finally:
        # Close the read-only workbook without saving and quit Excel.
        # This prevents lingering Excel processes after pyRevit finishes.
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


# Revit family parameter writing
# ------------------------------------------------------------------
def _family_symbols_by_family_name(document, family_name):
    """Collect family symbols whose parent family name matches the target."""
    # Walk all family symbols in the model and keep only types whose parent
    # family name matches the configured Carbon Pie family.
    symbols = []
    collector = DB.FilteredElementCollector(document).OfClass(DB.FamilySymbol)
    for symbol in collector:
        family = getattr(symbol, 'Family', None)
        if family is not None and _element_name(family) == family_name:
            symbols.append(symbol)
    return symbols


def _set_parameter_value(parameter, value):
    """Set one Revit parameter using a value converted for its storage type."""
    # Skip parameters that are missing or read-only and return a report reason
    # instead of raising an exception.
    if parameter is None:
        return False, 'missing parameter'
    if getattr(parameter, 'IsReadOnly', False):
        return False, 'read-only parameter'

    # Convert the incoming Excel value to text first.
    # The parameter storage type controls the final Revit value conversion.
    storage_type = parameter.StorageType
    text = _safe_text(value)

    # Set the parameter using the Revit API method that matches its storage
    # type, and report unsupported storage types instead of failing the run.
    try:
        if storage_type == DB.StorageType.String:
            parameter.Set(text)
        elif storage_type == DB.StorageType.Integer:
            parameter.Set(int(float(text)) if text else 0)
        elif storage_type == DB.StorageType.Double:
            parameter.Set(float(text) if text else 0.0)
        elif storage_type == DB.StorageType.ElementId:
            parameter.Set(DB.ElementId(int(float(text))))
        else:
            return False, 'unsupported storage type'
    except Exception as error:
        # Return the Revit/Excel conversion error so the output table can show
        # exactly why a parameter write was skipped.
        return False, _safe_text(error)
    return True, ''


def _write_family_type_parameters(symbols, pairs):
    """Write every parameter/value pair to each collected family type."""
    # Track successful writes and skipped writes separately for the final
    # pyRevit report.
    successes = []
    skips = []

    # Apply every validated Export worksheet pair to every target family type.
    # Each individual parameter write reports success or a skip reason.
    for symbol in symbols:
        symbol_name = _element_name(symbol)
        for pair in pairs:
            parameter_name = pair['parameter_name']
            parameter = symbol.LookupParameter(parameter_name)
            ok, reason = _set_parameter_value(parameter, pair['value'])
            if ok:
                successes.append([symbol_name, parameter_name, pair['value']])
            else:
                skips.append([symbol_name, parameter_name, reason])
    return successes, skips


# pyRevit output
# ------------------------------------------------------------------
def _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips):
    """Print the Carbon GWP run summary to the pyRevit output window."""
    # Print the high-level run metadata first so the selected files and target
    # family are visible even when there are skipped rows or writes.
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Export container workbook: `{}`'.format(metadata['export_workbook']))
    output.print_md('Post-processing workbook: `{}`'.format(metadata['post_processing_workbook']))
    output.print_md('Target family: `{}`'.format(CARBON_PIE_FAMILY_NAME))
    output.print_md('Family types found: {}'.format(metadata['family_type_count']))
    output.print_md('Parameter/value pairs attempted per type: {}'.format(len(valid_pairs)))
    output.print_md('Successful writes: {}'.format(len(successes)))

    # Report the Revit schedule export results.
    # This confirms which worksheet each selected schedule was written to.
    if exports:
        output.print_md('## Schedule Exports')
        output.print_table(
            [[item['schedule_name'], item['worksheet_name'], item['rows'], item['columns']] for item in exports],
            columns=['Schedule', 'Worksheet', 'Rows', 'Columns'])

    # Report the validated Export worksheet parameter/value pairs that were
    # eligible for Revit writes.
    if valid_pairs:
        output.print_md('## Export Sheet Parameter Values')
        output.print_table(
            [[pair['row'], pair['parameter_name'], pair['value']] for pair in valid_pairs],
            columns=['Row', 'Parameter', 'Value'])

    # Report rows skipped while reading or validating the Export worksheet.
    if skipped_rows:
        output.print_md('## Skipped Export Rows')
        output.print_table(
            [[item.get('row'), item.get('reason'), item.get('value', '')] for item in skipped_rows],
            columns=['Row', 'Reason', 'Value'])

    # Report parameters that could not be written on the target family types.
    if write_skips:
        output.print_md('## Skipped Parameter Writes')
        output.print_table(write_skips, columns=['Family Type', 'Parameter', 'Reason'])

    # Report successful writes last as the final confirmation table.
    if successes:
        output.print_md('## Successful Writes')
        output.print_table(successes, columns=['Family Type', 'Parameter', 'Value'])


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
# ==================================================================
def main():
    """Run the full schedule export, workbook read, and parameter write workflow."""
    # Get the pyRevit output window and active Revit document for this run.
    output = script.get_output()
    document = revit.doc

    # Ask the user to choose the three source schedules before touching Excel.
    schedules = _select_schedules(document)
    if not schedules:
        return

    # Ask for the export container workbook and post-processing workbook.
    # Both choices are required before the workflow can continue.
    export_workbook = _pick_workbook('Select Team Carbon GWP export container workbook',
                                     DEFAULT_EXPORT_CONTAINER_PATH)
    if not export_workbook:
        return
    post_processing_workbook = _pick_workbook('Select Team Carbon GWP post-processing workbook',
                                             DEFAULT_POST_PROCESSING_PATH)
    if not post_processing_workbook:
        return
    if not os.path.isfile(post_processing_workbook):
        forms.alert('Post-processing workbook not found:\n{}'.format(post_processing_workbook),
                    title=COMMAND_TITLE, warn_icon=True)
        return

    # Refresh the export workbook from Revit schedules, then read the calculated
    # Export worksheet values from the post-processing workbook.
    exports = _export_schedules_to_workbook(export_workbook, schedules)
    export_rows = _read_export_rows(post_processing_workbook)

    # Convert workbook rows into parameter/value pairs and validate them before
    # opening a Revit transaction.
    pairs, skipped_rows = parameter_value_pairs_from_export_rows(export_rows)
    valid_pairs, validation_skips = validate_parameter_value_pairs(pairs)
    skipped_rows.extend(validation_skips)
    if not valid_pairs:
        forms.alert('No parameter/value pairs were found on the Export worksheet.',
                    title=COMMAND_TITLE, warn_icon=True)
        return

    # Find the target Carbon Pie family types in the active model.
    # Stop before starting a transaction if the family is not loaded.
    symbols = _family_symbols_by_family_name(document, CARBON_PIE_FAMILY_NAME)
    if not symbols:
        forms.alert('Family not found in active model: {}'.format(CARBON_PIE_FAMILY_NAME),
                    title=COMMAND_TITLE, warn_icon=True)
        return

    # Write the validated values inside one Revit transaction.
    # Excel export and workbook reads have already completed before this point.
    with revit.Transaction('Carbon GWP Pull - Write Family Type Parameters'):
        successes, write_skips = _write_family_type_parameters(symbols, valid_pairs)

    # Package the run metadata and print the final output report.
    metadata = {
        'export_workbook': export_workbook,
        'post_processing_workbook': post_processing_workbook,
        'family_type_count': len(symbols),
    }
    _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips)


if __name__ == '__main__':
    # Run the command and catch unexpected failures so the user gets a readable
    # pyRevit output traceback instead of a silent command stop.
    try:
        main()
    except Exception:
        # Print the traceback to the pyRevit output window and show a compact
        # alert that points the user back to the detailed report.
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('The command stopped before it could finish.')
        output.print_md('```')
        output.print_md(traceback.format_exc())
        output.print_md('```')
        forms.alert(
            'Carbon GWP Pull stopped with an error. Review the pyRevit output window for details.',
            title=COMMAND_TITLE,
            warn_icon=True)
