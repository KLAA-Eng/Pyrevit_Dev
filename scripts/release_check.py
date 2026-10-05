"""Run the repository release gates without changing release or Git state."""

import argparse
import ast
import datetime
import io
import json
import os
import re
import subprocess
import sys

import check_tool_metadata as metadata
import generate_build_info as generator


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB_NAMES = ('KL&A Tools_dev.tab', 'KL&A Tools.tab')


def read_text(path):
    with io.open(path, encoding='utf-8-sig') as stream:
        return stream.read()


def git(*args):
    return subprocess.check_output(['git', '-C', ROOT] + list(args),
                                   stderr=subprocess.PIPE).decode('utf-8').strip()


def build_values(source):
    """Read generated constants without executing a module."""
    values = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            raise ValueError('build_info.py must contain generated constant assignments only')
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id in values:
            raise ValueError('build_info.py has an invalid or duplicate constant')
        values[target.id] = ast.literal_eval(node.value)
    return values


def ledger_rows(source):
    header = ['main delivery', 'main commit', 'delivery date', 'extension version',
              'tag / release evidence', 'delivery form']
    rows = metadata._table_rows(source)
    result = {}
    for index, row in enumerate(rows):
        if [cell.lower() for cell in row] == header:
            for item in rows[index + 1:]:
                if len(item) != 6:
                    break
                if item[0] != '---':
                    if item[0] in result:
                        raise ValueError('duplicate ledger delivery: ' + item[0])
                    result[item[0]] = item
            return result
    raise ValueError('delivery ledger table is missing')


def identity_errors(payload, build, changelog, readme, ledger, tabs):
    """Check authority, generated identity, layout, and prepared release records."""
    generator.validate_payload(payload)
    errors = []
    expected = {'VERSION': payload['version'], 'CHANNEL': payload['channel'],
                'RELEASE_DATE': payload['release_date'],
                'VERSION_LABEL': generator.expected_version_label(payload['version'], payload['channel'])}
    for key, value in expected.items():
        if build.get(key) != value:
            errors.append('build_info.{} must match version.json ({})'.format(key, value))
    if 'GIT_TAG' in build or 'GIT_SHA' in build:
        errors.append('replace ambiguous generated GIT_TAG/GIT_SHA with explicit identity/source fields')
    if not re.match(r'^[0-9a-f]{40}$', str(build.get('METADATA_SOURCE_SHA', ''))):
        errors.append('METADATA_SOURCE_SHA must record a full commit SHA at generation')
    try:
        date = build.get('BUILD_DATE', '')
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            raise ValueError('invalid format')
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except (ValueError, TypeError):
        errors.append('BUILD_DATE must be a valid ISO date')
    expected_tab = TAB_NAMES[0] if payload['channel'] == 'dev' else TAB_NAMES[1]
    if tabs != [expected_tab]:
        errors.append('identity requires exactly one active ribbon: ' + expected_tab)
    if expected['VERSION_LABEL'] not in readme:
        errors.append('README must state the current version identity')
    release_heading = '## {} - {}'.format(payload['version'], payload['release_date'])
    headings = re.findall(r'^## (\S+) - (\d{4}-\d{2}-\d{2})$', changelog, re.MULTILINE)
    if payload['channel'] == 'dev':
        unreleased = changelog.split('## Unreleased', 1)
        section = unreleased[1].split('\n## ', 1)[0] if len(unreleased) == 2 else ''
        if payload['version'] not in section:
            errors.append('CHANGELOG Unreleased must identify the current dev version')
        if any(version == payload['version'] for version, _date in headings):
            errors.append('dev identity must not have a changelog release entry')
    else:
        if not headings or headings[0] != (payload['version'], payload['release_date']):
            errors.append('latest changelog release must match version.json version/date')
        section = changelog.split(release_heading, 1)
        notes = section[1].split('\n## ', 1)[0] if len(section) == 2 else ''
        if '**Channel:** ' + payload['channel'].capitalize() not in notes:
            errors.append('changelog channel must match version.json')
        if '**Tag:** `' + expected['VERSION_LABEL'] + '`' not in notes:
            errors.append('changelog tag must match the release identity')
        row = ledger.get(payload['version'])
        expected_date = datetime.datetime.strptime(payload['release_date'], '%Y-%m-%d').strftime('%m.%d.%Y')
        if not row or row[2] != expected_date or row[3] != payload['version']:
            errors.append('ledger requires a release row with matching version/date')
    if not headings:
        errors.append('CHANGELOG must retain the latest published release history')
    if headings:
        latest = headings[0][0]
        if latest not in ledger:
            errors.append('latest published release is missing from the delivery ledger')
        if latest not in readme:
            errors.append('README must retain the latest published release version')
        if payload['channel'] == 'dev' and latest in ledger:
            row = ledger[latest]
            if not re.match(r'^[0-9a-f]{7,40}$', row[1]) or 'pending' in ' '.join(row).lower():
                errors.append('latest published delivery evidence must be resolved before dev preparation is complete')
    return errors


