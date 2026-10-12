# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = 'Carbon\nGWP Pull'
__version__ = 'v1.0'

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
# ==================================================================
# Imports
# ------------------------------------------------------------------

import os
import sys
import time
import traceback

from pyrevit import DB, forms, revit, script

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
# ==================================================================
# Command setup and shared helpers
# ------------------------------------------------------------------

COMMAND_TITLE = __title__.replace('\n', ' ')
TARGET_SHEET_NAME = 'SYNC TO CENTRAL'
POST_PROCESSING_REFRESH_TIMEOUT_SECONDS = 60.0
POST_PROCESSING_REFRESH_POLL_SECONDS = 0.25
CLOUD_MODEL_WORKBOOK_FOLDER = r'J:\Standards\910 Revit Support\KLAA Library'
MATERIAL_ACCURACY_WORKSHEET_NAME = 'Post-Processing'
MATERIAL_ACCURACY_FIRST_ROW = 41
MATERIAL_ACCURACY_LAST_ROW = 70
MATERIAL_ACCURACY_COLUMN = 'F'
EXPORT_WORKBOOK_PICKER_TITLE = 'Select Export Workbook (DYN Out sheets will be replaced)'
POST_PROCESSING_WORKBOOK_PICKER_TITLE = 'Select Post-processing'
EXCEL_WORKBOOK_FILTER = (
    'Excel Workbook (*.xlsx)|*.xlsx|'
    'Excel Macro-Enabled Workbook (*.xlsm)|*.xlsm')
CHART_OUTPUT_FOLDER_NAME = 'Carbon GWP Pull Charts'
MAX_CHART_SLICE_COUNT = 30
CHART_IMAGE_FILENAMES = {
    'gwp': 'Carbon GWP Summary.png',
    'volume': 'Carbon Material Volume Summary.png',
}


def _is_target_sheet_name(value):
    """Return whether a sheet name matches the required target, ignoring case."""
    return _safe_text(value).lower() == TARGET_SHEET_NAME.lower()


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
from excel_com import (
    add_workbook,
    add_worksheet,
    call_method,
    cell_at,
    close_excel_application,
    collection_count,
    create_excel_application,
    get_item,
    get_property,
    open_workbook,
    set_property,
    save_workbook,
    worksheet_collection,
)
from carbon_gwp.workflow import (
    DEFAULT_EXPORT_CONTAINER_PATH,
    DEFAULT_SCHEDULE_NAMES,
    EXPORT_WORKSHEET_NAME,
    has_exportable_cells,
    normalize_grid,
    safe_text as _safe_text,
    uniquify_worksheet_names,
    worksheet_name_for_schedule,
)
from carbon_gwp.chart import (
    GWP_CHART_UNIT,
    VOLUME_CHART_UNIT,
    chart_slices_from_export_rows,
    chart_total,
    format_chart_amount,
    format_chart_table_amount,
)
from carbon_gwp.revit_chart import (
    create_or_reload_chart,
    image_bottom_left,
    render_chart_png,
    titleblock_top_right,
)


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
        version=__version__,
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
def _cloud_model_workbook_folder():
    """Return the cloud-model workbook folder with an offline local fallback."""
    if os.path.isdir(CLOUD_MODEL_WORKBOOK_FOLDER):
        return CLOUD_MODEL_WORKBOOK_FOLDER
    user_profile = os.environ.get('USERPROFILE')
    if user_profile and os.path.isdir(user_profile):
        return user_profile
    system_drive = os.environ.get('SystemDrive', 'C:')
    return system_drive + os.sep


