"""Generate lib/build_info.py from the repo-root version.json file."""

from __future__ import print_function

import datetime
import io
import json
import os
import re
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_PATH = os.path.join(REPO_ROOT, "version.json")
BUILD_INFO_PATH = os.path.join(REPO_ROOT, "lib", "build_info.py")


def read_version_payload():
    with io.open(VERSION_PATH, "r", encoding="utf-8") as version_file:
        return json.load(version_file)


def run_git(args):
    try:
        output = subprocess.check_output(
            ["git"] + args,
            cwd=REPO_ROOT,
            stderr=subprocess.STDOUT,
        )
    except Exception:
        return ""

    if not isinstance(output, str):
        output = output.decode("utf-8", "replace")
    return output.strip()


def expected_version_label(version, channel):
    """Return the display identity; this does not assert a Git tag exists."""
    normalized_channel = (channel or "stable").lower()
    legacy_channel_suffix = re.search(r"(alpha|beta|rc)$", version, re.I)
    if normalized_channel == "stable" or legacy_channel_suffix:
        return "v{0}".format(version)
    return "v{0}-{1}".format(version, normalized_channel)


def validate_payload(payload):
    """Validate new extension identities before generating or checking metadata."""
    version = payload.get('version', '')
    if not isinstance(version, str) or not re.match(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$', version):
        raise ValueError('version must be numeric MAJOR.MINOR.PATCH')
    if payload.get('channel') not in ('dev', 'beta', 'stable'):
        raise ValueError('channel must be dev, beta, or stable')
    value = payload.get('release_date', '')
    if not isinstance(value, str) or not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise ValueError('release_date must be YYYY-MM-DD')
    datetime.datetime.strptime(value, '%Y-%m-%d')


def render_build_info(payload, source_sha, build_date):
    """Render deterministic identity fields and explicit generation provenance."""
    validate_payload(payload)
    return '''# This file is generated from version.json.
# Do not edit by hand; update version.json and regenerate instead.
# METADATA_SOURCE_SHA is HEAD at generation, not the resulting release commit.

VERSION = "{version}"
CHANNEL = "{channel}"
RELEASE_DATE = "{release_date}"
VERSION_LABEL = "{version_label}"
METADATA_SOURCE_SHA = "{source_sha}"
BUILD_DATE = "{build_date}"
'''.format(version=payload['version'], channel=payload['channel'],
           release_date=payload['release_date'],
           version_label=expected_version_label(payload['version'], payload['channel']),
           source_sha=source_sha, build_date=build_date)


def main():
    payload = read_version_payload()
    source_sha = run_git(["rev-parse", "HEAD"]) or "unknown"
    build_info_contents = render_build_info(payload, source_sha, datetime.date.today().isoformat())

    with io.open(BUILD_INFO_PATH, "w", encoding="utf-8", newline="\n") as build_info_file:
        build_info_file.write(build_info_contents)

    print("Wrote {0}".format(BUILD_INFO_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
