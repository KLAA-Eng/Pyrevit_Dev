__title__ = 'Toggle on Revision Schedule'
__version__ = 'v1.0'

from pyrevit import revit, DB, EXEC_PARAMS
from pyrevit import forms
from GUI import tool_selectors

# define a filterfunc to filter out issued revisions
def filterfunc(rev):
    if EXEC_PARAMS.config_mode:
        return True
    return rev.Issued == False

revisions = tool_selectors.select_revisions(revit.doc, title=__title__, version=__version__, button_name='Select Revisions',
                                   multiple=True,
                                   filterfunc=filterfunc)

if revisions:
    sheets = tool_selectors.select_sheets(revit.doc, title=__title__, version=__version__, button_name='Turn on Revisions',
                                 include_placeholder=True)
    if sheets:
        with revit.Transaction('Manually Turn on Revisions'):
            updated_sheets = revit.update.update_sheet_revisions(revisions,
                                                                 sheets)
        if updated_sheets:
            print('SELECTED REVISIONS TURNED ON FOR THESE SHEETS:')
            print('-' * 100)
            for s in updated_sheets:
                snum = s.Parameter[DB.BuiltInParameter.SHEET_NUMBER]\
                        .AsString().rjust(10)
                sname = s.Parameter[DB.BuiltInParameter.SHEET_NAME]\
                         .AsString().ljust(50)
                print('NUMBER: {0}   NAME:{1}'.format(snum, sname))