def _model_workbook_folder(document, fallback_path):
    """Return a usable workbook folder for the active Revit model.

    Local and workshared-central models use their disk folder. Cloud models use
    the KL&A Library folder when it is accessible, otherwise the user's local
    Windows profile folder. Revit Server, detached, and unsaved models retain
    the established Carbon-folder fallback because they do not expose a usable
    Windows project directory.
    """
    fallback_folder = os.path.dirname(fallback_path)
    try:
        if getattr(document, 'IsModelInCloud', False):
            return _cloud_model_workbook_folder()
    except Exception:
        return fallback_folder

    if getattr(document, 'IsWorkshared', False):
        try:
            central_path = document.GetWorksharingCentralModelPath()
            visible_path = DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
            central_folder = os.path.dirname(visible_path)
            if central_folder and os.path.isdir(central_folder):
                return central_folder
        except Exception:
            pass

    try:
        model_folder = os.path.dirname(document.PathName)
        if model_folder and os.path.isdir(model_folder):
            return model_folder
    except Exception:
        pass
    return fallback_folder


def _pick_workbook(title, initial_directory):
    """Prompt for an Excel workbook using the provided starting folder.

    Args:
        title: Text to display in the file picker.
        initial_directory: Existing folder that should open in the picker.

    Returns:
        Chosen workbook path, or a falsey value after cancellation.
    """
    init_dir = initial_directory if initial_directory and os.path.isdir(initial_directory) else None
    # Show both supported formats in one dialog. A cancelled selection must end
    # the command rather than opening a second, unexpected file picker.
    return forms.pick_file(
        files_filter=EXCEL_WORKBOOK_FILTER,
        init_dir=init_dir,
        title=title)

def _load_excel_application():
    """Return the shared Excel COM application used by this command."""
    return create_excel_application()

def _worksheet_by_name(workbook, worksheet_name):
    """Find an open workbook worksheet by its visible name.

    Args:
        workbook: Open Excel workbook to search.
        worksheet_name: Exact visible worksheet name.

    Returns:
        Matching worksheet, or ``None`` when absent.
    """
    # COMPAT: Excel COM worksheet collections start at index 1, not 0.
    worksheets = worksheet_collection(workbook)
    for index in range(1, collection_count(worksheets) + 1):
        worksheet = get_item(worksheets, index)
        if get_property(worksheet, 'Name') == worksheet_name:
            return worksheet
    return None


def _worksheet_by_name_ignoring_case(workbook, worksheet_name):
    """Find a workbook worksheet by name without depending on letter case."""
    worksheets = worksheet_collection(workbook)
    for index in range(1, collection_count(worksheets) + 1):
        worksheet = get_item(worksheets, index)
        if _safe_text(get_property(worksheet, 'Name')).lower() == _safe_text(worksheet_name).lower():
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
    worksheets = worksheet_collection(workbook)
    worksheet = add_worksheet(workbook, get_item(worksheets, collection_count(worksheets)))
    set_property(worksheet, 'Name', worksheet_name)
    return worksheet

