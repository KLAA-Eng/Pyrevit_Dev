# -*- coding: utf-8 -*-
"""Explicit, IronPython-safe boundary for Microsoft Excel COM.

Revit 2025+ can expose Excel PIA objects to IronPython as raw
``System.__ComObject`` instances. A raw wrapper can make a method look like a
property (for example ``Workbook.Close``), so command code must never infer
member usage from normal attribute access. Use the explicit operations below.
"""
from __future__ import unicode_literals


class ExcelComCompatibilityError(RuntimeError):
    """Raised when an Excel PIA or IDispatch operation cannot be completed."""


def _excel_interop():
    """Load and return the installed Microsoft Excel primary interop assembly."""
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')
    from Microsoft.Office.Interop import Excel
    return Excel


def _missing_value():
    """Return the COM sentinel for an omitted optional argument."""
    try:
        from System import Type
        return Type.Missing
    except Exception:
        return None


def _is_raw_com_object(value):
    """Return whether *value* is the ambiguous .NET COM runtime wrapper."""
    try:
        return value.GetType().FullName == 'System.__ComObject'
    except Exception:
        return False


def _arguments(values):
    """Convert Python values to the Object array required by IDispatch."""
    from System import Array, Object
    return Array[Object](list(values))


def _invoke_member(target, member_name, arguments):
    """Invoke a public IDispatch method on a raw COM wrapper."""
    from System.Reflection import BindingFlags
    flags = (BindingFlags.InvokeMethod | BindingFlags.Public |
             BindingFlags.Instance | BindingFlags.OptionalParamBinding)
    return target.GetType().InvokeMember(
        member_name, flags, None, target, _arguments(arguments))


def _get_property(target, property_name, arguments=None):
    """Read a public IDispatch property from a raw COM wrapper."""
    from System.Reflection import BindingFlags
    flags = BindingFlags.GetProperty | BindingFlags.Public | BindingFlags.Instance
    return target.GetType().InvokeMember(
        property_name, flags, None, target, _arguments(arguments or []))


def _set_property(target, property_name, value):
    """Set a public IDispatch property on a raw COM wrapper."""
    from System.Reflection import BindingFlags
    # .NET 8 rejects a flag set containing both SetProperty and
    # PutDispProperty.  These commands set scalar Excel properties, for which
    # SetProperty is the correct IDispatch operation.  PutDispProperty is only
    # needed for object-reference assignment and must not be combined here.
    flags = BindingFlags.SetProperty | BindingFlags.Public | BindingFlags.Instance
    return target.GetType().InvokeMember(
        property_name, flags, None, target, _arguments([value]))


def get_property(target, property_name):
    """Return a named property through PIA or explicit IDispatch.

    Pass the returned COM value back to another public helper; do not chain
    ordinary Python COM attributes or collection indexing from command code.
    """
    if _is_raw_com_object(target):
        return _get_property(target, property_name)
    return getattr(target, property_name)


def get_indexed_property(target, property_name, *indices):
    """Return a parameterized property through PIA or IDispatch.

    Excel ``Worksheet.Range`` is the important case: it looks callable through
    the PIA but is a parameterized property in IDispatch, so it must use
    ``GetProperty`` rather than ``InvokeMethod`` for a raw COM wrapper.
    """
    if _is_raw_com_object(target):
        return _get_property(target, property_name, indices)
    return getattr(target, property_name)(*indices)


def set_property(target, property_name, value):
    """Set a named property through PIA or explicit IDispatch."""
    if _is_raw_com_object(target):
        return _set_property(target, property_name, value)
    setattr(target, property_name, value)


def call_method(target, method_name, *arguments):
    """Call a named method through PIA or explicit IDispatch."""
    if _is_raw_com_object(target):
        return _invoke_member(target, method_name, arguments)
    return getattr(target, method_name)(*arguments)


def get_item(collection, *indices):
    """Return an indexed COM collection item through PIA or IDispatch."""
    if _is_raw_com_object(collection):
        try:
            return _get_property(collection, 'Item', indices)
        except Exception as property_error:
            # Excel collections are inconsistent: some expose Item as a
            # property-get and others only bind it as an IDispatch method.
            # Try the documented Item method only after the property path.
            try:
                return _invoke_member(collection, 'Item', indices)
            except Exception as method_error:
                raise ExcelComCompatibilityError(
                    'Excel collection Item failed through property and method '
                    'dispatch. Property error: {}; method error: {}'.format(
                        property_error, method_error))
    if len(indices) == 1:
        return collection[indices[0]]
    return collection[tuple(indices)]


def collection_count(collection):
    """Return the integer count for an Excel collection."""
    return int(get_property(collection, 'Count'))


def create_excel_application():
    """Create and configure a hidden Excel application using the installed PIA."""
    excel = _excel_interop().ApplicationClass()
    set_property(excel, 'Visible', False)
    set_property(excel, 'DisplayAlerts', False)
    return excel


def _disable_automation_macros(excel):
    """Force-disable automation macros and return the prior setting if available."""
    try:
        previous_setting = get_property(excel, 'AutomationSecurity')
    except Exception:
        return None
    import clr
    clr.AddReference('Office')
    from Microsoft.Office.Core import MsoAutomationSecurity
    set_property(excel, 'AutomationSecurity',
                 MsoAutomationSecurity.msoAutomationSecurityForceDisable)
    return previous_setting


def _restore_automation_macros(excel, previous_setting):
    """Restore macro automation state only when this module changed it."""
    if previous_setting is not None:
        set_property(excel, 'AutomationSecurity', previous_setting)


