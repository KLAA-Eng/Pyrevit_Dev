#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scale lint for KLCode XAML.

Strict files (the shared foundation dictionaries) may not carry numeric layout literals at all: every
size, gap, radius and border weight is a typed token in KLCodeFoundationTokens.xaml. Consumer windows are
reported: any Margin / Padding component that is not on the 4 / 8 / 12 / 16 / 24 spacing scale (or 0)
is listed with its file and line, so the drift is visible without failing the build until the owner
decides to make it fail (``--fail-on-report``).

Runs under CPython 3 and IronPython 2.7; no third-party modules.
"""
from __future__ import print_function

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRICT = ('lib/GUI/Resources/KLCodeFoundation.xaml', 'lib/GUI/Resources/KLCodeComponents.xaml')
EXEMPT = ('lib/GUI/Resources/KLCodeSharedPrimitives.xaml',)  # merges only the palette, so it cannot name tokens
SCALE = (0, 4, 8, 12, 16, 24)
LAYOUT = ('Margin', 'Padding', 'Width', 'Height', 'MinWidth', 'MinHeight', 'MaxWidth', 'MaxHeight',
          'CornerRadius', 'BorderThickness', 'FontSize', 'StrokeThickness', 'KeyboardIncrement')
SPACING = ('Margin', 'Padding')
NUMBER = r'-?[0-9]+(?:\.[0-9]+)?'
ATTR = re.compile(r'\b(%s)="(%s(?:,%s){0,3})"' % ('|'.join(LAYOUT), NUMBER, NUMBER))
SETTER = re.compile(r'Property="(%s)"\s+Value="(%s(?:,%s){0,3})"' % ('|'.join(LAYOUT), NUMBER, NUMBER))


def literals(text):
    """Yield (line, property, value) for every numeric layout literal in a XAML text."""
    for number, line in enumerate(text.splitlines(), 1):
        for pattern in (ATTR, SETTER):
            for match in pattern.finditer(line):
                yield number, match.group(1), match.group(2)


def strict_violations(text):
    return [(line, prop, value) for line, prop, value in literals(text)
            if any(float(part) != 0 for part in value.split(','))]


def off_scale(text):
    return [(line, prop, value) for line, prop, value in literals(text)
            if prop in SPACING and any(float(part) not in SCALE for part in value.split(','))]


def consumer_files(root):
    for base in ('lib/GUI', 'lib/match', 'KL&A Tools_dev.tab', 'src'):
        for directory, folders, files in os.walk(os.path.join(root, base)):
            folders[:] = [f for f in folders if f not in ('bin', 'obj', '_Templates', '__pycache__')]
            for name in files:
                if name.endswith('.xaml'):
                    path = os.path.relpath(os.path.join(directory, name), root).replace(os.sep, '/')
                    if path not in STRICT and path not in EXEMPT and 'locale' not in path and 'ResourceDictionary' not in name:
                        yield path


def read(root, path):
    with io.open(os.path.join(root, path), 'r', encoding='utf-8') as stream:
        return stream.read()


def main(argv):
    root = ROOT
    fail_on_report = '--fail-on-report' in argv
    failures = 0
    for path in STRICT:
        for line, prop, value in strict_violations(read(root, path)):
            print('STRICT  %s:%d %s="%s" is a literal; use a token' % (path, line, prop, value))
            failures += 1
    reported = 0
    for path in consumer_files(root):
        for line, prop, value in off_scale(read(root, path)):
            print('REPORT  %s:%d %s="%s" is off the 4/8/12/16/24 scale' % (path, line, prop, value))
            reported += 1
    print('check_ui_scale: %d strict violation(s), %d off-scale consumer literal(s)' % (failures, reported))
    return 1 if failures or (fail_on_report and reported) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
