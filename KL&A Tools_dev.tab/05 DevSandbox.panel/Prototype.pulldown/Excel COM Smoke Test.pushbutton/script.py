# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Excel COM Smoke Test"
__version__ = "v0.2"


import glob
import hashlib
import os
import sys
import tempfile
import traceback
import uuid

from pyrevit import forms, revit, script


def _extension_root(path):
    """Return the owning extension folder for a nested pyRevit script path."""
    current = os.path.abspath(path)
    while True:
        if current.lower().endswith('.extension'):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


LIB_DIR = os.path.join(_extension_root(__file__), 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from excel_com import (
    add_chart_object, add_list_object, add_workbook, add_worksheet, call_method,
    close_excel_application, collection_count, create_excel_application,
    create_pivot_cache, get_item, get_property, open_workbook, range_at,
    save_workbook, set_property, worksheet_collection,
)

SMOKE_ROOT_NAME = 'KLCodeExcelComSmoke'
FILE_PREFIX = 'KLCode_Excel_Com_Smoke_'


def _smoke_paths(token=None, temp_root=None):
    """Create a unique, verifiably owned workbook and CSV path description."""
    token = token or uuid.uuid4().hex
    temp_root = os.path.abspath(temp_root or tempfile.gettempdir())
    root = os.path.abspath(os.path.join(temp_root, SMOKE_ROOT_NAME))
    run_dir = os.path.abspath(os.path.join(root, token))
    workbook_path = os.path.abspath(os.path.join(
        run_dir, '{}{}.xlsx'.format(FILE_PREFIX, token)))
    csv_path = os.path.abspath(os.path.join(
        run_dir, '{}{}.csv'.format(FILE_PREFIX, token)))
    return {'token': token, 'root': root, 'run_dir': run_dir,
            'workbook_path': workbook_path, 'csv_path': csv_path}


def _is_owned_path(paths, path):
    """Return whether *path* is an exact current-run disposable asset."""
    path = os.path.abspath(path)
    return (
        os.path.dirname(paths['run_dir']) == paths['root'] and
        os.path.dirname(path) == paths['run_dir'] and
        path in (paths['workbook_path'], paths['csv_path']) and
        path.startswith(paths['run_dir'] + os.sep))


def _prepare_paths(paths):
    """Create only the owned per-run folder; never overwrite a prior run."""
    if not (_is_owned_path(paths, paths['workbook_path']) and
            _is_owned_path(paths, paths['csv_path'])):
        raise RuntimeError('Smoke-test path ownership check failed.')
    if os.path.exists(paths['run_dir']) or os.path.exists(paths['workbook_path']):
        raise RuntimeError('Smoke-test path unexpectedly already exists.')
    if not os.path.isdir(paths['root']):
        os.makedirs(paths['root'])
    os.mkdir(paths['run_dir'])
    with open(paths['csv_path'], 'w') as csv_file:
        csv_file.write('Category,Amount\nConcrete,12\nSteel,5\n')


def _runtime_type(value):
    """Return a stable type label without assuming normal COM projection."""
    try:
        return value.GetType().FullName
    except Exception:
        return type(value).__name__


def _error_detail(error):
    """Include a .NET inner exception when COM wraps the useful cause."""
    detail = '{}: {}'.format(type(error).__name__, error)
    try:
        inner = getattr(error, 'InnerException', None)
        if inner is None:
            inner = error.clsException.InnerException
        if inner is not None:
            detail += ' | Inner: {}: {}'.format(
                inner.GetType().FullName, inner.Message)
    except Exception:
        pass
    return detail


def _record(results, name, action):
    """Run one facade operation and retain its success or failure evidence."""
    try:
        value = action()
        results.append([name, 'PASS', _runtime_type(value), ''])
        return value
    except Exception as error:
        results.append([name, 'FAIL', '', _error_detail(error)])
        return None


def _probe_excel_reference(results):
    """Report the first Excel assembly lookup without changing facade behavior."""
    try:
        import clr
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception as error:
        row = ['Excel interop name lookup', 'INFO', '',
               'First lookup failed: {}'.format(_error_detail(error))]
    else:
        row = ['Excel interop name lookup', 'PASS', '',
               'Short-name reference loaded.']
    results.append(row)
    return row


def _script_fingerprint():
    """Identify the exact smoke script that this Revit process executed."""
    try:
        with open(__file__, 'rb') as source:
            return hashlib.sha256(source.read()).hexdigest()
    except Exception as error:
        return 'unavailable: {}'.format(_error_detail(error))


def _pia_file_paths():
    """Find Excel PIA files in a few common Office and GAC locations."""
    filename = 'Microsoft.Office.Interop.Excel.dll'
    paths = []
    for root in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')):
        if not root:
            continue
        office = os.path.join(root, 'Microsoft Office', 'root')
        paths.append(os.path.join(
            office, 'vfs', 'ProgramFilesX86', 'Microsoft Office',
            'Office16', 'DCF', filename))
        paths.extend(glob.glob(os.path.join(
            office, 'Office16', 'ADDINS', 'PowerPivot Excel Add-in*', filename)))
    windows = os.environ.get('WINDIR')
    if windows:
        paths.extend(glob.glob(os.path.join(
            windows, 'Microsoft.NET', 'assembly', 'GAC_MSIL',
            'Microsoft.Office.Interop.Excel', '*', filename)))
    return sorted(set(path for path in paths if os.path.isfile(path)))


def _report_pia_files(results):
    """Read PIA file identities without loading them into Revit."""
    paths = _pia_file_paths()
    if not paths:
        results.append(['Excel interop files on disk', 'INFO', '',
                        'None found in the checked Office and GAC locations; '
                        'other installation paths remain possible.'])
        return
    try:
        from System.Reflection import AssemblyName
    except Exception as error:
        results.append(['Excel interop files on disk', 'INFO', '',
                        'Could not inspect file identities: {}'.format(
                            _error_detail(error))])
        return
    for path in paths:
        try:
            identity = AssemblyName.GetAssemblyName(path).FullName
        except Exception as error:
            identity = 'Unreadable: {}'.format(_error_detail(error))
        results.append(['Excel interop file on disk', 'INFO', '',
                        'Identity: {} | Path: {}'.format(identity, path)])


def _report_loaded_excel_assemblies(results):
    """Report the identity and location of Excel PIAs loaded in this process."""
    try:
        from System import AppDomain
        assemblies = [assembly for assembly in AppDomain.CurrentDomain.GetAssemblies()
                      if assembly.GetName().Name == 'Microsoft.Office.Interop.Excel']
        if not assemblies:
            results.append(['Loaded Excel interop assembly', 'INFO', '',
                            'No Excel interop assembly is loaded in this Revit process.'])
            return
        for assembly in assemblies:
            try:
                location = assembly.Location or '(no file location)'
            except Exception as error:
                location = 'Unavailable: {}'.format(_error_detail(error))
            results.append(['Loaded Excel interop assembly', 'PASS',
                            _runtime_type(assembly),
                            'Identity: {} | Location: {}'.format(
                                assembly.FullName, location)])
    except Exception as error:
        results.append(['Loaded Excel interop assembly', 'INFO', '',
                        'Could not inspect loaded assemblies: {}'.format(
                            _error_detail(error))])


def _cleanup(paths, excel, workbook, results, retain_assets):
    """Release Excel first, then delete only proven-owned successful-run assets."""
    cleanup_errors = []
    if excel is not None:
        cleanup_errors = close_excel_application(
            excel, workbook, suppress_errors=True)
    for error in cleanup_errors:
        results.append(['Excel cleanup', 'FAIL', '', error])
    if retain_assets or cleanup_errors:
        return False
    for path in (paths['workbook_path'], paths['csv_path']):
        if os.path.isfile(path) and _is_owned_path(paths, path):
            try:
                os.remove(path)
            except Exception as error:
                results.append(['Delete {}'.format(os.path.basename(path)), 'FAIL', '', str(error)])
                return False
    try:
        if os.path.isdir(paths['run_dir']) and not os.listdir(paths['run_dir']):
            os.rmdir(paths['run_dir'])
    except Exception as error:
        results.append(['Delete run folder', 'FAIL', '', str(error)])
        return False
    results.append(['Owned temp cleanup', 'PASS', '', ''])
    return True


def main():
    """Exercise the shared facade without accessing or changing the Revit model."""
    output = script.get_output()
    results = []
    paths = _smoke_paths()
    excel = None
    workbook = None
    reopen_excel = None
    reopened = None
    retain_assets = False
    try:
        _prepare_paths(paths)
        output.print_md('# {}'.format(__title__))
        output.print_md('Revit: {} | Document access: none'.format(
            getattr(revit.doc.Application, 'VersionNumber', 'Unknown')))
        output.print_md('Smoke script version: {}'.format(__version__))
        output.print_md('Smoke script path: {}'.format(os.path.abspath(__file__)))
        output.print_md('Smoke script SHA-256: {}'.format(_script_fingerprint()))
        lookup_row = _probe_excel_reference(results)
        output.print_md('Excel interop name lookup: {} | {}'.format(
            lookup_row[1], lookup_row[3]))
        excel = _record(results, 'Create hidden Excel application', create_excel_application)
        _report_loaded_excel_assemblies(results)
        _report_pia_files(results)
        if excel is None:
            retain_assets = True
            return
        _record(results, 'Read application Visible', lambda: get_property(excel, 'Visible'))
        _record(results, 'Read application DisplayAlerts', lambda: get_property(excel, 'DisplayAlerts'))
        workbook = _record(results, 'Workbooks.Add', lambda: add_workbook(excel))
        if workbook is None:
            retain_assets = True
            return
        sheets = _record(results, 'Get Worksheets collection', lambda: worksheet_collection(workbook))
        first = _record(results, 'Worksheets.Item(1)', lambda: get_item(sheets, 1))
        _record(results, 'Worksheets.Count', lambda: collection_count(sheets))
        _record(results, 'Rename first worksheet', lambda: set_property(first, 'Name', 'Facade Data'))
        second = _record(results, 'Worksheets.Add(After)', lambda: add_worksheet(workbook, after=first))
        _record(results, 'Rename second worksheet', lambda: set_property(second, 'Name', 'Facade Query'))
        _record(results, 'Set Facade Data A1', lambda: set_property(range_at(first, 'A1'), 'Value2', 'Facade marker'))
        marker = _record(results, 'Read Facade Data A1', lambda: get_property(range_at(first, 'A1'), 'Value2'))
        if marker != 'Facade marker':
            results.append(['Validate Facade Data A1', 'FAIL', '', 'Expected Facade marker, got {}'.format(marker)])
        else:
            results.append(['Validate Facade Data A1', 'PASS', '', ''])
        _record(results, 'Set Facade Data B1 formula', lambda: set_property(range_at(first, 'B1'), 'Formula', '=1+1'))
        _record(results, 'Read UsedRange', lambda: get_property(first, 'UsedRange'))
        created_query = _record(results, 'CSV QueryTables.Add', lambda: call_method(
            get_property(second, 'QueryTables'), 'Add', 'TEXT;{}'.format(paths['csv_path']), range_at(second, 'A1')))
        query = _record(results, 'Get first QueryTable', lambda: get_item(get_property(second, 'QueryTables'), 1))
        if query is None:
            query = created_query
            if query is not None:
                results.append(['Use returned QueryTable', 'PASS', _runtime_type(query),
                                'Collection Item was unavailable.'])
        if query is not None:
            _record(results, 'Configure text query', lambda: set_property(query, 'TextFileCommaDelimiter', True))
            _record(results, 'Refresh text query', lambda: call_method(query, 'Refresh', False))
        table_sheet = _record(results, 'Add table worksheet', lambda: add_worksheet(workbook, after=second))
        if table_sheet is not None:
            _record(results, 'Rename table worksheet', lambda: set_property(
                table_sheet, 'Name', 'Facade Table'))
            _record(results, 'Set table headers', lambda: set_property(
                range_at(table_sheet, 'A1'), 'Value2', 'Category'))
            _record(results, 'Set table value', lambda: set_property(
                range_at(table_sheet, 'A2'), 'Value2', 'Concrete'))
            _record(results, 'Create ListObject', lambda: add_list_object(table_sheet))
        pivot_sheet = _record(results, 'Add pivot worksheet', lambda: add_worksheet(workbook, after=second))
        if pivot_sheet is not None:
            _record(results, 'Create PivotCache', lambda: create_pivot_cache(
                workbook, get_property(second, 'UsedRange')))
        _record(results, 'Create ChartObject', lambda: add_chart_object(
            first, 20, 20, 300, 160))
        _record(results, 'Workbook SaveAs', lambda: save_workbook(workbook, paths['workbook_path']))
    finally:
        if any([row[1] == 'FAIL' for row in results]):
            retain_assets = True
        initial_cleanup_errors = []
        if excel is not None:
            initial_cleanup_errors = close_excel_application(
                excel, workbook, suppress_errors=True)
        for error in initial_cleanup_errors:
            results.append(['Initial Excel cleanup', 'FAIL', '', error])
        if initial_cleanup_errors:
            retain_assets = True
        if os.path.isfile(paths['workbook_path']) and not retain_assets:
            reopen_excel = _record(results, 'Create Excel for reopen', create_excel_application)
            if reopen_excel is not None:
                reopened = _record(results, 'Workbooks.Open read-only', lambda: open_workbook(
                    reopen_excel, paths['workbook_path'], update_links=0, read_only=True))
                if reopened is not None:
                    _record(results, 'RefreshAll', lambda: call_method(reopened, 'RefreshAll'))
                    _record(results, 'CalculateFullRebuild', lambda: call_method(reopen_excel, 'CalculateFullRebuild'))
                close_excel_application(reopen_excel, reopened, suppress_errors=True)
        _cleanup(paths, None, None, results, retain_assets)
        output.print_table(results, columns=['Operation', 'Status', 'Runtime type', 'Detail'])
        failures = len([row for row in results if row[1] == 'FAIL'])
        if failures:
            forms.alert('{} operation(s) failed. This run retained its owned temp assets for diagnosis. Review the output table.'.format(failures), title=__title__, warn_icon=True)
        else:
            forms.alert('All Excel COM facade smoke operations passed.', title=__title__)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(__title__))
        output.print_md('```')
        output.print_md(traceback.format_exc())
        output.print_md('```')