def _clear_worksheet(worksheet):
    """Remove previous values from an export worksheet.

    Args:
        worksheet: Excel worksheet to clear before export.
    """
    try:
        call_method(get_property(worksheet, 'Cells'), 'Clear')
    except Exception:
        # WORKAROUND: Some Excel COM wrappers expose only ``UsedRange.Clear``.
        call_method(get_property(worksheet, 'UsedRange'), 'Clear')

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
            set_property(cell_at(worksheet, row_index, column_index), 'Value2', value)
    # Format for readability. AutoFit changes presentation only, so a failure
    # here must not discard the completed schedule export.
    try:
        call_method(get_property(worksheet, 'Columns'), 'AutoFit')
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
    errors = []
    for method_name in ('GetCellText', 'GetCellCalculatedValue'):
        try:
            value = getattr(section, method_name)(row, column)
            return _safe_text(value)
        except Exception as error:
            errors.append(_safe_text(error))
    raise RuntimeError(
        'Could not read schedule cell at row {}, column {}: {}'.format(
            row, column, '; '.join(errors)))


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
    except Exception as error:
        raise RuntimeError('Could not access schedule table section: {}'.format(error))
    # Validate table bounds. Missing Revit bounds mean this section cannot be
    # exported safely.
    first_row = getattr(section, 'FirstRowNumber', None)
    last_row = getattr(section, 'LastRowNumber', None)
    first_column = getattr(section, 'FirstColumnNumber', None)
    last_column = getattr(section, 'LastColumnNumber', None)
    if None in (first_row, last_row, first_column, last_column):
        raise RuntimeError('Schedule table section has no readable bounds.')

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
    set_property(excel, 'Visible', False)
    set_property(excel, 'DisplayAlerts', False)
    workbook = None
    exports = []
    operation_failed = False
    # Open or create the container. Keep a new workbook in memory until every
    # schedule has exported successfully, so a failed export cannot leave an
    # incomplete workbook at the user-selected path.
    try:
        is_new_workbook = not os.path.isfile(workbook_path)
        if is_new_workbook:
            workbook = add_workbook(excel)
        else:
            workbook = open_workbook(excel, workbook_path)
        # Plan worksheet names. Convert Revit titles to unique Excel names so
        # duplicate titles cannot overwrite each other's export.
        raw_sheet_names = [worksheet_name_for_schedule(_element_name(schedule)) for schedule in schedules]
        sheet_names = uniquify_worksheet_names(raw_sheet_names)

        for schedule, sheet_name in zip(schedules, sheet_names):
            grid = _schedule_table_grid(schedule)
            if not has_exportable_cells(grid):
                raise ValueError(
                    'Selected schedule has no exportable cells: {}'.format(
                        _element_name(schedule)))
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
        if is_new_workbook:
            save_workbook(workbook, workbook_path)
        else:
            save_workbook(workbook)
        return exports
    except Exception:
        operation_failed = True
        raise
    finally:
        # INVARIANT: This function owns the export workbook and must release
        # Excel so the file is not left locked for the post-processing workbook.
        # The explicit Save/SaveAs above is the only persistence point.
        # Closing without saving prevents a failed mid-export from writing a
        # partially cleared container workbook. The shared helper still quits
        # Excel when the workbook-close COM call fails.
        close_excel_application(excel, workbook, suppress_errors=operation_failed)


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


def _com_collection_items(collection):
    """Return COM collection items whether the host exposes iteration or Item."""
    if collection is None:
        return []
    try:
        return [get_item(collection, index)
                for index in range(1, collection_count(collection) + 1)]
    except Exception:
        # Host-independent tests use ordinary Python lists; production COM
        # collections normally expose Count and Item through the facade above.
        try:
            return list(collection)
        except Exception:
            return []


def _make_query_refresh_foreground(workbook):
    """Disable background refresh for workbook query tables in this session.

    The setting is applied only to the read-only COM instance; it is never
    saved back into the analyst's workbook.
    """
    try:
        connections = get_property(workbook, 'Connections')
    except Exception:
        connections = None
    for connection in _com_collection_items(connections):
        for property_name in ('OLEDBConnection', 'ODBCConnection'):
            try:
                set_property(get_property(connection, property_name), 'BackgroundQuery', False)
            except Exception:
                pass
    for worksheet in _com_collection_items(worksheet_collection(workbook)):
        for collection_name in ('QueryTables', 'ListObjects'):
            try:
                collection = get_property(worksheet, collection_name)
            except Exception:
                collection = None
            for source in _com_collection_items(collection):
                try:
                    try:
                        query_table = get_property(source, 'QueryTable')
                    except Exception:
                        query_table = source
                    set_property(query_table, 'BackgroundQuery', False)
                except Exception:
                    pass


def _query_refresh_is_running(workbook):
    """Return whether a workbook query still reports an active refresh."""
    try:
        connections = get_property(workbook, 'Connections')
    except Exception:
        connections = None
    for connection in _com_collection_items(connections):
        for property_name in ('OLEDBConnection', 'ODBCConnection'):
            try:
                if get_property(get_property(connection, property_name), 'Refreshing'):
                    return True
            except Exception:
                pass
    for worksheet in _com_collection_items(worksheet_collection(workbook)):
        for collection_name in ('QueryTables', 'ListObjects'):
            try:
                collection = get_property(worksheet, collection_name)
            except Exception:
                collection = None
            for source in _com_collection_items(collection):
                try:
                    try:
                        query_table = get_property(source, 'QueryTable')
                    except Exception:
                        query_table = source
                    if get_property(query_table, 'Refreshing'):
                        return True
                except Exception:
                    pass
    return False


