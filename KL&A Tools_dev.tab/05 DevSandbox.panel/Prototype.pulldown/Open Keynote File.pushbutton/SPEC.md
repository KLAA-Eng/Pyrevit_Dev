# Open Keynote File

## Purpose

`Open Keynote File` is a DevSandbox pyRevit prototype that opens the keynote
file connected to the active Revit project.

## Scope and output

The command resolves the active document's keynote table external file
reference, converts the Revit model path to a user-visible path, verifies that
the path is a local or network file accessible to Windows, and opens it with the
default application.

If the direct keynote table reference cannot be resolved, the command falls
back to reading saved external reference data from `TransmissionData`.

## Exclusions and limits

The command does not ask the user to select a replacement keynote file. It does
not modify, reload, relink, save, or synchronize the Revit model.

Cloud-only or otherwise non-filesystem keynote references are reported as path
issues instead of being opened.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: `os`; `pyrevit.DB`, `forms`, `revit`, `script`
- External effect: opens one existing keynote file through `os.startfile`

## Current status

This is a development-tab command and must be validated inside the target
Revit/pyRevit environment before promotion.
