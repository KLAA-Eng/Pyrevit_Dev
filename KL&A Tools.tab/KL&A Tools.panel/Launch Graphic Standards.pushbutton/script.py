# -*- coding: utf-8 -*-
__title__ = "Open Graphics Standards Bluebeam Session"
__doc__ = "Launches KL&A Graphics Standards Bluebeam Studio Session from Revit."

import re
import subprocess

from pyrevit import forms, script

logger = script.get_logger()

SESSION_ID = "665-447-452"

def normalize_session_id(raw_value):
    if not raw_value:
        return None

    raw_value = str(raw_value).strip()
    match = re.search(r'(\d{3}-\d{3}-\d{3}|\d{9})', raw_value)

    if not match:
        return None

    digits = re.sub(r'\D', '', match.group(1))

    if len(digits) != 9:
        return None

    return "{}-{}-{}".format(digits[0:3], digits[3:6], digits[6:9])

session_id = normalize_session_id(SESSION_ID)

if not session_id:
    forms.alert(
        "The SESSION_ID is not valid.",
        title="Invalid Bluebeam Session ID",
        warn_icon=True
    )
    script.exit()

studio_url = "studio://studio.bluebeam.com/{}/".format(session_id)
logger.info("Launching Bluebeam Studio Session: {}".format(studio_url))

try:
    subprocess.Popen(["cmd", "/c", "start", "", studio_url], shell=False)
except Exception as ex:
    forms.alert(
        "Could not launch Session."
        .format(str(ex)),
        title="Launch Failed",
        warn_icon=True
    )
    script.exit()