def _wait_for_query_refresh(workbook):
    """Wait briefly for foreground workbook queries and fail before stale reads."""
    elapsed = 0.0
    while _query_refresh_is_running(workbook):
        if elapsed >= POST_PROCESSING_REFRESH_TIMEOUT_SECONDS:
            raise ValueError(
                'Post-processing workbook refresh did not finish within {} seconds. '
                'The Export sheet was not read to avoid a stale chart.'.format(
                    int(POST_PROCESSING_REFRESH_TIMEOUT_SECONDS)))
        time.sleep(POST_PROCESSING_REFRESH_POLL_SECONDS)
        elapsed += POST_PROCESSING_REFRESH_POLL_SECONDS


def _material_accuracy_check(workbook):
    """Inspect the approved material-classification cells for Excel #N/A errors.

    Excel's ``ISNA`` function distinguishes a true formula error from text that
    happens to look like ``#N/A``. The check is informational: callers always
    receive a result record and may continue the chart workflow.
    """
    result = {
        'status': 'completed',
        'sheet': MATERIAL_ACCURACY_WORKSHEET_NAME,
        'range': '{}{}:{}{}'.format(
            MATERIAL_ACCURACY_COLUMN, MATERIAL_ACCURACY_FIRST_ROW,
            MATERIAL_ACCURACY_COLUMN, MATERIAL_ACCURACY_LAST_ROW),
        'cells': [],
        'reason': '',
    }
    try:
        worksheet = _worksheet_by_name_ignoring_case(
            workbook, MATERIAL_ACCURACY_WORKSHEET_NAME)
        if worksheet is None:
            raise ValueError('Worksheet not found: {}'.format(
                MATERIAL_ACCURACY_WORKSHEET_NAME))
        for row_number in range(MATERIAL_ACCURACY_FIRST_ROW,
                                MATERIAL_ACCURACY_LAST_ROW + 1):
            address = '{}{}'.format(MATERIAL_ACCURACY_COLUMN, row_number)
            # ``ISNA`` is true only for Excel's #N/A error value, not for a
            # manually entered text value that resembles the error.
            if bool(call_method(worksheet, 'Evaluate', 'ISNA({})'.format(address))):
                result['cells'].append(address)
    except Exception as error:
        result['status'] = 'unavailable'
        result['reason'] = _safe_text(error) or 'The worksheet or range could not be read.'
    return result


