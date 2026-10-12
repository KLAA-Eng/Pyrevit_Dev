# -*- coding: utf-8 -*-
"""Exercise the transaction boundary with a small stand-in for Revit."""

import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))


class Status(object):
    Started = "Started"
    Committed = "Committed"
    RolledBack = "RolledBack"
    Pending = "Pending"


class InvalidTarget(Exception):
    pass


class Document(object):
    def __init__(self):
        self.elements = []
        self.fail_commit = False

    def snapshot(self):
        return [(element, element.Name, element.SheetNumber)
                for element in self.elements]

    def restore(self, snapshot):
        for element, name, number in snapshot:
            object.__setattr__(element, "Name", name)
            object.__setattr__(element, "SheetNumber", number)


class Element(object):
    def __init__(self, doc, name, number):
        object.__setattr__(self, "Name", name)
        object.__setattr__(self, "SheetNumber", number)
        doc.elements.append(self)

    def __setattr__(self, field, value):
        if value == "invalid":
            raise InvalidTarget("Invalid exact target")
        if value == "normalize":
            value = "Normalized"
        object.__setattr__(self, field, value)


class FakeTransaction(object):
    def __init__(self, doc, unused_name=None):
        self.doc = doc
        self.status = None
        self.is_parent = unused_name is not None

    def Start(self):
        self.before = self.doc.snapshot()
        self.status = Status.Started
        return self.status

    def Commit(self):
        if self.is_parent and self.doc.fail_commit:
            self.doc.restore(self.before)
            self.status = Status.RolledBack
        else:
            self.status = Status.Committed
        return self.status

    def RollBack(self):
        self.doc.restore(self.before)
        self.status = Status.RolledBack
        return self.status

    def GetStatus(self):
        return self.status

    def Dispose(self):
        pass


def load_batch():
    db = types.ModuleType("Autodesk.Revit.DB")
    db.Transaction = FakeTransaction
    db.SubTransaction = FakeTransaction
    db.TransactionStatus = Status
    exceptions = types.ModuleType("Autodesk.Revit.Exceptions")
    exceptions.ArgumentException = InvalidTarget
    fake_modules = {"Autodesk": types.ModuleType("Autodesk"),
                    "Autodesk.Revit": types.ModuleType("Autodesk.Revit"),
                    "Autodesk.Revit.DB": db,
                    "Autodesk.Revit.Exceptions": exceptions}
    source = os.path.join(os.path.dirname(__file__), "..", "lib",
                          "find_replace", "revit_batch.py")
    spec = importlib.util.spec_from_file_location("batch_under_test", source)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, fake_modules):
        spec.loader.exec_module(module)
    return module


class BatchTests(unittest.TestCase):
    def test_failed_second_field_rolls_back_one_sheet_only(self):
        batch = load_batch()
        doc = Document()
        first = Element(doc, "First", "A1")
        second = Element(doc, "Second", "A2")
        result = batch.apply_batch(doc, "Rename", [
            {"element": first, "label": "A1", "changes": [
                ("Name", "New First"), ("SheetNumber", "invalid")]},
            {"element": second, "label": "A2", "changes": [
                ("Name", "New Second"), ("SheetNumber", "B2")]}])
        self.assertEqual(("First", "A1"), (first.Name, first.SheetNumber))
        self.assertEqual(("New Second", "B2"), (second.Name, second.SheetNumber))
        self.assertEqual(1, len(result["skipped"]))
        self.assertEqual(1, len(result["changed"]))

    def test_failed_batch_commit_reports_no_committed_changes(self):
        batch = load_batch()
        doc = Document()
        doc.fail_commit = True
        sheet = Element(doc, "First", "A1")
        result = batch.apply_batch(doc, "Rename", [
            {"element": sheet, "label": "A1", "changes": [("Name", "New")]}])
        self.assertEqual("First", sheet.Name)
        self.assertEqual([], result["changed"])
        self.assertEqual(1, len(result["failed"]))
        self.assertIn("Batch transaction status", result["error"])

    def test_non_exact_setter_result_is_skipped_and_rolled_back(self):
        batch = load_batch()
        doc = Document()
        sheet = Element(doc, "First", "A1")
        result = batch.apply_batch(doc, "Rename", [
            {"element": sheet, "label": "A1", "changes": [("Name", "normalize")]}])
        self.assertEqual("First", sheet.Name)
        self.assertEqual(1, len(result["skipped"]))
        self.assertEqual([], result["changed"])


if __name__ == "__main__":
    unittest.main()
