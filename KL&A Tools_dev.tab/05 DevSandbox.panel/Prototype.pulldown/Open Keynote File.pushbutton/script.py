# -*- coding: utf-8 -*-
"""Open the keynote file connected to the active Revit project."""
from __future__ import print_function

import os

from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Open Keynote File'


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _model_path_to_visible_path(model_path):
    if model_path is None:
        return ''
    try:
        return DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
    except Exception:
        return ''


def _path_from_external_file_reference(ext_ref):
    if ext_ref is None:
        return ''

    for method_name in ('GetAbsolutePath', 'GetPath'):
        try:
            path = _model_path_to_visible_path(getattr(ext_ref, method_name)())
            if path:
                return path
        except Exception:
            pass
    return ''


def _keynote_path_from_table(doc):
    try:
        keynote_table = DB.KeynoteTable.GetKeynoteTable(doc)
    except Exception:
        keynote_table = None

    if keynote_table is None:
        return ''

    try:
        return _path_from_external_file_reference(
            keynote_table.GetExternalFileReference())
    except Exception:
        return ''


def _keynote_path_from_transmission_data(doc):
    location = doc.PathName
    if not location:
        return ''

    try:
        model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(location)
        trans_data = DB.TransmissionData.ReadTransmissionData(model_path)
    except Exception:
        return ''

    if trans_data is None:
        return ''

    try:
        external_references = trans_data.GetAllExternalFileReferenceIds()
    except Exception:
        return ''

    for ref_id in external_references:
        try:
            ext_ref = trans_data.GetLastSavedReferenceData(ref_id)
        except Exception:
            continue

        try:
            is_keynote = (
                ext_ref.ExternalFileReferenceType ==
                DB.ExternalFileReferenceType.KeynoteTable
            )
        except Exception:
            is_keynote = False

        if is_keynote:
            path = _path_from_external_file_reference(ext_ref)
            if path:
                return path

    return ''


def _connected_keynote_path(doc):
    path = _keynote_path_from_table(doc)
    if path:
        return path
    return _keynote_path_from_transmission_data(doc)


def main():
    doc = revit.doc
    path = _connected_keynote_path(doc)
    if not path:
        _stop(
            'Could not find a connected keynote file path for the active '
            'project. Save the model and confirm the keynote file is loaded, '
            'then try again.'
        )

    if not os.path.isfile(path):
        _stop(
            'The connected keynote path could not be opened as a local file:\n\n'
            '{}'.format(path)
        )

    try:
        os.startfile(path)
    except Exception as error:
        _stop('Could not open keynote file:\n\n{}\n\n{}'.format(path, error))


if __name__ == '__main__':
    main()
