"""Generate lib/build_info.py from the repo-root version.json file."""

from __future__ import print_function

import datetime
import io
import json
import os
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


def main():
    payload = read_version_payload()
    version = payload["version"]
    release_date = payload.get("release_date") or datetime.date.today().isoformat()
    git_tag = run_git(["describe", "--tags", "--exact-match", "HEAD"]) or "v{0}".format(version)
    git_sha = run_git(["rev-parse", "--short", "HEAD"]) or "unknown"

    build_info_contents = """# This file is generated from version.json.
# Do not edit by hand; update version.json and regenerate instead.

VERSION = "{version}"
CHANNEL = "{channel}"
RELEASE_DATE = "{release_date}"
GIT_TAG = "{git_tag}"
GIT_SHA = "{git_sha}"
BUILD_DATE = "{build_date}"
""".format(
        version=version,
        channel=payload.get("channel", ""),
        release_date=release_date,
        git_tag=git_tag,
        git_sha=git_sha,
        build_date=datetime.date.today().isoformat(),
    )

    with io.open(BUILD_INFO_PATH, "w", encoding="utf-8", newline="\n") as build_info_file:
        build_info_file.write(build_info_contents)

    print("Wrote {0}".format(BUILD_INFO_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
