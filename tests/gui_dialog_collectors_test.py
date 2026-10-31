"""Read-only collector contracts at the Revit API boundary."""
import os
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from GUI.dialogs import collectors
from GUI.dialogs.models import SelectionState


class Frozen(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __setattr__(self, name, value):
        raise AssertionError('Collector must not modify source objects')


def sheet(key, number, name, placeholder=False):
    return Frozen(UniqueId=key, SheetNumber=number, Name=name, IsPlaceholder=placeholder)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.created_collectors = []
        self.sheet_type, self.set_type = object(), object()
        parent = self

        class FakeCollector(object):
            def __init__(self, document):
                self.document = document
                self.disposed = False
                parent.created_collectors.append(self)

            def OfClass(self, element_type):
                self.element_type = element_type
                return self

            def WhereElementIsNotElementType(self):
                return self

            def ToElements(self):
                return self.document.elements[self.element_type]

            def Dispose(self):
                self.disposed = True

        self.api = types.SimpleNamespace(
            ViewSheet=self.sheet_type, ViewSheetSet=self.set_type,
            FilteredElementCollector=FakeCollector,
            Revision=types.SimpleNamespace(GetAllRevisionIds=lambda document: document.revision_ids),
            RevisionSettings=types.SimpleNamespace(GetRevisionSettings=lambda document: document.settings),
            RevisionNumbering=types.SimpleNamespace(PerProject='project'))

    def document(self, sheets=(), sets=(), family=False):
        return Frozen(elements={self.sheet_type: list(sheets), self.set_type: list(sets)}, IsFamilyDocument=family)

    def test_import_is_host_free(self):
        code = "import sys; sys.path.insert(0, 'lib'); import GUI.dialogs.collectors; assert 'Autodesk.Revit.DB' not in sys.modules; assert 'wpf' not in sys.modules; assert 'pyrevit' not in sys.modules"
        subprocess.check_call([sys.executable, '-B', '-c', code], cwd=ROOT)

    def test_sheets_sort_by_number_not_text(self):
        rows = [sheet('a', 'S10', 'Ten'), sheet('b', 'S2', 'Two'), sheet('c', 'A101', 'Plan'),
                sheet('d', 'S2.1', 'Two one'), sheet('e', 's1', 'One')]
        with patch.object(collectors, '_db', return_value=self.api):
            sorted_rows, _ = collectors.sheet_items(self.document(rows))
        self.assertEqual(['A101 - Plan', 's1 - One', 'S2 - Two', 'S2.1 - Two one', 'S10 - Ten'],
                         [row.Label for row in sorted_rows])

    def test_sheets_share_one_state_across_sets_and_filter_placeholders_consistently(self):
        one, two = sheet('one', 'S101', 'Notes'), sheet('two', 'S201', 'Plan')
        placeholder = sheet('placeholder', 'S001', 'Future', True)
        other_view = Frozen(UniqueId='view')
        sets = [Frozen(UniqueId='set-b', Name='Issue B', Views=[two, placeholder, one]),
                Frozen(UniqueId='set-a', Name='All Sheets', Views=[one, other_view])]
        document = self.document([two, placeholder, one, one], sets)
        with patch.object(collectors, '_db', return_value=self.api):
            rows, groups = collectors.sheet_items(document)
        self.assertEqual(['one', 'two'], [row.Key for row in rows])
        self.assertEqual(['S101 - Notes', 'S201 - Plan'], [row.Label for row in rows])
        self.assertIs(one, rows[0].Value)
        self.assertEqual(2, len(groups))
        self.assertNotIn('All Sheets', [group.Label for group in groups], 'Reserved implicit group must stay distinct')
        state = SelectionState(rows, groups=groups)
        state.group = groups[0].Key
        state.set_checked('one', True)
        state.group = groups[1].Key
        self.assertEqual([one], state.selected_values)
        self.assertTrue(all(item.disposed for item in self.created_collectors))

    def test_explicit_placeholder_inclusion_and_filter_apply_once_per_sheet(self):
        one, placeholder = sheet('one', 'S101', 'Notes'), sheet('p', 'S001', 'Future', True)
        document = self.document([one, placeholder], [Frozen(UniqueId='set', Name='Issue', Views=[one, placeholder])])
        seen = []
        with patch.object(collectors, '_db', return_value=self.api):
            rows, groups = collectors.sheet_items(document, include_placeholders=True,
                filterfunc=lambda item: seen.append(item.UniqueId) or item.IsPlaceholder)
        self.assertEqual(['one', 'p'], seen)
        self.assertEqual(['p'], [row.Key for row in rows])
        self.assertIn('placeholder', rows[0].Label.lower())
        self.assertEqual((groups[0].Key,), rows[0].Groups)

    def test_revision_order_status_and_per_project_numbers(self):
        first = Frozen(UniqueId='r1', SequenceNumber=1, RevisionNumber='A', Description='First', RevisionDate='2026-01-01', Issued=True)
        later = Frozen(UniqueId='r2', SequenceNumber=2, RevisionNumber='B', Description='Later', RevisionDate='2026-02-01', Issued=False)
        values = {'r1': first, 'r2': later}
        document = Frozen(IsFamilyDocument=False, settings=Frozen(RevisionNumbering='project'), revision_ids=['r2', 'r1'], GetElement=values.get)
        with patch.object(collectors, '_db', return_value=self.api):
            rows = collectors.revision_items(document)
            unissued = collectors.revision_items(document, filterfunc=lambda item: not item.Issued)
        self.assertEqual(['r1', 'r2'], [row.Key for row in rows])
        self.assertEqual('A - First', rows[0].Label)
        self.assertIn('2026-01-01', rows[0].Description)
        self.assertIn('Issued', rows[0].Description)
        self.assertIn('Unissued', rows[1].Description)
        self.assertEqual([later], [row.Value for row in unissued])

    def test_per_sheet_revisions_do_not_read_invalid_revision_number_property(self):
        class PerSheetRevision(object):
            UniqueId = 'revision'
            SequenceNumber = 3
            Description = 'Change'
            RevisionDate = ''
            Issued = False

            @property
            def RevisionNumber(self):
                raise AssertionError('RevisionNumber is unavailable in per-sheet mode')

        revision = PerSheetRevision()
        document = Frozen(IsFamilyDocument=False, settings=Frozen(RevisionNumbering='sheet'), revision_ids=['revision'], GetElement=lambda key: revision)
        with patch.object(collectors, '_db', return_value=self.api):
            rows = collectors.revision_items(document)
        self.assertEqual('3 - Change', rows[0].Label)

    def test_family_sheet_revision_sources_return_empty_without_loading_db(self):
        with patch.object(collectors, '_db', side_effect=AssertionError('No project queries for a family')):
            self.assertEqual(([], []), collectors.sheet_items(self.document(family=True)))
            self.assertEqual([], collectors.revision_items(self.document(family=True)))

    def test_empty_project_queries_and_missing_document_are_explicit(self):
        with patch.object(collectors, '_db', return_value=self.api):
            self.assertEqual(([], []), collectors.sheet_items(self.document()))
        for factory in (collectors.sheet_items, collectors.revision_items):
            with self.assertRaises(ValueError):
                factory(None)

    def test_query_failure_disposes_collector_and_predicate_errors_propagate(self):
        with patch.object(collectors, '_db', return_value=self.api):
            with self.assertRaises(KeyError):
                collectors.sheet_items(Frozen(IsFamilyDocument=False, elements={}))
        self.assertTrue(self.created_collectors[0].disposed)
        document = self.document([sheet('one', 'S101', 'Notes')])
        def broken_filter(item):
            raise ValueError('Caller validation failed')
        with patch.object(collectors, '_db', return_value=self.api):
            with self.assertRaisesRegex(ValueError, 'Caller validation failed'):
                collectors.sheet_items(document, filterfunc=broken_filter)

    def test_open_documents_preserve_duplicate_titles_and_exclude_links_active(self):
        active = Frozen(Title='Active', PathName='active.rvt', IsLinked=False, IsFamilyDocument=False)
        project = Frozen(Title='Same', PathName='project.rvt', IsLinked=False, IsFamilyDocument=False)
        family = Frozen(Title='Same', PathName='family.rfa', IsLinked=False, IsFamilyDocument=True)
        linked = Frozen(Title='Link', PathName='link.rvt', IsLinked=True, IsFamilyDocument=False)
        application = Frozen(Documents=[active, project, family, linked])
        rows = collectors.document_items(application, active_document=active)
        self.assertEqual([project, family], [row.Value for row in rows])
        self.assertNotEqual(rows[0].Key, rows[1].Key)
        self.assertIn('Project', rows[0].Description)
        self.assertIn('project.rvt', rows[0].Description)
        self.assertIn('Family', rows[1].Description)
        self.assertEqual(['Same', 'Same'], [row.Label for row in rows])
        rows = collectors.document_items(application, active_document=active, include_active=True, include_families=False)
        self.assertEqual([active, project], [row.Value for row in rows])

    def test_document_collection_requires_explicit_active_context_and_handles_missing_paths(self):
        unsaved = Frozen(Title='New project', PathName='', IsLinked=False, IsFamilyDocument=False)
        application = Frozen(Documents=[unsaved])
        with self.assertRaises(ValueError):
            collectors.document_items(application)
        rows = collectors.document_items(application, include_active=True)
        self.assertIn('No file path', rows[0].Description)
        self.assertEqual([], collectors.document_items(application, include_active=True, filterfunc=lambda item: False))

    def test_document_key_hash_collisions_and_repeated_source_do_not_merge_documents(self):
        class CollidingDocument(Frozen):
            def __hash__(self):
                return 1
        first = CollidingDocument(Title='Same', PathName='one.rvt', IsLinked=False, IsFamilyDocument=False)
        second = CollidingDocument(Title='Same', PathName='two.rvt', IsLinked=False, IsFamilyDocument=False)
        rows = collectors.document_items(Frozen(Documents=[first, second, first]), include_active=True)
        self.assertEqual([first, second], [row.Value for row in rows])
        state = SelectionState(rows)
        state.set_visible_checked(True)
        self.assertEqual([first, second], state.selected_values)


if __name__ == '__main__':
    unittest.main()
