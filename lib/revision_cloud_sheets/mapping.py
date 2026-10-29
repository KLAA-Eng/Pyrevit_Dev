"""Pure rules for mapping revision clouds to the sheets that show them."""

import re


def sheets_by_cloud(clouds_by_sheet, cloud_ids=None):
    """Invert ``(sheet_key, [cloud_id, ...])`` pairs into ``{cloud_id: [sheet_key]}``.

    When ``cloud_ids`` is given, only those clouds are reported, and each one
    is present even when no sheet shows it. Sheet keys keep their input order
    and appear once per cloud.
    """
    result = {}
    if cloud_ids is not None:
        for cloud_id in cloud_ids:
            result[cloud_id] = []
    for sheet_key, sheet_cloud_ids in clouds_by_sheet:
        for cloud_id in sheet_cloud_ids:
            if cloud_ids is not None and cloud_id not in result:
                continue
            sheets = result.setdefault(cloud_id, [])
            if sheet_key not in sheets:
                sheets.append(sheet_key)
    return result


def sheet_number_sort_key(sheet_number):
    """Sort sheet numbers naturally, so S-2 comes before S-10."""
    parts = re.split(r'(\d+)', (sheet_number or '').upper())
    return tuple(
        (0, int(part), '') if part.isdigit() else (1, 0, part)
        for part in parts if part
    )