def delivery_errors(version, ledger, git_call=git):
    """Verify resolved ledger evidence against local objects, never the network."""
    row = ledger.get(version)
    if not row:
        return ['delivery is missing from the ledger: ' + version]
    if row[0] != version or row[3] != version:
        return ['delivery identifier and extension version must match the requested delivery']
    if not re.match(r'^[0-9a-f]{7,40}$', row[1]) or 'pending' in ' '.join(row).lower():
        return ['delivery commit/publication evidence is still pending: ' + version]
    tags = re.findall(r'(?<![\w.-])(v\d+\.\d+\.\d+(?:-beta)?)(?![\w.-])', row[4])
    if len(set(tags)) != 1 or '/releases/tag/' not in row[4]:
        return ['delivery requires one release tag and a recorded publication URL']
    tag = tags[0]
    try:
        commit = git_call('rev-parse', row[1] + '^{commit}')
        if git_call('cat-file', '-t', 'refs/tags/' + tag) != 'tag':
            return ['release tag must be annotated: ' + tag]
        if git_call('rev-parse', 'refs/tags/' + tag + '^{}') != commit:
            return ['release tag does not peel to the ledger main commit']
        payload = json.loads(git_call('show', commit + ':version.json'))
        if (payload.get('version') != row[3] or payload.get('channel') not in ('beta', 'stable') or
                generator.expected_version_label(payload['version'], payload['channel']) != tag):
            return ['tagged version/channel does not match ledger evidence']
        date = datetime.datetime.strptime(payload['release_date'], '%Y-%m-%d').strftime('%m.%d.%Y')
        if date != row[2]:
            return ['tagged release date does not match ledger evidence']
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError) as error:
        return ['cannot verify delivery objects: ' + str(error)]
    return []


def check_identity(delivery=None):
    try:
        payload = json.loads(read_text(os.path.join(ROOT, 'version.json')))
        build = build_values(read_text(os.path.join(ROOT, 'lib', 'build_info.py')))
        ledger = ledger_rows(read_text(metadata.DELIVERY_LEDGER))
        errors = identity_errors(payload, build, read_text(os.path.join(ROOT, 'CHANGELOG.md')),
                                 read_text(os.path.join(ROOT, 'README.md')), ledger,
                                 [name for name in TAB_NAMES if os.path.isdir(os.path.join(ROOT, name))])
        sha = build.get('METADATA_SOURCE_SHA', '')
        if re.match(r'^[0-9a-f]{40}$', sha):
            git('cat-file', '-e', sha + '^{commit}')
        if payload['channel'] == 'dev':
            if git('tag', '--list', build['VERSION_LABEL']):
                errors.append('dev identity must remain untagged')
        if delivery:
            errors.extend(delivery_errors(delivery, ledger))
        for error in errors:
            print('Identity: ' + error)
        return 1 if errors else 0
    except (OSError, ValueError, TypeError, KeyError, SyntaxError, subprocess.CalledProcessError) as error:
        print('Identity: ' + str(error))
        return 1


def run_command(label, args):
    print('\n' + label, flush=True)
    try:
        return subprocess.call(args, cwd=ROOT)
    except OSError as error:
        print(str(error))
        return 1


def check_untracked_whitespace():
    """Include new source/docs that ordinary git diff does not yet inspect."""
    try:
        errors = []
        for name in git('ls-files', '--others', '--exclude-standard', '-z').split('\0'):
            if not name or os.path.splitext(name)[1].lower() not in ('.py', '.ps1', '.md', '.yaml', '.yml'):
                continue
            lines = read_text(os.path.join(ROOT, name)).splitlines()
            for number, line in enumerate(lines, 1):
                if line.endswith((' ', '\t')):
                    errors.append('{}:{}: trailing whitespace'.format(name, number))
            if lines and not lines[-1]:
                errors.append(name + ': blank line at EOF')
        for error in errors:
            print(error)
        return 1 if errors else 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error))
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', help='also verify a completed ledger delivery against local Git objects')
    args = parser.parse_args(argv)
    results = [run_command('Full test discovery', [sys.executable, '-m', 'unittest', 'discover',
                                                 '-s', 'tests', '-p', '*_test.py']),
               run_command('Visible-command metadata audit', [sys.executable, 'scripts/check_tool_metadata.py'])]
    for label, arguments in [('Working-tree whitespace', ['diff', '--check']),
                             ('Staged whitespace', ['diff', '--cached', '--check']),
                             ('Release-delta whitespace (fetch origin first)', ['diff', '--check', 'origin/main...HEAD'])]:
        results.append(run_command(label, ['git', '-C', ROOT] + arguments))
    print('\nNew-file whitespace', flush=True)
    results.append(check_untracked_whitespace())
    print('\nExtension identity and release records', flush=True)
    results.append(check_identity(args.delivery))
    failed = sum(bool(result) for result in results)
    print('\nRelease check: {} gate(s) failed. Live Revit/Excel and remote publication require separate evidence.'.format(failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
