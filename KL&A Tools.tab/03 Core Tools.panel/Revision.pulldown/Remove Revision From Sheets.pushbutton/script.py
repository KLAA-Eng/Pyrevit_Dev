__title__ = 'Toggle off Revision Schedule'
__version__ = 'v1.0'

from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script


logger = script.get_logger()


revisions = forms.select_revisions(button_name='Select Revisions',
                                   multiple=True)

logger.debug(revisions)

if revisions:
    sheets = forms.select_sheets(button_name='Turn off Revisions',
                                 include_placeholder=True)
    if sheets:
        with revit.Transaction('Manually Turn off Revisions'):
            updated_sheets = revit.update.update_sheet_revisions(revisions,
                                                                 sheets,
                                                                 state=False)
        if updated_sheets:
            print('SELECTED REVISIONS TURNED OFF FOR THESE SHEETS:')
            print('-' * 100)
            cloudedsheets = []
            for s in sheets:
                if s in updated_sheets:
                    revit.report.print_sheet(s)
                else:
                    cloudedsheets.append(s)
        else:
            cloudedsheets = sheets

        if len(cloudedsheets) > 0:
            print('\n\nSELECTED REVISION IS CLOUDED ON THESE SHEETS '
                  'AND CAN NOT BE TURNED OFF.')
            print('-' * 100)

            for s in cloudedsheets:
                revit.report.print_sheet(s)
