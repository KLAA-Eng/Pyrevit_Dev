"""Host-independent ForteWEB .4wf reader/writer.

A .4wf file is a JSON array: a project header followed by one detail record per
member. New members are cloned from a template file that contains one member of
each kind (``floor_joist``, ``roof_dropbeam`` ...).
"""

from __future__ import division, print_function

import copy
import io
import json


PSF = 1.0 / 144.0
STANDARD_SPACINGS_TEXT = '12/16/19.2/24/32'

# Which template member/support each detected support type is copied from.
# !! These are best guesses from the sample file - confirm in ForteWEB and edit !!
SUPPORT_SOURCE = {
    'hanger': ('floor_flushbeam', 0),   # SupportType 6, Accessory 4
    'beam': ('floor_joist', 0),         # SupportType 6, Accessory 0
    'wall': ('floor_joist', 1),         # SupportType 0
    'column': ('floor_dropbeam', 0),    # SupportType 8
}


def member_kind(summary):
    return '%s_%s' % (summary['StructuralSystemStringTag'], summary['MemberTypeStringTag'])


def parse_templates(data):
    """Return (header, {kind: (summary, detail)}) from parsed .4wf JSON."""
    header = data[0]
    details = dict((d['MemberIDTag'], d) for d in data[1:])
    templates = {}
    for container in header['MemberManagerData']['MemberContainers']:
        for summary in container['Members']:
            templates.setdefault(member_kind(summary), (summary, details[summary['IDTag']]))
    return header, templates


def load_templates(template_path):
    with io.open(template_path, 'r', encoding='utf-8-sig') as stream:
        return parse_templates(json.loads(stream.read()))


def apply_spacing(summary, detail, spacing, name, warnings):
    """Joists only: set o.c. spacing on the summary row and in the product spacing list."""
    if summary['MemberTypeStringTag'] != 'joist' or not spacing:
        return
    summary['Spacing'] = spacing
    options = detail['ProductSelectionData'].get('Spacings') or []
    match = [option for option in options if abs(option['Key'] - spacing) < 0.05]
    for option in options:
        option['Value']['Selected'] = bool(match) and option is match[0]
    if match:
        detail['ProductSelectionData']['CustomSpacing'] = 0.0
    else:
        detail['ProductSelectionData']['CustomSpacing'] = spacing
        if warnings is not None:
            warnings.append('%s: %.2f" is not a standard spacing (%s) - written as '
                            'custom spacing, check in ForteWEB'
                            % (name, spacing, STANDARD_SPACINGS_TEXT))


def build_members(header, templates, members, warnings=None):
    """Return the .4wf JSON list for ``members`` using parsed template data.

    members: list of dicts
      name, kind, span_in, notes (opt), spacing_in (opt)
      supports: [{"type": hanger|beam|wall|column|None, "width": in}, {...}]
      optional: trib_in, loads_psf {class_number: psf}
    """
    header = copy.deepcopy(header)
    container = header['MemberManagerData']['MemberContainers'][0]

    summaries, details, tags, reactions = [], [], {}, {}
    for index, member in enumerate(members):
        if member['kind'] not in templates:
            raise ValueError("Template has no '%s' member. Available: %s"
                             % (member['kind'], ', '.join(sorted(templates))))
        t_sum, t_det = templates[member['kind']]
        sups = member['supports']
        b0, b1 = sups[0]['width'], sups[-1]['width']

        summary = copy.deepcopy(t_sum)
        template_span = sum(span['SpanLength'] for span in t_det['SpansData']['Spans'])
        summary.update({
            'ContainerID': container['ContainerID'], 'MemberID': index, 'IDTag': index,
            'MemberName': member['name'], 'Notes': member.get('notes', ''),
            'PAEServiceMemberID': '', 'PAEVersion': '', 'PAEDataVersion': '',
            'LoadBearingLength': b0, 'LoadBearingLengthFriendly': '%.2f"' % b0,
            'MemberLength': round(t_sum['MemberLength'] + member['span_in'] - template_span, 3),
            'DesignResult': 'ND', 'ProblemIsDesigned': False,
            'HasValidPaeSolution': False, 'UtilizationPercent': '',
            'UtilizationCode': '', 'ErrorString': ''})
        summaries.append(summary)
        tags[str(index)] = {'Key': container['ContainerID'], 'Value': index}
        reactions[str(index)] = {'FromReactions': [], 'ToReactions': []}

        detail = copy.deepcopy(t_det)
        detail['MemberIDTag'] = index
        detail['SpansData']['Spans'] = [{'SpanLength': round(member['span_in'], 3)}]

        t_supports = detail['SupportsData']['Supports']
        for slot, support in ((0, sups[0]), (len(t_supports) - 1, sups[-1])):
            if support.get('type') in SUPPORT_SOURCE:
                src_kind, src_index = SUPPORT_SOURCE[support['type']]
                if src_kind in templates:
                    t_supports[slot] = copy.deepcopy(
                        templates[src_kind][1]['SupportsData']['Supports'][src_index])
            t_supports[slot]['Width'] = support['width']
            t_supports[slot]['Width_friendly'] = '%.2f"' % support['width']

        full_length = round(member['span_in'] + b0 + b1, 3)
        y_loads = detail['HorizontalYAxisLoadData']
        if y_loads:
            trib = member.get('trib_in')
            for load in y_loads['LoadGroups']['0']['LoadDefs']:
                if load.get('IsFullLength', True):
                    load['StartLocation'], load['EndLocation'] = 0.0, full_length
                if trib:
                    load['StartTribWidth'] = load['EndTribWidth'] = trib
                    load['TribWidthIsDefault'] = False
                for load_class, psf in (member.get('loads_psf') or {}).items():
                    load['Loads'][str(load_class)]['StartMagnitude'] = psf * PSF
                    load['Loads'][str(load_class)]['EndMagnitude'] = psf * PSF
            if trib:
                y_loads['DefaultTribWidth'] = trib

        apply_spacing(summary, detail, member.get('spacing_in'), member['name'], warnings)

        detail['SolutionsData']['SolutionList'] = []
        detail['SolutionsData']['DesignResultsProductPasses'] = False
        detail['ConnectorOutputData'] = {'DesignedConnectors': None, 'PreviousConnectors': None}
        detail['ReportOutputHorizontalData'] = {'HorizontalMemberReportData': None,
                                                'PostDesignGraphicData': None}
        details.append(detail)

    container['Members'] = summaries
    manager = header['MemberManagerData']
    manager['MemberContainers'] = [container]
    manager['MemberTagCollection'] = tags
    manager['MemberTagToLinkedReactionDictionary'] = reactions
    manager['SelectedContainerID'] = manager['SelectedMemberID'] = -1
    header['SelectedMemberIDTag'] = -1
    return [header] + details


def build_4wf(template_path, out_path, members, warnings=None):
    """Write a .4wf file for ``members`` cloned from ``template_path``."""
    header, templates = load_templates(template_path)
    data = build_members(header, templates, members, warnings)
    text = json.dumps(data, separators=(',', ':'))   # ASCII-escaped
    with io.open(out_path, 'w', encoding='utf-8') as stream:
        stream.write(u'' + text)
    return out_path
