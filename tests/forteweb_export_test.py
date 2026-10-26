from __future__ import print_function

import json
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.forteweb_export.fourwf import build_4wf, build_members, parse_templates
from lib.forteweb_export.workflow import (
    beam_kind,
    clear_span_in,
    fmt_ftin,
    median_spacing_in,
    parse_tolerance,
    plan_closest,
    structural_system,
    system_member_labels,
)


def _member(id_tag, system, member_type):
    summary = {'IDTag': id_tag, 'StructuralSystemStringTag': system,
               'MemberTypeStringTag': member_type, 'MemberLength': 130.0}
    detail = {
        'MemberIDTag': id_tag,
        'SpansData': {'Spans': [{'SpanLength': 120.0}]},
        'SupportsData': {'Supports': [{'Width': 3.5, 'Source': '%s-0' % member_type},
                                      {'Width': 3.5, 'Source': '%s-1' % member_type}]},
        'HorizontalYAxisLoadData': {'DefaultTribWidth': 16.0, 'LoadGroups': {'0': {'LoadDefs': [
            {'IsFullLength': True, 'StartLocation': 0.0, 'EndLocation': 127.0,
             'Loads': {'1': {'StartMagnitude': 0.0, 'EndMagnitude': 0.0}}}]}}},
        'ProductSelectionData': {'CustomSpacing': 0.0, 'Spacings': [
            {'Key': 16.0, 'Value': {'Selected': True}},
            {'Key': 24.0, 'Value': {'Selected': False}}]},
        'SolutionsData': {'SolutionList': ['old'], 'DesignResultsProductPasses': True},
        'ConnectorOutputData': {}, 'ReportOutputHorizontalData': {},
    }
    return summary, detail


def _template():
    pairs = [_member(0, 'floor', 'joist'), _member(1, 'floor', 'flushbeam'),
             _member(2, 'floor', 'dropbeam')]
    header = {'SelectedMemberIDTag': 0, 'MemberManagerData': {
        'MemberContainers': [{'ContainerID': 7, 'Members': [p[0] for p in pairs]}],
        'MemberTagCollection': {}, 'MemberTagToLinkedReactionDictionary': {},
        'SelectedContainerID': 7, 'SelectedMemberID': 0}}
    return [header] + [p[1] for p in pairs]


def _joist(**overrides):
    member = {'name': 'J1', 'kind': 'floor_joist', 'span_in': 150.0, 'notes': 'Revit Id 5',
              'supports': [{'type': 'wall', 'width': 5.5}, {'type': 'hanger', 'width': 3.5}]}
    member.update(overrides)
    return member


