"""Lists revision clouds on sheets and directly placed views, by sheet."""

from pyrevit import revit, DB
from pyrevit import script


output = script.get_output()
output.close_others()


def _element_id_value(element_id):
    try:
        return element_id.Value
    except Exception:
        return element_id.IntegerValue


def _sheet_label(sheet):
    return '{} - {}'.format(sheet.SheetNumber, sheet.Name)


def _view_name(view):
    try:
        return revit.query.get_name(view)
    except Exception:
        return view.Name


def _cloud_location(doc, sheet, cloud):
    """Describes where a sheet-visible cloud is displayed on that sheet."""
    owner_view = doc.GetElement(cloud.OwnerViewId)
    if owner_view is None:
        return 'OWNER VIEW NOT FOUND'
    if isinstance(owner_view, DB.ViewSheet):
        return 'ON SHEET'

    placed_view_ids = set([
        _element_id_value(view_id) for view_id in sheet.GetAllPlacedViews()
    ])
    owner_value = _element_id_value(owner_view.Id)
    if owner_value in placed_view_ids:
        return 'IN VIEW: {}'.format(_view_name(owner_view))

    # Clouds owned by a primary view can be displayed in its dependent view.
    # Report the placed dependent, not the primary owner, when it is present.
    try:
        dependent_ids = owner_view.GetDependentViewIds()
    except Exception:
        dependent_ids = []
    placed_dependents = []
    for dependent_id in dependent_ids:
        if _element_id_value(dependent_id) not in placed_view_ids:
            continue
        dependent_view = doc.GetElement(dependent_id)
        if dependent_view is not None:
            placed_dependents.append(_view_name(dependent_view))
    if placed_dependents:
        return 'IN VIEW: {}'.format(', '.join(placed_dependents))
    return 'IN OWNER VIEW: {}'.format(_view_name(owner_view))


def _cloud_sort_key(doc, cloud):
    """Sorts clouds by their project revision order, then by cloud id."""
    revision = doc.GetElement(cloud.RevisionId)
    try:
        sequence = revision.SequenceNumber
    except Exception:
        sequence = 2147483647
    return (sequence, _element_id_value(cloud.Id))


def _cloud_line(cloud, location):
    revision = revit.doc.GetElement(cloud.RevisionId)
    revision_number = revit.query.get_param(
        cloud, 'Revision Number').AsValueString()
    revision_sequence = revit.query.get_param(
        revision, 'Revision Number', revision.SequenceNumber).AsValueString()
    revision_display = revision_number if not revision_sequence else revision_sequence
    cloud_id = output.linkify([cloud.Id])
    return ('REV#: {revision}\t\tREV SEQ#: {sequence}\t\tID: {cloud_id}'
            '\t\t{location}').format(
                revision=revision_display,
                sequence=revision.SequenceNumber,
                cloud_id=cloud_id,
                location=location)


def _clouds_by_sheet(doc):
    """Groups every revision cloud visible on each sheet by that sheet."""
    clouds_by_sheet = {}
    sheets = (DB.FilteredElementCollector(doc)
              .OfCategory(DB.BuiltInCategory.OST_Sheets)
              .WhereElementIsNotElementType()
              .ToElements())

    for sheet in sheets:
        if sheet.IsPlaceholder:
            continue
        # Returns individual clouds visible on this sheet, including clouds in
        # views on the sheet and clouds placed directly on the sheet:
        # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/dd1487e6-dffa-5c9c-8fcc-ff8f664b494e.htm
        clouds = []
        for cloud_id in sheet.GetAllRevisionCloudIds():
            cloud = doc.GetElement(cloud_id)
            if cloud is not None:
                clouds.append(cloud)
        clouds.sort(key=lambda cloud: _cloud_sort_key(doc, cloud))
        if clouds:
            clouds_by_sheet[_element_id_value(sheet.Id)] = {
                'sheet': sheet,
                'clouds': clouds,
            }
    return clouds_by_sheet


def main():
    clouds_by_sheet = _clouds_by_sheet(revit.doc)

    for group in sorted(
            clouds_by_sheet.values(),
            key=lambda item: item['sheet'].SheetNumber):
        output.print_md('## {}'.format(_sheet_label(group['sheet'])))
        for cloud in group['clouds']:
            print(_cloud_line(
                cloud, _cloud_location(revit.doc, group['sheet'], cloud)))

    print('\nSEARCH COMPLETED.')


if __name__ == '__main__':
    main()