def _read_export_rows(workbook_path, include_material_accuracy_check=False):
    """Refresh links and read rows from the post-processing Export sheet.

    Opens Excel read-only, updates external formula links in memory, and closes
    without saving after recalculation.

    Args:
        workbook_path: Path to the post-processing Excel workbook.
        include_material_accuracy_check: When true, also return the
            informational #N/A material-classification check result.

    Returns:
        Rectangular grid of Export worksheet values. When
        ``include_material_accuracy_check`` is true, returns a tuple of the
        grid and the check result.

    Raises:
        ValueError: Required Export worksheet is not present.
    """
    excel = _load_excel_application()
    set_property(excel, 'Visible', False)
    set_property(excel, 'DisplayAlerts', False)
    workbook = None
    operation_failed = False
    try:
        # ``UpdateLinks=3`` makes Excel update external formula links when the
        # post-processing workbook opens. Without it, a linked Export sheet can
        # retain its last saved (often zero) values even though this command has
        # just written fresh schedule data to the selected container workbook.
        workbook = open_workbook(
            excel, workbook_path, update_links=3, read_only=True)
        # Open the analyst workbook read-only. This command needs calculated
        # values but must not overwrite its formulas or source data.
        # The new post-processing workbook uses Power Query to read the three
        # DYN Out sheets from the container workbook. RefreshAll normally runs
        # those queries in the background; make the read-only session
        # foreground-only before refreshing so Export cannot be read while its
        # query inputs are temporarily blank.
        _make_query_refresh_foreground(workbook)
        call_method(workbook, 'RefreshAll')
        _wait_for_query_refresh(workbook)
        link_sources = call_method(workbook, 'LinkSources')
        if link_sources is not None:
            call_method(workbook, 'UpdateLink', link_sources)
        call_method(excel, 'CalculateUntilAsyncQueriesDone')
        call_method(excel, 'CalculateFullRebuild')
        # Read the workbook contract. The Export tab's first three columns map
        # source names to the GWP and material-volume chart values to render.
        worksheet = _worksheet_by_name(workbook, EXPORT_WORKSHEET_NAME)
        if worksheet is None:
            raise ValueError('Worksheet not found: {}'.format(EXPORT_WORKSHEET_NAME))

        used_range = get_property(worksheet, 'UsedRange')
        row_count = int(get_property(get_property(used_range, 'Rows'), 'Count'))
        column_count = int(get_property(get_property(used_range, 'Columns'), 'Count'))
        rows = _com_range_values_to_rows(get_property(used_range, 'Value2'), row_count, column_count)
        if include_material_accuracy_check:
            return rows, _material_accuracy_check(workbook)
        return rows
    except Exception:
        operation_failed = True
        raise
    finally:
        # INVARIANT: This reader never saves analyst-owned workbook changes.
        # The shared helper quits Excel even if Close(False) fails, avoiding a
        # lingering hidden process and a locked analyst workbook.
        close_excel_application(excel, workbook, suppress_errors=operation_failed)


# Managed Revit chart placement
# ------------------------------------------------------------------
def _sync_to_central_sheet(document):
    """Return the uniquely named SYNC TO CENTRAL sheet, when it exists.

    The tool never creates a sheet or guesses between duplicate sheet names.
    """
    matches = []
    for sheet in DB.FilteredElementCollector(document).OfClass(DB.ViewSheet):
        if _is_target_sheet_name(_element_name(sheet)):
            matches.append(sheet)
    if len(matches) != 1:
        if not matches:
            forms.alert(
                'Sheet not found: {}. Create it outside this command, then run again.'.format(
                    TARGET_SHEET_NAME),
                title=COMMAND_TITLE,
                warn_icon=True)
        else:
            forms.alert(
                'Multiple sheets are named {}. Rename the duplicates before running again.'.format(
                    TARGET_SHEET_NAME),
                title=COMMAND_TITLE,
                warn_icon=True)
        return None
    return matches[0]


def _is_active_sheet(document, sheet):
    """Return whether the command is currently running on the target sheet."""
    try:
        return _element_id_value(document.ActiveView.Id) == _element_id_value(sheet.Id)
    except Exception:
        return False


def _chart_png_path(chart_output_folder, chart_kind):
    """Return the generated PNG location for a managed chart.

    Args:
        chart_output_folder: New command-owned folder for the current run.
        chart_kind: ``gwp`` or ``volume`` chart identifier.

    Returns:
        Absolute PNG path in ``chart_output_folder``.

    Raises:
        ValueError: ``chart_kind`` is not a supported chart identifier.

    Chart images are saved in a timestamped folder beside the selected
    post-processing workbook so the project team can access the exact
    rendered graphics without replacing pre-existing files.
    """
    try:
        filename = CHART_IMAGE_FILENAMES[chart_kind]
    except KeyError:
        raise ValueError('Unsupported chart kind: {}'.format(chart_kind))
    return os.path.join(chart_output_folder, filename)


