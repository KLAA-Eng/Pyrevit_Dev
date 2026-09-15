# -*- coding: utf-8 -*-
import os
import urllib

from pyrevit import forms, revit, script
from Autodesk.Revit.DB import ModelPathUtils


# Base ResponsePage URL only. Keep sample values out of this string.
FORM_BASE_URL = "https://forms.microsoft.com/Pages/ResponsePage.aspx?id=Bfmd9K3MFkqVWdMqprbPvvfxx29Ur-NGhLTDKxuFAqVUMU1OMUpRWDRKUDBMNEFEMlQ2SEJJNFdCUi4u"
FIELD_MAP = {
    "report_type": "rd238bee241134be78f2f0f21eab8b1f3",
    "subject": "r9ce9687c26eb4eeda8e9cfa798fe4188",
    "user_name": "re12656beea964a95a038244508ce903f",
    "revit_build": "r57d7fb02c8e34ef69930b3bef1230fa2",
    "is_workshared": "rfdefb4c8c0ad4daa883dd1cbd40a2da0",
}


def has_form_configuration():
    if not FORM_BASE_URL or "ResponsePage.aspx?id=" not in FORM_BASE_URL:
        return False

    return all(
        field_key and field_key.startswith("r")
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

    subject = forms.ask_for_string(
        default="",
        prompt="Add a short subject for the form subject line.",
        title="Feedback subject"
    )

    if subject is None:
        script.exit()

    return report_type, subject.strip()


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

    report_type, subject = prompt_for_user_input()

    payload = collect_context()
    payload["report_type"] = report_type
    payload["subject"] = subject or "<no subject provided>"

    os.startfile(build_form_url(payload))


if __name__ == "__main__":
    main()