class ForteWebWriterTests(unittest.TestCase):
    def setUp(self):
        self.header, self.templates = parse_templates(_template())

    def test_templates_are_keyed_by_system_and_member_type(self):
        self.assertEqual(sorted(self.templates),
                         ['floor_dropbeam', 'floor_flushbeam', 'floor_joist'])

    def test_member_span_length_and_supports_are_written(self):
        data = build_members(self.header, self.templates, [_joist()])
        summary = data[0]['MemberManagerData']['MemberContainers'][0]['Members'][0]
        detail = data[1]

        self.assertEqual(summary['MemberName'], 'J1')
        self.assertEqual(summary['MemberLength'], 160.0)
        self.assertEqual(summary['LoadBearingLength'], 5.5)
        self.assertEqual(detail['SpansData']['Spans'], [{'SpanLength': 150.0}])
        supports = detail['SupportsData']['Supports']
        self.assertEqual(supports[0]['Source'], 'joist-1')        # wall
        self.assertEqual(supports[1]['Source'], 'flushbeam-0')    # hanger
        self.assertEqual([s['Width'] for s in supports], [5.5, 3.5])
        load = detail['HorizontalYAxisLoadData']['LoadGroups']['0']['LoadDefs'][0]
        self.assertEqual(load['EndLocation'], 159.0)
        self.assertEqual(detail['SolutionsData']['SolutionList'], [])

    def test_template_data_is_not_mutated(self):
        build_members(self.header, self.templates, [_joist(spacing_in=24.0)])
        self.assertEqual(self.header['SelectedMemberIDTag'], 0)
        self.assertEqual(self.templates['floor_joist'][1]['SpansData']['Spans'],
                         [{'SpanLength': 120.0}])

    def test_standard_spacing_selects_matching_option(self):
        warnings = []
        data = build_members(self.header, self.templates, [_joist(spacing_in=24.0)], warnings)
        options = data[1]['ProductSelectionData']['Spacings']
        self.assertEqual([o['Value']['Selected'] for o in options], [False, True])
        self.assertEqual(warnings, [])

    def test_nonstandard_spacing_is_custom_with_warning(self):
        warnings = []
        data = build_members(self.header, self.templates, [_joist(spacing_in=18.0)], warnings)
        self.assertEqual(data[1]['ProductSelectionData']['CustomSpacing'], 18.0)
        self.assertEqual(len(warnings), 1)

    def test_beams_never_receive_spacing(self):
        data = build_members(self.header, self.templates,
                             [_joist(kind='floor_flushbeam', spacing_in=18.0)])
        self.assertNotIn('Spacing', data[0]['MemberManagerData']['MemberContainers'][0]['Members'][0])

    def test_missing_template_kind_is_reported(self):
        with self.assertRaises(ValueError):
            build_members(self.header, self.templates, [_joist(kind='roof_joist')])

    def test_build_4wf_round_trips_through_a_file(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        template = os.path.join(folder, 'template.4wf')
        with open(template, 'w') as stream:
            json.dump(_template(), stream)
        out_path = build_4wf(template, os.path.join(folder, 'out.4wf'), [_joist()])
        with open(out_path) as stream:
            data = json.load(stream)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['SelectedMemberIDTag'], -1)


class ForteWebWorkflowTests(unittest.TestCase):
    def test_plan_closest_clamps_to_segment(self):
        self.assertEqual(plan_closest(5, 3, 0, 0, 10, 0), (5, 0, 3))
        self.assertEqual(plan_closest(-4, 3, 0, 0, 10, 0), (0, 0, 5))

    def test_fmt_ftin(self):
        self.assertEqual(fmt_ftin(150.5), "12' 6.50\"")

    def test_structural_system_override_and_level_name(self):
        self.assertEqual(structural_system('Level 2 ROOF'), 'roof')
        self.assertEqual(structural_system('Level 2'), 'floor')
        self.assertEqual(structural_system(None), 'floor')
        self.assertEqual(structural_system('Roof', 'FLOOR'), 'floor')

    def test_median_spacing_ignores_duplicate_offsets(self):
        self.assertEqual(median_spacing_in([4.0, 0.0, 1.333333, 2.666667, 2.666667]), 16.0)
        self.assertEqual(median_spacing_in([0.0, 2.0, 4.0, 5.333333]), 24.0)
        self.assertIsNone(median_spacing_in([1.0]))

    def test_clear_span_uses_inside_faces(self):
        self.assertEqual(clear_span_in({'s': 0.0, 'width': 4.0}, {'s': 120.0, 'width': 6.0}), 115.0)

    def test_beam_kind_prefers_framing_then_level(self):
        self.assertEqual(beam_kind(2, 1)[0], 'dropbeam')
        self.assertEqual(beam_kind(1, 1)[0], 'flushbeam')
        self.assertEqual(beam_kind(0, 0, 1.5, 'L2')[0], 'flushbeam')
        self.assertEqual(beam_kind(0, 0, 12.0, 'L2')[0], 'dropbeam')
        self.assertEqual(beam_kind(0, 0)[0], 'flushbeam')

    def test_system_member_labels(self):
        self.assertEqual(system_member_labels('FJ-1', [120]), [(120, 'FJ-1')])
        self.assertEqual(system_member_labels('FJ-1', [96, 120]),
                         [(120, 'FJ-1 - 1'), (96, 'FJ-1 - 2')])

    def test_parse_tolerance(self):
        self.assertEqual(parse_tolerance('0.75'), 0.75)
        self.assertIsNone(parse_tolerance('-1'))
        self.assertIsNone(parse_tolerance('abc'))


if __name__ == '__main__':
    unittest.main()