def _create_chart_output_folder(post_processing_workbook):
    """Create and return a unique generated-chart folder for this run.

    Args:
        post_processing_workbook: Path to the selected analyst workbook.

    Returns:
        New timestamped folder below the workbook's ``Carbon GWP Pull Charts``
        directory.

    Raises:
        OSError: The command cannot create the output folder.

    The folder is deliberately unique per run. Re-rendering never deletes or
    overwrites a file chosen or created by a project user.
    """
    parent_folder = os.path.dirname(post_processing_workbook)
    base_folder = os.path.join(parent_folder, CHART_OUTPUT_FOLDER_NAME)
    run_name = time.strftime('%Y%m%d-%H%M%S')
    run_folder = os.path.join(base_folder, run_name)
    suffix = 2
    while os.path.exists(run_folder):
        run_folder = os.path.join(base_folder, '{}-{}'.format(run_name, suffix))
        suffix += 1
    os.makedirs(run_folder)
    return run_folder


def _same_workbook_path(first_path, second_path):
    """Return whether two workbook selections identify the same file.

    Args:
        first_path: First selected workbook path.
        second_path: Second selected workbook path.

    Returns:
        ``True`` when normalized absolute paths are equal.
    """
    return os.path.normcase(os.path.abspath(first_path)) == os.path.normcase(
        os.path.abspath(second_path))


def _chart_slice_limit_exceeded(chart_results):
    """Return chart names whose legends exceed the supported render limit.

    Args:
        chart_results: Chart dictionaries containing ``name`` and ``slices``.

    Returns:
        Names of charts with more than ``MAX_CHART_SLICE_COUNT`` slices.
    """
    return [chart['name'] for chart in chart_results
            if len(chart['slices']) > MAX_CHART_SLICE_COUNT]


# pyRevit output reporting
# ------------------------------------------------------------------
def _print_report(output, metadata, exports, chart_results, material_accuracy_check=None):
    """Render a Carbon GWP result summary in the pyRevit output window.

    Writes report headings and tables to ``output`` without modifying the
    Revit document or either workbook.

    Args:
        output: pyRevit output window for this command run.
        metadata: Selected workbooks, target sheet, and chart update metadata.
        exports: Schedule export metadata dictionaries.
        chart_results: Per-measure chart dictionaries containing slices and
            skipped Export rows.
        material_accuracy_check: Optional informational #N/A check result.
    """
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Export container workbook: `{}`'.format(metadata['export_workbook']))
    output.print_md('Post-processing workbook: `{}`'.format(metadata['post_processing_workbook']))
    output.print_md('Target sheet: `{}`'.format(metadata['target_sheet']))
    if metadata.get('chart_output_folder'):
        output.print_md('Generated chart folder: `{}`'.format(
            metadata['chart_output_folder']))
    # Report only populated sections. Empty headings add noise, while populated
    # tables show the selected schedules, skipped rows, and write outcomes.
    if exports:
        output.print_md('## Schedule Exports')
        output.print_table(
            [[item['schedule_name'], item['worksheet_name'], item['rows'], item['columns']] for item in exports],
            columns=['Schedule', 'Worksheet', 'Rows', 'Columns'])
    for chart in chart_results:
        output.print_md('## {} Chart'.format(chart['name']))
        output.print_md('Chart slices: {}'.format(len(chart['slices'])))
        output.print_md(
            'Chart total: {}'.format(format_chart_amount(chart['total'], chart['unit'])))
        if chart.get('action'):
            output.print_md('Managed chart: {}'.format(chart['action']))
        if chart['slices']:
            output.print_table(
                [[item['row'], item['source_name'], item['display_label'],
                  format_chart_table_amount(item['value'])]
                 for item in chart['slices']],
                columns=['Row', 'Source', 'Material', chart['unit']])
        if chart['skipped']:
            output.print_md('### Skipped Export Rows')
            output.print_table(
                [[item.get('row'), item.get('source_name', ''),
                  item.get('display_label', ''), item.get('reason')]
                 for item in chart['skipped']],
                columns=['Row', 'Source', 'Material', 'Reason'])
    if material_accuracy_check:
        output.print_md('## Material Accuracy Check')
        if material_accuracy_check['status'] == 'unavailable':
            output.print_md('Check not completed: {}'.format(
                material_accuracy_check['reason']))
        elif material_accuracy_check['cells']:
            output.print_md(
                'Excel `#N/A` errors found in `{}`:'.format(
                    material_accuracy_check['range']))
            output.print_table(
                [[material_accuracy_check['sheet'], cell]
                 for cell in material_accuracy_check['cells']],
                columns=['Worksheet', 'Cell'])
        else:
            output.print_md(
                'Completed: no Excel `#N/A` errors found in `{}`.'.format(
                    material_accuracy_check['range']))


