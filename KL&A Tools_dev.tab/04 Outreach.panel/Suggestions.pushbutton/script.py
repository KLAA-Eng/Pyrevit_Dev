# -*- coding: utf-8 -*-
import os
import urllib

from pyrevit import forms, revit, script
from Autodesk.Revit.DB import ModelPathUtils


# Replace these placeholders with the real Microsoft Form URL and field keys.
# The field key names should match the query string keys from a prefilled link.
FORM_BASE_URL = "https://forms.office.com/Pages/ResponsePage.aspx?id=REPLACE_ME"
FIELD_MAP = {
    "report_type": "REPORT_TYPE_FIELD",
    "summary": "SUMMARY_FIELD",
    "user_name": "USER_FIELD",
    "revit_version": "REVIT_VERSION_FIELD",
    "revit_build": "REVIT_BUILD_FIELD",
    "document_title": "DOCUMENT_TITLE_FIELD",
    "document_path": "DOCUMENT_PATH_FIELD",
    "is_workshared": "WORKSHARED_FIELD",
    "machine_name": "MACHINE_FIELD",
}


def has_form_configuration():
    if "REPLACE_ME" in FORM_BASE_URL:
        return False

    return all(
        field_key and "FIELD" not in field_key
        for field_key in FIELD_MAP.values()
    )


def get_document_path(doc):
    path_name = doc.PathName or ""
    if path_name:
        return path_name

    try:
        central_path = doc.GetWorksharingCentralModelPath()
        if central_path:
            return ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
    except Exception:
        pass

    return "<unsaved>"


def collect_context():
    doc = revit.doc
    app = __revit__.Application

    version_number = getattr(app, "VersionNumber", "") or ""
    sub_version = getattr(app, "SubVersionNumber", "") or ""
    build_parts = [part for part in [version_number, sub_version] if part]

    return {
        "user_name": getattr(app, "Username", "") or os.environ.get("USERNAME", ""),
        "revit_version": getattr(app, "VersionName", "") or version_number,
        "revit_build": " | ".join(build_parts),
        "document_title": doc.Title if doc else "<no document>",
        "document_path": get_document_path(doc) if doc else "<no document>",
        "is_workshared": "Yes" if doc and doc.IsWorkshared else "No",
        "machine_name": os.environ.get("COMPUTERNAME", ""),
    }


def prompt_for_user_input():
    report_type = forms.CommandSwitchWindow.show(
        ["Bug Report", "Suggestion", "General Feedback", "Cancel"],
        message="What kind of feedback do you want to send?"
    )

    if not report_type or report_type == "Cancel":
        script.exit()

    summary = forms.ask_for_string(
        default="",
        prompt="Add a short summary for the form subject line.",
        title="Feedback Summary"
    )

    if summary is None:
        script.exit()

    return report_type, summary.strip()


def build_form_url(payload):
    query_items = []

    for payload_key, field_key in FIELD_MAP.items():
        value = payload.get(payload_key, "")
        if not field_key or value is None:
            continue

        query_items.append(
            "{}={}".format(
                urllib.quote_plus(field_key),
                urllib.quote_plus(value.encode("utf-8"))
            )
        )

    separator = "&" if "?" in FORM_BASE_URL else "?"
    return "{}{}{}".format(FORM_BASE_URL, separator, "&".join(query_items))


def main():
    if not has_form_configuration():
        forms.alert(
            "Update FORM_BASE_URL and FIELD_MAP in this button script with the real Microsoft Forms prefilled link values before using it.",
            title="Suggestions Form Not Configured",
            warn_icon=True,
        )
        script.exit()

    report_type, summary = prompt_for_user_input()

    payload = collect_context()
    payload["report_type"] = report_type
    payload["summary"] = summary or "<no summary provided>"

    os.startfile(build_form_url(payload))


if __name__ == "__main__":
    main()
