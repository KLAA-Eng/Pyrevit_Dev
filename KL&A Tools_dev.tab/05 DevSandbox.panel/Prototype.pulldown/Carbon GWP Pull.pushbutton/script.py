# -*- coding: utf-8 -*-
from __future__ import print_function

__version__ = 'v0.0.0.proto'
__doc__ = """Version: v0.0.0.proto
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
# Imports
# ------------------------------------------------------------------

import os
import sys
import traceback

from pyrevit import DB, forms, revit, script

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
# ==================================================================
# Command setup and shared helpers
# ------------------------------------------------------------------

COMMAND_TITLE = __title__


def _extension_root(path):
    """Locate the extension bundle that owns a command path.

    Args:
        path: Path to the executing command script.
    Returns:
        The nearest ``.extension`` ancestor, or the absolute input path.
    """
    current = os.path.abspath(path)
    # Locate the extension root. Commands live deep in the bundle hierarchy,
    # so climb folders until pyRevit's ``.extension`` boundary is found.
    while True:
        if current.lower().endswith('.extension'):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
# Load shared helpers. pyRevit executes this nested command directly, so add
# the extension library before importing helpers that do not ship with pyRevit.
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


# COMPAT: IronPython exposes ``unicode`` while CPython 3 exposes ``str``.
try:
    TEXT_TYPES = (unicode,)
except NameError:
    TEXT_TYPES = (str,)


# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
# ==================================================================
# Revit, Excel, and text helpers
# ------------------------------------------------------------------
def _element_id_value(element_id):
    """Read the integer from a Revit element ID.

    Args:
        element_id: A Revit ``ElementId`` instance, or ``None``.
    Returns:
        The integer ID, or ``None`` when no ID value can be read.
    """
    # COMPAT: Revit 2024+ uses ``Value``; older releases use ``IntegerValue``.
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None

def _element_name(element, default='Unnamed'):
    """Read a Revit element name without propagating lookup failures.

    Args:
        element: A Revit element, wrapper, or ``None``.
        default: Value returned if the element has no readable name.
    Returns:
        The element name or ``default``.
    """
    if element is None:
        return default

    # COMPAT: Some pyRevit wrappers expose ``Name`` without the static API.
    try:
        name = DB.Element.Name.GetValue(element)
    except Exception:
        try:
            name = element.Name
        except Exception:
            name = None
    return name or default

def _safe_text(value):
    """Normalize a host value for output or parameter writing.

    Args:
        value: Excel, Revit, or caller-provided value.
    Returns:
        Text with missing values blank and integral numbers without decimals.
    """
    if value is None:
        return ''
    # Preserve existing text. Parameter names and report labels can depend on
    # their original spelling and whitespace.
    if isinstance(value, TEXT_TYPES):
        return value
    # Normalize Excel numbers. Excel represents 5 as 5.0; remove that display
    # decimal before the value reaches a Revit text parameter.
    try:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
    except Exception:
        pass
    # Normalize formatted cells. Excel can return 5.0 as text instead of a
    # float, so repeat the whole-number cleanup after string conversion.
    text = str(value)
    if text.endswith('.0'):
        try:
            return str(int(float(text)))
        except Exception:
            pass
    return text

# Schedule selection and workbook export
# ------------------------------------------------------------------
def _schedule_options(document):
    """Create selection labels for exportable model schedules.

    Args:
        document: Active Revit project document.
    Returns:
        Unique display labels mapped to ``ViewSchedule`` instances.
    """
    # Collect exportable schedules. The collector sees every schedule, but
    # templates and titleblock revision schedules cannot supply export data.
    schedules = DB.FilteredElementCollector(document).OfClass(DB.ViewSchedule)
    options = {}
    # Build unique choices. Duplicate schedule names receive an ElementId so
    # each label still resolves to exactly one schedule.
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
    """Prompt for the three schedule exports required by the workbook.

    Args:
        document: Active Revit project document.
    Returns:
        Three selected schedules, or ``None`` after cancellation or rejection.
    """
    options = _schedule_options(document)
    if not options:
        forms.alert('No schedules were found in the active model.', title=COMMAND_TITLE, warn_icon=True)
        return None
    # Select source schedules. Pre-select the standard Carbon schedules when
    # their names exist in the active project.
    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select exactly three schedules to export:',
        button_name='Use Schedules',
        version='DevSandbox Prototype',
        SelectMultiple=True,
        initial_checked_names=DEFAULT_SCHEDULE_NAMES,
    )
    # Normalize the selection. The form can return one object or a list; the
    # length check and export loop need one consistent list shape.
    if not selected:
        return None
    if not isinstance(selected, list):
        selected = [selected]

    # INVARIANT: The downstream workbook formulas require three schedule tabs.
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
    """Prompt for an Excel workbook using a configured starting folder.

    Args:
        title: Text to display in the file picker.
        default_path: Workbook path whose existing directory starts the picker.
    Returns:
        Chosen workbook path, or a falsey value after cancellation.
    """
    init_dir = os.path.dirname(default_path) if default_path and os.path.isdir(os.path.dirname(default_path)) else None
    # Select a workbook. Start in the configured folder and allow macro-enabled
    # files without this command running workbook macros.
    picked = forms.pick_file(file_ext='xlsx', init_dir=init_dir, title=title)
    if picked:
        return picked
    picked = forms.pick_file(file_ext='xlsm', init_dir=init_dir, title=title)
    return picked

def _load_excel_application():
    """Start a caller-owned Microsoft Excel COM application.

    Returns:
        Excel application that the caller must close with ``Quit``.
    """
    # COMPAT: Office installations resolve different Excel interop names.
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')
    # Create only the Excel application. Each caller owns the matching
    # workbook-close and Excel-quit lifecycle for the files it opens.
    from Microsoft.Office.Interop import Excel
    return Excel.ApplicationClass()

def _worksheet_by_name(workbook, worksheet_name):
    """Find an open workbook worksheet by its visible name.

    Args:
        workbook: Open Excel workbook to search.
        worksheet_name: Exact visible worksheet name.
    Returns:
        Matching worksheet, or ``None`` when absent.
    """
    # COMPAT: Excel COM worksheet collections start at index 1, not 0.
    for index in range(1, workbook.Worksheets.Count + 1):
        worksheet = workbook.Worksheets[index]
        if worksheet.Name == worksheet_name:
            return worksheet
    return None

def _ensure_worksheet(workbook, worksheet_name):
    """Find an export worksheet or append it to a workbook.

    Args:
        workbook: Open Excel workbook to update.
        worksheet_name: Excel-safe export worksheet name.
    Returns:
        Existing worksheet or newly appended worksheet.
    """
    # INVARIANT: Reuse sheets so workbook formulas keep their expected links.
    worksheet = _worksheet_by_name(workbook, worksheet_name)
    if worksheet is not None:
        return worksheet
    # Append the export sheet after existing tabs so unrelated workbook tabs
    # remain in their original order.
    worksheet = workbook.Worksheets.Add(After=workbook.Worksheets[workbook.Worksheets.Count])
    worksheet.Name = worksheet_name
    return worksheet

def _clear_worksheet(worksheet):
    """Remove previous values from an export worksheet.

    Args:
        worksheet: Excel worksheet to clear before export.
    """
    try:
        worksheet.Cells.Clear()
    except Exception:
        # WORKAROUND: Some Excel COM wrappers expose only ``UsedRange.Clear``.
        worksheet.UsedRange.Clear()

def _write_grid_to_worksheet(worksheet, grid):
    """Replace an export worksheet with schedule cell values.

    Args:
        worksheet: Excel worksheet to update.
        grid: Rectangular or ragged iterable of schedule rows.
    """
    # INVARIANT: Clear first so a shorter export cannot leave stale cells.
    _clear_worksheet(worksheet)
    # Validate the grid. An empty schedule has no cells to write, so skip width
    # calculations and Excel COM calls.
    if not grid:
        return
    row_count = len(grid)
    column_count = max([len(row) for row in grid] or [0])
    if column_count == 0:
        return
    # Write a rectangular grid. Revit rows may have different lengths, so fill
    # missing cells with blanks before writing to Excel.
    for row_index, row in enumerate(grid, start=1):
        # Excel cell indexes begin at 1, unlike normal Python list indexes.
        for column_index in range(1, column_count + 1):
            value = row[column_index - 1] if column_index - 1 < len(row) else ''
            worksheet.Cells[row_index, column_index].Value2 = value
    # Format for readability. AutoFit changes presentation only, so a failure
    # here must not discard the completed schedule export.
    try:
        worksheet.Columns.AutoFit()
    except Exception:
        pass

def _schedule_cell_text(schedule, section_type, section, row, column):
    """Read the displayed value from a Revit schedule cell.

    Args:
        schedule: Source Revit ``ViewSchedule``.
        section_type: Revit table section type.
        section: Revit table section containing the cell.
        row: Revit table row index.
        column: Revit table column index.
    Returns:
        Displayed cell text, or an empty string if it cannot be read.
    """
    try:
        return _safe_text(schedule.GetCellText(section_type, row, column))
    except Exception:
        pass
    # Fall back to section APIs when schedule-level reading is unavailable.
    # COMPAT: Revit table APIs expose different cell readers by release.
    for method_name in ('GetCellText', 'GetCellCalculatedValue'):
        try:
            value = getattr(section, method_name)(row, column)
            return _safe_text(value)
        except Exception:
            pass
    return ''


def _section_rows(schedule, section_type):
    """Extract the displayed rows from a Revit schedule section.

    Args:
        schedule: Source Revit ``ViewSchedule``.
        section_type: Revit table section type to extract.
    Returns:
        Cell-text rows, or an empty list when the section is unavailable.
    """
    try:
        section = schedule.GetTableData().GetSectionData(section_type)
    except Exception:
        return []
    # Validate table bounds. Missing Revit bounds mean this section cannot be
    # exported safely.
    first_row = getattr(section, 'FirstRowNumber', None)
    last_row = getattr(section, 'LastRowNumber', None)
    first_column = getattr(section, 'FirstColumnNumber', None)
    last_column = getattr(section, 'LastColumnNumber', None)
    if None in (first_row, last_row, first_column, last_column):
        return []

    rows = []
    for row in range(int(first_row), int(last_row) + 1):
        values = []
        for column in range(int(first_column), int(last_column) + 1):
            values.append(_schedule_cell_text(schedule, section_type, section, row, column))
        rows.append(values)
    return rows


def _schedule_table_grid(schedule):
    """Combine a schedule header and body into a rectangular text grid.

    Args:
        schedule: Revit ``ViewSchedule`` to export.
    Returns:
        Rectangular grid with header rows before body rows.
    """
    rows = []
    rows.extend(_section_rows(schedule, DB.SectionType.Header))
    rows.extend(_section_rows(schedule, DB.SectionType.Body))
    # Combine visible sections. Keep the header before the body so Excel matches
    # the order users see in Revit.
    return normalize_grid(rows)


def _export_schedules_to_workbook(workbook_path, schedules):
    """Refresh schedule export worksheets in an Excel workbook.

    Opens or creates the workbook, writes the selected schedules, saves it,
    and releases the Excel process.

    Args:
        workbook_path: Path to the export container workbook.
        schedules: Selected Revit ``ViewSchedule`` instances.
    Returns:
        Export metadata dictionaries for the pyRevit report.
    """
    excel = _load_excel_application()
    # Prepare background Excel. Hide the application and its prompts so they do
    # not interrupt the pyRevit command.
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    exports = []
    # Open or create the container. Existing workbooks keep their formulas and
    # unrelated tabs; missing workbooks are created at the chosen path.
    try:
        if not os.path.isfile(workbook_path):
            workbook = excel.Workbooks.Add()
            workbook.SaveAs(workbook_path)
        else:
            workbook = excel.Workbooks.Open(workbook_path)
        # Plan worksheet names. Convert Revit titles to unique Excel names so
        # duplicate titles cannot overwrite each other's export.
        raw_sheet_names = [worksheet_name_for_schedule(_element_name(schedule)) for schedule in schedules]
        sheet_names = uniquify_worksheet_names(raw_sheet_names)

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
        # Save the completed export only after every selected schedule tab is
        # refreshed, avoiding a partial workbook on an earlier failure.
        workbook.Save()
        return exports
    finally:
        # INVARIANT: This function owns the export workbook and must release
        # Excel so the file is not left locked for the post-processing workbook.
        if workbook is not None:
            workbook.Close(True)
        excel.Quit()


# Post-processing workbook reader
# ------------------------------------------------------------------
def _com_range_values_to_rows(values, row_count, column_count):
    """Copy an Excel COM range into normalized Python text rows.

    Args:
        values: Scalar or two-dimensional Excel COM range value.
        row_count: Excel range row count.
        column_count: Excel range column count.
    Returns:
        Rectangular grid of text values.
    """
    if values is None:
        return normalize_grid([])
    if row_count == 1 and column_count == 1:
        return normalize_grid([[values]])
    # Convert the COM range. Excel exposes multi-cell ranges as COM arrays,
    # rather than the normal Python lists used by the rest of this command.
    # COMPAT: Excel COM arrays can expose lower bounds other than 1.
    rows = []
    row_lower_bound = 1
    column_lower_bound = 1
    try:
        row_lower_bound = int(values.GetLowerBound(0))
        column_lower_bound = int(values.GetLowerBound(1))
    except Exception:
        pass
    # Copy every cell into Python rows. Preserve unreadable COM values as
    # ``None`` so later normalization represents them as blank cells.
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
    """Refresh links and read rows from the post-processing Export sheet.

    Opens Excel read-only and closes it without saving after recalculation.

    Args:
        workbook_path: Path to the post-processing Excel workbook.
    Returns:
        Rectangular grid of Export worksheet values.

    Raises:
        ValueError: Required Export worksheet is not present.
    """
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Open(workbook_path, ReadOnly=True)
        # Open the analyst workbook read-only. This command needs calculated
        # values but must not overwrite its formulas or source data.
        # WORKAROUND: Excel versions and workbook connections support different
        # refresh APIs, so try each available calculation path.
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
        # Read the workbook contract. The Export tab's first two columns map
        # Revit parameter names to the values this command will write.
        worksheet = _worksheet_by_name(workbook, EXPORT_WORKSHEET_NAME)
        if worksheet is None:
            raise ValueError('Worksheet not found: {}'.format(EXPORT_WORKSHEET_NAME))

        used_range = worksheet.UsedRange
        row_count = int(used_range.Rows.Count)
        column_count = int(used_range.Columns.Count)
        rows = _com_range_values_to_rows(used_range.Value2, row_count, column_count)
        return rows
    finally:
        # INVARIANT: This reader never saves analyst-owned workbook changes.
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


# Carbon Pie family parameter writing
# ------------------------------------------------------------------
def _family_symbols_by_family_name(document, family_name):
    """Collect type symbols belonging to a named Revit family.

    Args:
        document: Active Revit project document.
        family_name: Target Revit family name.
    Returns:
        Matching Revit ``FamilySymbol`` instances.
    """
    symbols = []
    # Collect Carbon Pie types. Revit stores family types as symbols, so filter
    # all symbols by their parent family name.
    collector = DB.FilteredElementCollector(document).OfClass(DB.FamilySymbol)
    for symbol in collector:
        family = getattr(symbol, 'Family', None)
        if family is not None and _element_name(family) == family_name:
            symbols.append(symbol)
    return symbols


def _set_parameter_value(parameter, value):
    """Write one Export worksheet value to a Revit parameter.

    Args:
        parameter: Revit parameter to write, or ``None``.
        value: Excel value to convert for the storage type.
    Returns:
        Tuple ``(success, reason)``; ``reason`` is empty after success.
    """
    if parameter is None:
        return False, 'missing parameter'
    if getattr(parameter, 'IsReadOnly', False):
        return False, 'read-only parameter'
    # Prepare the Revit value. Convert Excel's generic cell value to the exact
    # storage type required by ``Set``; failures become report rows.
    storage_type = parameter.StorageType
    text = _safe_text(value)

    # Revit parameters reject values whose Python type does not match storage.
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
        return False, _safe_text(error)
    return True, ''


def _write_family_type_parameters(symbols, pairs):
    """Apply validated Export worksheet values to every target family type.

    Args:
        symbols: Target Revit ``FamilySymbol`` instances.
        pairs: Validated parameter/value dictionaries from the Export sheet.
    Returns:
        Tuple ``(successes, skips)`` of pyRevit report-table rows.
    """
    successes = []
    skips = []
    # Track each write result. The report must distinguish completed writes from
    # missing, read-only, or incompatible parameters.
    for symbol in symbols:
        symbol_name = _element_name(symbol)
        # Apply every validated Export row to this Carbon Pie family type.
        for pair in pairs:
            parameter_name = pair['parameter_name']
            parameter = symbol.LookupParameter(parameter_name)
            ok, reason = _set_parameter_value(parameter, pair['value'])
            if ok:
                successes.append([symbol_name, parameter_name, pair['value']])
            else:
                skips.append([symbol_name, parameter_name, reason])
    return successes, skips


# pyRevit output reporting
# ------------------------------------------------------------------
def _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips):
    """Render a Carbon GWP result summary in the pyRevit output window.

    Args:
        output: pyRevit output window for this command run.
        metadata: Selected workbooks and target-family metadata.
        exports: Schedule export metadata dictionaries.
        valid_pairs: Parameter/value dictionaries approved for writing.
        skipped_rows: Rows rejected while parsing or validating Export data.
        successes: Successful parameter-write table rows.
        write_skips: Skipped parameter-write table rows.
    """
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Export container workbook: `{}`'.format(metadata['export_workbook']))
    output.print_md('Post-processing workbook: `{}`'.format(metadata['post_processing_workbook']))
    output.print_md('Target family: `{}`'.format(CARBON_PIE_FAMILY_NAME))
    output.print_md('Family types found: {}'.format(metadata['family_type_count']))
    output.print_md('Parameter/value pairs attempted per type: {}'.format(len(valid_pairs)))
    output.print_md('Successful writes: {}'.format(len(successes)))
    # Report only populated sections. Empty headings add noise, while populated
    # tables show the selected schedules, skipped rows, and write outcomes.
    if exports:
        output.print_md('## Schedule Exports')
        output.print_table(
            [[item['schedule_name'], item['worksheet_name'], item['rows'], item['columns']] for item in exports],
            columns=['Schedule', 'Worksheet', 'Rows', 'Columns'])
    if valid_pairs:
        output.print_md('## Export Sheet Parameter Values')
        output.print_table(
            [[pair['row'], pair['parameter_name'], pair['value']] for pair in valid_pairs],
            columns=['Row', 'Parameter', 'Value'])
    if skipped_rows:
        output.print_md('## Skipped Export Rows')
        output.print_table(
            [[item.get('row'), item.get('reason'), item.get('value', '')] for item in skipped_rows],
            columns=['Row', 'Reason', 'Value'])
    if write_skips:
        output.print_md('## Skipped Parameter Writes')
        output.print_table(write_skips, columns=['Family Type', 'Parameter', 'Reason'])
    if successes:
        output.print_md('## Successful Writes')
        output.print_table(successes, columns=['Family Type', 'Parameter', 'Value'])


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
# ==================================================================
def main():
    """Run the interactive Carbon GWP export and parameter-write workflow.

    Prompts for schedules and workbooks, then writes validated Export values
    to Carbon Pie types in one Revit transaction.
    """
    output = script.get_output()
    document = revit.doc
    # Collect required user input. Later steps need all three schedules and both
    # workbooks, so cancellation ends the run before external work begins.
    schedules = _select_schedules(document)
    if not schedules:
        return
    # Select the two workbook roles. The container receives schedule tabs; the
    # post-processing workbook calculates values written back to Revit.
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
    # Refresh external data first. Excel failures occur before a Revit
    # transaction, keeping file problems separate from model changes.
    exports = _export_schedules_to_workbook(export_workbook, schedules)
    export_rows = _read_export_rows(post_processing_workbook)

    # INVARIANT: Validate workbook rows before a Revit transaction can change
    # any family type.
    pairs, skipped_rows = parameter_value_pairs_from_export_rows(export_rows)
    valid_pairs, validation_skips = validate_parameter_value_pairs(pairs)
    skipped_rows.extend(validation_skips)
    if not valid_pairs:
        forms.alert('No parameter/value pairs were found on the Export worksheet.',
                    title=COMMAND_TITLE, warn_icon=True)
        return
    # Find target types before a transaction starts. A missing Carbon Pie family
    # must not create an empty or misleading model change.
    symbols = _family_symbols_by_family_name(document, CARBON_PIE_FAMILY_NAME)
    if not symbols:
        forms.alert('Family not found in active model: {}'.format(CARBON_PIE_FAMILY_NAME),
                    title=COMMAND_TITLE, warn_icon=True)
        return
    # Write values in one transaction. Revit can undo the complete update if a
    # later parameter write fails.
    # INVARIANT: This transaction is the only place the active model changes.
    with revit.Transaction('Carbon GWP Pull - Write Family Type Parameters'):
        successes, write_skips = _write_family_type_parameters(symbols, valid_pairs)

    metadata = {
        'export_workbook': export_workbook,
        'post_processing_workbook': post_processing_workbook,
        'family_type_count': len(symbols),
    }
    _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Report diagnostic detail in pyRevit while keeping the user dialog
        # concise enough to act on quickly.
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
