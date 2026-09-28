"""Set selected revisions on selected sheets."""

from pyrevit import revit, DB, EXEC_PARAMS
from pyrevit import forms

# define a filterfunc to filter out issued revisions
def filterfunc(rev):
    if EXEC_PARAMS.config_mode:
        return True
    return rev.Issued == False

revisions = forms.select_revisions(button_name='Select Revisions',
                                   multiple=True,
                                   filterfunc=filterfunc)

if revisions:
    sheets = forms.select_sheets(button_name='Turn on Revisions',
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