def open_workbook(excel, workbook_path, update_links=None, read_only=None):
    """Open a workbook with macros disabled and explicit optional arguments."""
    workbooks = get_property(excel, 'Workbooks')
    missing = _missing_value()
    arguments = [workbook_path,
                 update_links if update_links is not None else missing,
                 read_only if read_only is not None else missing]
    arguments.extend([missing] * 12)
    previous_setting = _disable_automation_macros(excel)
    try:
        if _is_raw_com_object(workbooks):
            return _invoke_member(workbooks, 'Open', arguments)
        options = {}
        if update_links is not None:
            options['UpdateLinks'] = update_links
        if read_only is not None:
            options['ReadOnly'] = read_only
        return workbooks.Open(workbook_path, **options)
    except Exception as error:
        raise ExcelComCompatibilityError('Excel Workbooks.Open failed: {}'.format(error))
    finally:
        _restore_automation_macros(excel, previous_setting)


def add_workbook(excel):
    """Create a workbook through the public ``Workbooks.Add`` member."""
    workbooks = get_property(excel, 'Workbooks')
    try:
        if _is_raw_com_object(workbooks):
            return _invoke_member(workbooks, 'Add', [_missing_value()])
        return workbooks.Add()
    except Exception as error:
        raise ExcelComCompatibilityError('Excel Workbooks.Add failed: {}'.format(error))


def worksheet_collection(workbook):
    """Return the workbook worksheet collection through the explicit boundary."""
    return get_property(workbook, 'Worksheets')


def worksheet_at(workbook, index):
    """Return a one-based worksheet item."""
    return get_item(worksheet_collection(workbook), index)


def add_worksheet(workbook, after=None):
    """Add a worksheet, optionally after a known worksheet."""
    worksheets = worksheet_collection(workbook)
    if _is_raw_com_object(worksheets):
        missing = _missing_value()
        return _invoke_member(worksheets, 'Add', [missing, after, missing, missing])
    if after is None:
        return worksheets.Add()
    return worksheets.Add(After=after)


def range_at(worksheet, address):
    """Return a worksheet range by address."""
    return get_indexed_property(worksheet, 'Range', address)


def pivot_cache_collection(workbook):
    """Return a workbook PivotCaches collection through its correct COM shape."""
    if _is_raw_com_object(workbook):
        try:
            return get_property(workbook, 'PivotCaches')
        except Exception as property_error:
            try:
                return _invoke_member(workbook, 'PivotCaches', [])
            except Exception as method_error:
                raise ExcelComCompatibilityError(
                    'Excel Workbook.PivotCaches failed through property and '
                    'method dispatch. Property error: {}; method error: {}'.format(
                        property_error, method_error))
    return call_method(workbook, 'PivotCaches')


def chart_object_collection(worksheet):
    """Return a worksheet ChartObjects collection through its correct COM shape."""
    if _is_raw_com_object(worksheet):
        try:
            return get_property(worksheet, 'ChartObjects')
        except Exception as property_error:
            try:
                return _invoke_member(worksheet, 'ChartObjects', [])
            except Exception as method_error:
                raise ExcelComCompatibilityError(
                    'Excel Worksheet.ChartObjects failed through property and '
                    'method dispatch. Property error: {}; method error: {}'.format(
                        property_error, method_error))
    return call_method(worksheet, 'ChartObjects')


def add_list_object(worksheet, source_range=None, has_headers=1):
    """Create a worksheet table with explicit COM optional arguments."""
    source_range = source_range or get_property(worksheet, 'UsedRange')
    list_objects = get_property(worksheet, 'ListObjects')
    missing = _missing_value()
    return call_method(
        list_objects, 'Add', 1, source_range, missing, has_headers, missing)


def create_pivot_cache(workbook, source_range):
    """Create a database PivotCache with its optional Version argument omitted."""
    source_data = source_range
    if _is_raw_com_object(source_range):
        # Excel documents that a Range object can cause an unexpected type
        # mismatch when creating a PivotCache.  An external A1 reference is
        # the stable COM-neutral representation for a raw range wrapper.
        missing = _missing_value()
        source_data = _get_property(
            source_range, 'Address',
            [missing, missing, missing, True, missing])
    return call_method(
        pivot_cache_collection(workbook), 'Create', 1, source_data, _missing_value())


def add_chart_object(worksheet, left, top, width, height):
    """Add a chart object with Excel's expected single-precision geometry."""
    return call_method(
        chart_object_collection(worksheet), 'Add', float(left), float(top),
        float(width), float(height))


def cell_at(worksheet, row_index, column_index):
    """Return a worksheet cell by one-based row and column indexes."""
    return get_item(get_property(worksheet, 'Cells'), row_index, column_index)


def save_workbook(workbook, workbook_path=None):
    """Save a workbook, using ``SaveAs`` only when a path is supplied."""
    if workbook_path is None:
        return call_method(workbook, 'Save')
    return call_method(workbook, 'SaveAs', workbook_path)


def close_excel_application(excel, workbook=None, suppress_errors=False):
    """Close an optional workbook and always request Excel exit.

    ``suppress_errors`` preserves an earlier command failure while both cleanup
    operations are attempted. The returned list can be added to a report.
    """
    errors = []
    if workbook is not None:
        try:
            call_method(workbook, 'Close', False)
        except Exception as error:
            errors.append('Workbook.Close: {}'.format(error))
    try:
        call_method(excel, 'Quit')
    except Exception as error:
        errors.append('Excel.Quit: {}'.format(error))
    if errors and not suppress_errors:
        raise ExcelComCompatibilityError('; '.join(errors))
    return errors
