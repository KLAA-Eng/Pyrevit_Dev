from __future__ import print_function

import importlib.util
import os
import sys
import types
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVISION_ROOT = os.path.join(
    PROJECT_ROOT, 'KL&A Tools_dev.tab', '03 Core Tools.panel',
    'Revision.pulldown')
COMMAND_PATH = os.path.join(
    REVISION_ROOT, 'Hide Revision Clouds.pushbutton', 'script.py')
FINDER_PATH = os.path.join(
    REVISION_ROOT, 'Find All Revision Clouds On Views.pushbutton', 'script.py')


class FakeGenericList(object):
    @classmethod
    def __class_getitem__(cls, unused_item_type):
        return list


def load_command_module():
    pyrevit = types.ModuleType('pyrevit')
    pyrevit.DB = object()
    pyrevit.forms = object()
    pyrevit.revit = object()
    pyrevit.script = object()
    gui = types.ModuleType('GUI')
    gui_forms = types.ModuleType('GUI.forms')
    gui_forms.select_from_dict = lambda *args, **kwargs: []
    system = types.ModuleType('System')
    collections = types.ModuleType('System.Collections')
    generic = types.ModuleType('System.Collections.Generic')
    generic.List = FakeGenericList
    clr = types.ModuleType('clr')
    clr.AddReference = lambda unused_reference: None
    autodesk = types.ModuleType('Autodesk')
    autodesk_revit = types.ModuleType('Autodesk.Revit')
    ui = types.ModuleType('Autodesk.Revit.UI')
    ui.TaskDialog = object()
    ui.TaskDialogCommandLinkId = object()
    ui.TaskDialogCommonButtons = object()
    ui.TaskDialogResult = object()

    modules = {
        'pyrevit': pyrevit,
        'GUI': gui,
        'GUI.forms': gui_forms,
        'System': system,
        'System.Collections': collections,
        'System.Collections.Generic': generic,
        'clr': clr,
        'Autodesk': autodesk,
        'Autodesk.Revit': autodesk_revit,
        'Autodesk.Revit.UI': ui,
    }
    previous = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    library_path = os.path.join(PROJECT_ROOT, 'lib')
    sys.path.insert(0, library_path)
    try:
        spec = importlib.util.spec_from_file_location(
            'revision_clouds_command_test_module', COMMAND_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, prior in previous.items():
            if prior is None:
                del sys.modules[name]
            else:
                sys.modules[name] = prior
        sys.path.remove(library_path)


def load_finder_module():
    pyrevit = types.ModuleType('pyrevit')
    pyrevit.DB = object()
    pyrevit.revit = object()
    pyrevit.script = types.SimpleNamespace(
        get_output=lambda: types.SimpleNamespace(close_others=lambda: None))
    previous = sys.modules.get('pyrevit')
    sys.modules['pyrevit'] = pyrevit
    try:
        spec = importlib.util.spec_from_file_location(
            'find_revision_clouds_command_test_module', FINDER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            del sys.modules['pyrevit']
        else:
            sys.modules['pyrevit'] = previous


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeDocument(object):
    def __init__(self, elements):
        self.elements = {element_id.Value: element
                         for element_id, element in elements.items()}

    def GetElement(self, element_id):
        return self.elements.get(element_id.Value)


class FakeSheet(object):
    def __init__(self, value, placed_view_ids=(), additional_ids=(),
                 revision_cloud_ids=()):
        self.Id = FakeElementId(value)
        self.SheetNumber = 'S{}'.format(value)
        self.Name = 'Sheet {}'.format(value)
        self._placed_view_ids = list(placed_view_ids)
        self._revision_cloud_ids = list(revision_cloud_ids)
        self._additional_ids = FakeRevisionIds(additional_ids)
        self.saved_revision_ids = None
        self.IsPlaceholder = False
        self.hidden_ids = []
        self.unhidden_ids = []

    def GetAllPlacedViews(self):
        return self._placed_view_ids

    def GetAllRevisionCloudIds(self):
        return self._revision_cloud_ids

    def GetAdditionalRevisionIds(self):
        return self._additional_ids

    def SetAdditionalRevisionIds(self, revision_ids):
        self.saved_revision_ids = list(revision_ids)

    def HideElements(self, element_ids):
        self.hidden_ids.extend(element_ids)

    def UnhideElements(self, element_ids):
        self.unhidden_ids.extend(element_ids)


class FakeView(object):
    def __init__(self, value, primary_view_id=None, dependent_view_ids=()):
        self.Id = FakeElementId(value)
        self.Name = 'View {}'.format(value)
        self._primary_view_id = primary_view_id
        self._dependent_view_ids = list(dependent_view_ids)
        self.hidden_ids = []
        self.unhidden_ids = []

    def HideElements(self, element_ids):
        self.hidden_ids.extend(element_ids)

    def UnhideElements(self, element_ids):
        self.unhidden_ids.extend(element_ids)

    def GetPrimaryViewId(self):
        return self._primary_view_id

    def GetDependentViewIds(self):
        return self._dependent_view_ids


class FakeCollector(list):
    def OfCategory(self, unused_category):
        return self

    def WhereElementIsNotElementType(self):
        return self

    def ToElements(self):
        return list(self)


class FakeCloud(object):
    def __init__(self, value, revision_value, hidden=False, hideable=True,
                 owner_value=None, sheet_values=()):
        self.Id = FakeElementId(value)
        self.RevisionId = FakeElementId(revision_value)
        self.OwnerViewId = FakeElementId(owner_value)
        self._hidden = hidden
        self._hideable = hideable
        self._sheet_values = sheet_values

    def IsHidden(self, unused_view):
        return self._hidden

    def CanBeHidden(self, unused_view):
        return self._hideable

    def GetSheetIds(self):
        return [FakeElementId(value) for value in self._sheet_values]


class FakeRevisionIds(list):
    def Add(self, revision_id):
        self.append(revision_id)

    def Remove(self, revision_id):
        self.remove(revision_id)


class RevisionCloudCommandTests(unittest.TestCase):
    def setUp(self):
        self.command = load_command_module()
        self.command.DB = types.SimpleNamespace(
            ElementId=FakeElementId, ViewSheet=FakeSheet)
        self.command._view_label = lambda view: view.Name

    def _set_cloud_collector(self, clouds):
        self.command.DB = types.SimpleNamespace(
            ElementId=FakeElementId,
            ViewSheet=FakeSheet,
            BuiltInCategory=types.SimpleNamespace(OST_RevisionClouds=object()),
            FilteredElementCollector=lambda unused_doc: FakeCollector(clouds),
        )

    def test_bundle_promotes_cloud_tool_and_hides_global_turn_off(self):
        with open(os.path.join(REVISION_ROOT, 'bundle.yaml'), 'r') as stream:
            revision_layout = stream.read()
        prototype_layout_path = os.path.join(
            PROJECT_ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
            'Prototype.pulldown', 'bundle.yaml')
        with open(prototype_layout_path, 'r') as stream:
            prototype_layout = stream.read()

        self.assertIn('  - Hide Revision Clouds', revision_layout)
        self.assertNotIn('  - Turn Off All Revisions', revision_layout)
        self.assertNotIn('  - Hide Revision Clouds', prototype_layout)

    def test_edited_revision_metadata_uses_new_english_titles(self):
        expected_titles = {
            'Find All Revision Clouds On Views.pushbutton':
                'Find All Revision Clouds',
            'Set Revision On Sheets.pushbutton':
                'Manually Turn on Revisions',
            'Remove Revision From Sheets.pushbutton':
                'Manually Turn off Revisions',
        }
        for bundle_name, title in expected_titles.items():
            bundle_path = os.path.join(
                REVISION_ROOT, bundle_name, 'bundle.yaml')
            with open(bundle_path, 'r') as stream:
                bundle_text = stream.read()
            self.assertIn('en_us: {}'.format(title), bundle_text)
            self.assertNotIn('ko:', bundle_text)

    def test_revision_and_sheet_pickers_start_with_no_checked_items(self):
        revision = types.SimpleNamespace(Id=FakeElementId(1))
        sheet = FakeSheet(10)
        selections = []
        self.command.DB = types.SimpleNamespace(
            BuiltInCategory=types.SimpleNamespace(
                OST_Revisions=object(), OST_Sheets=object()),
            FilteredElementCollector=lambda unused_doc: FakeCollector(
                [revision]),
        )
        self.command._revision_option_label = lambda unused_revision: 'R1'
        self.command.select_from_dict = lambda options, **kwargs: (
            selections.append(kwargs) or list(options.values()))

        self.command._select_revisions(object(), 'Hide')
        self.command.DB = types.SimpleNamespace(
            BuiltInCategory=types.SimpleNamespace(
                OST_Revisions=object(), OST_Sheets=object()),
            FilteredElementCollector=lambda unused_doc: FakeCollector([sheet]),
        )
        self.command._select_sheets(object(), 'Hide')

        self.assertEqual([], selections[0]['initial_checked_names'])
        self.assertEqual([], selections[1]['initial_checked_names'])
        self.assertEqual('Hide Clouds', selections[1]['button_name'])

    def test_finder_groups_each_cloud_returned_by_its_sheet(self):
        finder = load_finder_module()
        finder.DB = types.SimpleNamespace(
            ViewSheet=FakeSheet,
            BuiltInCategory=types.SimpleNamespace(OST_Sheets=object()),
            FilteredElementCollector=lambda unused_doc: FakeCollector(
                [sheet_a, sheet_b]),
        )
        dependent_view_a = FakeView(20)
        dependent_view_b = FakeView(21)
        parent_view = FakeView(22)
        sheet_a = FakeSheet(10, placed_view_ids=[dependent_view_a.Id])
        sheet_b = FakeSheet(11, placed_view_ids=[dependent_view_b.Id])
        cloud_on_dependent_a = FakeCloud(
            100, 7, owner_value=20, sheet_values=[10, 11])
        cloud_on_dependent_b = FakeCloud(101, 7, owner_value=21)
        cloud_on_parent_view = FakeCloud(
            102, 7, owner_value=22, sheet_values=[10, 11])
        cloud_on_sheet = FakeCloud(103, 7, owner_value=10)
        sheet_a._revision_cloud_ids = [
            cloud_on_dependent_a.Id, cloud_on_sheet.Id]
        sheet_b._revision_cloud_ids = [cloud_on_dependent_b.Id]
        document = FakeDocument({
            dependent_view_a.Id: dependent_view_a,
            dependent_view_b.Id: dependent_view_b,
            parent_view.Id: parent_view,
            sheet_a.Id: sheet_a,
            sheet_b.Id: sheet_b,
            cloud_on_dependent_a.Id: cloud_on_dependent_a,
            cloud_on_dependent_b.Id: cloud_on_dependent_b,
            cloud_on_parent_view.Id: cloud_on_parent_view,
            cloud_on_sheet.Id: cloud_on_sheet,
        })

        groups = finder._clouds_by_sheet(document)

        self.assertEqual(
            [cloud_on_dependent_a, cloud_on_sheet], groups[10]['clouds'])
        self.assertEqual([cloud_on_dependent_b], groups[11]['clouds'])
        self.assertNotIn(cloud_on_parent_view, groups[10]['clouds'])
        self.assertNotIn(cloud_on_parent_view, groups[11]['clouds'])

    def test_finder_reports_sheet_and_placed_dependent_locations(self):
        finder = load_finder_module()
        finder.DB = types.SimpleNamespace(ViewSheet=FakeSheet)
        placed_view = FakeView(21)
        primary_view = FakeView(
            20, dependent_view_ids=[placed_view.Id])
        sheet = FakeSheet(10, placed_view_ids=[placed_view.Id])
        cloud_in_primary = FakeCloud(100, 7, owner_value=20)
        cloud_on_sheet = FakeCloud(101, 7, owner_value=10)
        document = FakeDocument({
            primary_view.Id: primary_view,
            placed_view.Id: placed_view,
            sheet.Id: sheet,
            cloud_in_primary.Id: cloud_in_primary,
            cloud_on_sheet.Id: cloud_on_sheet,
        })

        self.assertEqual(
            'IN VIEW: View 21',
            finder._cloud_location(document, sheet, cloud_in_primary))
        self.assertEqual(
            'ON SHEET',
            finder._cloud_location(document, sheet, cloud_on_sheet))

    def test_finder_sorts_each_sheet_cloud_list_by_revision_sequence(self):
        finder = load_finder_module()
        late_revision = types.SimpleNamespace(
            Id=FakeElementId(8), SequenceNumber=8)
        early_revision = types.SimpleNamespace(
            Id=FakeElementId(7), SequenceNumber=2)
        late_cloud = FakeCloud(101, 8, owner_value=10)
        early_cloud = FakeCloud(100, 7, owner_value=10)
        sheet = FakeSheet(
            10, revision_cloud_ids=[late_cloud.Id, early_cloud.Id])
        finder.DB = types.SimpleNamespace(
            BuiltInCategory=types.SimpleNamespace(OST_Sheets=object()),
            FilteredElementCollector=lambda unused_doc: FakeCollector([sheet]),
        )
        document = FakeDocument({
            sheet.Id: sheet,
            late_revision.Id: late_revision,
            early_revision.Id: early_revision,
            late_cloud.Id: late_cloud,
            early_cloud.Id: early_cloud,
        })

        groups = finder._clouds_by_sheet(document)

        self.assertEqual(
            [early_cloud, late_cloud], groups[10]['clouds'])

    def test_cloud_selection_respects_hide_and_unhide_state(self):
        owner_view = FakeView(20)
        sheet = FakeSheet(10, placed_view_ids=[owner_view.Id])
        visible_cloud = FakeCloud(
            100, 7, hidden=False, owner_value=20, sheet_values=[10])
        hidden_cloud = FakeCloud(
            101, 7, hidden=True, owner_value=20, sheet_values=[10])
        document = FakeDocument({owner_view.Id: owner_view, sheet.Id: sheet})

        hide_report = self._report()
        self._set_cloud_collector([visible_cloud, hidden_cloud])
        hide_targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, True, hide_report)
        unhide_report = self._report()
        self._set_cloud_collector([visible_cloud, hidden_cloud])
        unhide_targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, False, unhide_report)

        self.assertEqual([(owner_view, [visible_cloud.Id])], hide_targets)
        self.assertEqual([(owner_view, [hidden_cloud.Id])], unhide_targets)
        self.assertEqual(1, hide_report['already_in_requested_state'])
        self.assertEqual(1, unhide_report['already_in_requested_state'])

    def test_hide_operates_on_the_cloud_owner_view(self):
        owner_view = FakeView(20)
        sheet = FakeSheet(10, placed_view_ids=[owner_view.Id])
        cloud = FakeCloud(
            100, 7, hidden=False, owner_value=20, sheet_values=[10])
        document = FakeDocument({owner_view.Id: owner_view, sheet.Id: sheet})
        self._set_cloud_collector([cloud])
        report = self._report()
        targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, True, report)
        self.command.revit = types.SimpleNamespace(
            doc=document, Transaction=FakeTransaction)

        self.command._apply_changes(
            targets, [sheet], [FakeElementId(7)], True, report)

        self.assertEqual([cloud.Id], owner_view.hidden_ids)

    def test_hide_uses_sheet_cloud_ids_when_owner_is_not_directly_placed(self):
        owner_view = FakeView(20)
        placed_dependent_view = FakeView(21, owner_view.Id)
        cloud = FakeCloud(100, 7, hidden=False, owner_value=20)
        sheet = FakeSheet(
            10,
            placed_view_ids=[placed_dependent_view.Id],
            revision_cloud_ids=[cloud.Id])
        document = FakeDocument({
            owner_view.Id: owner_view,
            placed_dependent_view.Id: placed_dependent_view,
            sheet.Id: sheet,
            cloud.Id: cloud,
        })
        self._set_cloud_collector([cloud])
        report = self._report()

        targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, True, report)
        self.command.revit = types.SimpleNamespace(
            doc=document, Transaction=FakeTransaction)
        self.command._apply_changes(
            targets, [sheet], [FakeElementId(7)], True, report)

        self.assertEqual([cloud.Id], owner_view.hidden_ids)
        self.assertEqual([cloud.Id], placed_dependent_view.hidden_ids)

    def test_unhide_operates_on_the_directly_placed_cloud_owner_view(self):
        owner_view = FakeView(20)
        sheet = FakeSheet(10, placed_view_ids=[owner_view.Id])
        cloud = FakeCloud(100, 7, hidden=True, owner_value=20)
        document = FakeDocument({owner_view.Id: owner_view, sheet.Id: sheet})
        self._set_cloud_collector([cloud])
        report = self._report()
        targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, False, report)
        self.command.revit = types.SimpleNamespace(
            doc=document, Transaction=FakeTransaction)

        self.command._apply_changes(
            targets, [sheet], [FakeElementId(7)], False, report)

        self.assertEqual([cloud.Id], owner_view.unhidden_ids)

    def test_unhide_handles_a_hidden_cloud_in_placed_dependent_view(self):
        owner_view = FakeView(20)
        placed_dependent_view = FakeView(21, owner_view.Id)
        sheet = FakeSheet(10, placed_view_ids=[placed_dependent_view.Id])
        cloud = FakeCloud(100, 7, hidden=True, owner_value=20)
        document = FakeDocument({
            owner_view.Id: owner_view,
            placed_dependent_view.Id: placed_dependent_view,
            sheet.Id: sheet,
            cloud.Id: cloud,
        })
        self._set_cloud_collector([cloud])
        report = self._report()
        targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, False, report)
        self.command.revit = types.SimpleNamespace(
            doc=document, Transaction=FakeTransaction)

        self.command._apply_changes(
            targets, [sheet], [FakeElementId(7)], False, report)

        self.assertEqual([cloud.Id], owner_view.unhidden_ids)
        self.assertEqual([cloud.Id], placed_dependent_view.unhidden_ids)

    def test_hide_targets_cloud_owned_directly_by_selected_sheet(self):
        sheet = FakeSheet(10)
        cloud = FakeCloud(100, 7, hidden=False, owner_value=10)
        document = FakeDocument({sheet.Id: sheet})
        self._set_cloud_collector([cloud])
        report = self._report()

        targets = self.command._matching_clouds_by_owner_view(
            document, [sheet], {7}, True, report)
        self.command.revit = types.SimpleNamespace(
            doc=document, Transaction=FakeTransaction)
        self.command._apply_changes(
            targets, [sheet], [FakeElementId(7)], True, report)

        self.assertEqual([cloud.Id], sheet.hidden_ids)

    def test_schedule_updates_every_selected_sheet_without_matching_clouds(self):
        revision_one = FakeElementId(1)
        revision_two = FakeElementId(2)
        sheet_a = FakeSheet(10, additional_ids=[revision_one])
        sheet_b = FakeSheet(11, additional_ids=[])
        report = self._report()

        self.command._update_sheet_revision_schedules(
            [sheet_a, sheet_b], [revision_one, revision_two], True, report)

        self.assertEqual([1, 2], [item.Value for item in sheet_a.saved_revision_ids])
        self.assertEqual([1, 2], [item.Value for item in sheet_b.saved_revision_ids])
        self.assertEqual(3, report['schedule_entries_changed'])

    def test_schedule_turn_off_removes_selected_revisions_on_every_sheet(self):
        revision_one = FakeElementId(1)
        revision_two = FakeElementId(2)
        sheet_a = FakeSheet(10, additional_ids=[revision_one, revision_two])
        sheet_b = FakeSheet(11, additional_ids=[revision_two])
        report = self._report()

        self.command._update_sheet_revision_schedules(
            [sheet_a, sheet_b], [revision_one, revision_two], False, report)

        self.assertEqual([], sheet_a.saved_revision_ids)
        self.assertEqual([], sheet_b.saved_revision_ids)
        self.assertEqual(3, report['schedule_entries_changed'])

    def test_unhide_leaves_every_selected_sheet_schedule_unchanged(self):
        revision = FakeElementId(1)
        sheet = FakeSheet(10, additional_ids=[revision])
        self.command.revit = types.SimpleNamespace(
            doc=object(), Transaction=FakeTransaction)
        report = self._report()

        self.command._apply_changes([], [sheet], [revision], False, report)

        self.assertIsNone(sheet.saved_revision_ids)
        self.assertEqual(0, report['schedule_entries_changed'])

    def _report(self):
        return {
            'clouds_changed': 0,
            'already_in_requested_state': 0,
            'not_hideable': 0,
            'state_check_errors': 0,
            'views_without_matching_clouds': [],
            'cloud_errors': [],
            'schedule_entries_changed': 0,
            'schedule_entries_already_in_state': 0,
            'schedule_errors': [],
        }


class FakeTransaction(object):
    def __init__(self, *unused_args, **unused_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, unused_type, unused_value, unused_traceback):
        return False


if __name__ == '__main__':
    unittest.main()