def _show_material_accuracy_warning(material_accuracy_check,
                                    chart_update_completed=True):
    """Show a non-blocking material-accuracy warning after reporting results."""
    if material_accuracy_check['status'] == 'unavailable':
        forms.alert(
            'The Material Accuracy check was not completed, please review the '
            'Material Breakdown table in Excel',
            title=COMMAND_TITLE,
            warn_icon=True)
    elif material_accuracy_check['cells']:
        if chart_update_completed:
            message = (
                'The chart update completed, but {} #N/A result(s) were found in '
                '{}!{}. Review the pyRevit report for affected cells.')
        else:
            message = (
                '{} #N/A result(s) were found in {}!{}. Review the pyRevit '
                'report for affected cells.')
        forms.alert(
            message.format(
                len(material_accuracy_check['cells']),
                material_accuracy_check['sheet'],
                material_accuracy_check['range']),
            title=COMMAND_TITLE,
            warn_icon=True)


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
# ==================================================================
# Main
# ------------------------------------------------------------------
def main():
    """Run the interactive Carbon GWP export and managed-chart workflow."""
    output = script.get_output()
    document = revit.doc
    target_sheet = _sync_to_central_sheet(document)
    if target_sheet is None:
        return
    if not _is_active_sheet(document, target_sheet):
        forms.alert(
            'Open the {} sheet, then run {} again.'.format(TARGET_SHEET_NAME, COMMAND_TITLE),
            title=COMMAND_TITLE,
            warn_icon=True)
        return
    # The titleblock anchors both chart images on every run. GWP aligns its
    # top-left to the titleblock top-right; volume starts at the GWP bottom-left.
    # Collect required user input. Later steps need all three schedules and both
    # workbooks, so cancellation ends the run before external work begins.
    schedules = _select_schedules(document)
    if not schedules:
        return
    # Select the two workbook roles. The export workbook receives schedule
    # tabs; the post-processing workbook calculates values for chart rendering.
    export_workbook = _pick_workbook(
        EXPORT_WORKBOOK_PICKER_TITLE,
        _model_workbook_folder(document, DEFAULT_EXPORT_CONTAINER_PATH))
    if not export_workbook:
        return
    post_processing_workbook = _pick_workbook(
        POST_PROCESSING_WORKBOOK_PICKER_TITLE,
        os.path.dirname(export_workbook))
    if not post_processing_workbook:
        return
    if _same_workbook_path(export_workbook, post_processing_workbook):
        forms.alert(
            'Select different workbooks for schedule export and post-processing. '
            'The export workbook will have its DYN Out worksheets replaced.',
            title=COMMAND_TITLE,
            warn_icon=True)
        return
    if not os.path.isfile(post_processing_workbook):
        forms.alert('Post-processing workbook not found:\n{}'.format(post_processing_workbook),
                    title=COMMAND_TITLE, warn_icon=True)
        return
    # Export and refresh external data before a Revit transaction, keeping
    # workbook failures separate from model changes.
    output.print_md('Preparing Carbon GWP Pull...')
    output.print_md('Exporting selected schedules to the export workbook...')
    exports = _export_schedules_to_workbook(export_workbook, schedules)
    output.print_md('Refreshing and calculating the post-processing workbook...')
    export_rows, material_accuracy_check = _read_export_rows(
        post_processing_workbook, include_material_accuracy_check=True)
    gwp_slices, gwp_skipped = chart_slices_from_export_rows(export_rows, 1, 'GWP')
    volume_slices, volume_skipped = chart_slices_from_export_rows(
        export_rows, 2, 'material volume')

    metadata = {
        'export_workbook': export_workbook,
        'post_processing_workbook': post_processing_workbook,
        'target_sheet': TARGET_SHEET_NAME,
    }
    chart_results = [
        {
            'kind': 'gwp',
            'name': 'Embodied Carbon',
            'caption': 'Total GWP',
            'unit': GWP_CHART_UNIT,
            'slices': gwp_slices,
            'skipped': gwp_skipped,
        },
        {
            'kind': 'volume',
            'name': 'Material Volume',
            'caption': 'Total Volume',
            'unit': VOLUME_CHART_UNIT,
            'slices': volume_slices,
            'skipped': volume_skipped,
        },
    ]
    for chart in chart_results:
        chart['total'] = chart_total(chart['slices'])
    missing_charts = [chart['name'] for chart in chart_results if not chart['slices']]
    if missing_charts:
        _print_report(
            output, metadata, exports, chart_results, material_accuracy_check)
        _show_material_accuracy_warning(
            material_accuracy_check, chart_update_completed=False)
        forms.alert(
            'No positive numeric values were found for {} on the Export worksheet. '
            'Review the pyRevit output for skipped rows.'.format(', '.join(missing_charts)),
            title=COMMAND_TITLE,
            warn_icon=True)
        return

    oversized_charts = _chart_slice_limit_exceeded(chart_results)
    if oversized_charts:
        forms.alert(
            '{} has more than {} material rows. Reduce or group the Export '
            'worksheet rows before rendering a readable chart.'.format(
                ', '.join(oversized_charts), MAX_CHART_SLICE_COUNT),
            title=COMMAND_TITLE,
            warn_icon=True)
        return

    # Create a new tool-owned output folder before rendering. A failed render
    # can leave only partial generated output; it cannot delete an earlier file.
    output.print_md('Rendering chart PNGs...')
    chart_output_folder = _create_chart_output_folder(post_processing_workbook)
    metadata['chart_output_folder'] = chart_output_folder
    image_paths = {}
    # Render before the Revit transaction. A drawing failure leaves both
    # existing managed charts unchanged and preserves prior generated PNGs.
    for chart in chart_results:
        image_path = _chart_png_path(chart_output_folder, chart['kind'])
        image_paths[chart['kind']] = image_path
        render_chart_png(chart['slices'], image_path, chart['caption'], chart['unit'])
    # INVARIANT: Import/reload is the only Revit model mutation. Revit rolls
    # this transaction back if either image placement or reload cannot complete.
    output.print_md('Updating managed charts on {}...'.format(TARGET_SHEET_NAME))
    with revit.Transaction('Carbon GWP Pull - Update Managed Charts'):
        gwp_chart = chart_results[0]
        volume_chart = chart_results[1]
        titleblock_point = titleblock_top_right(document, target_sheet, DB)
        chart_action, image_instance = create_or_reload_chart(
            document, target_sheet, titleblock_point,
            image_paths[gwp_chart['kind']], DB, gwp_chart['kind'])
        gwp_chart['action'] = chart_action
        gwp_chart['instance_id'] = _element_id_value(image_instance.Id)
        gwp_image_instance = image_instance
        chart_action, image_instance = create_or_reload_chart(
            document, target_sheet, image_bottom_left(
                gwp_image_instance, target_sheet, DB),
            image_paths[volume_chart['kind']], DB, volume_chart['kind'])
        volume_chart['action'] = chart_action
        volume_chart['instance_id'] = _element_id_value(image_instance.Id)
    _print_report(output, metadata, exports, chart_results, material_accuracy_check)
    _show_material_accuracy_warning(material_accuracy_check)


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
