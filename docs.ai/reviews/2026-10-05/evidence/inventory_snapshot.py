"""Reproduce review inventories; run with Python 3 and Pillow from repository root.

Only writes CSV/JSON evidence beside this script. Does not import Revit code.
PNG color checks are measurements, not automatic findings about design intent.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import check_tool_metadata as metadata


def write_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    tracked = [p for p in tracked if p]
    commands = []
    for name in metadata.visible_bundles(str(ROOT)):
        path = Path(name)
        script = path / 'script.py'
        commands.append(dict(path=path.relative_to(ROOT).as_posix(),
                             kind=path.suffix[1:],
                             panel=path.relative_to(ROOT).parts[1],
                             script_lines=len(script.read_text(encoding='utf-8-sig').splitlines()) if script.exists() else 0,
                             spec=(path / 'SPEC.md').exists(),
                             icon=(path / 'icon.png').exists(),
                             metadata_errors='; '.join(metadata.validate_bundle(str(path)))))
    write_csv('commands.csv', commands)
    xamls = []
    for name in tracked:
        if not name.lower().endswith('.xaml'):
            continue
        path = ROOT / name
        try:
            root = ET.parse(path).getroot()
            elements = list(root.iter())
            xamls.append(dict(path=name, root=root.tag.split('}')[-1],
                              class_name=root.get('{http://schemas.microsoft.com/winfx/2006/xaml}Class', ''),
                              width=root.get('Width', ''), height=root.get('Height', ''),
                              resize_mode=root.get('ResizeMode', ''),
                              controls=len(elements),
                              automation_attributes=sum('AutomationProperties.' in key for element in elements for key in element.attrib),
                              parse_error=''))
        except ET.ParseError as error:
            xamls.append(dict(path=name, root='', class_name='', width='', height='', resize_mode='', controls=0,
                              automation_attributes=0, parse_error=str(error)))
    write_csv('xaml.csv', xamls)
    icons = []
    palette = {'orange': (255, 128, 0), 'green': (51, 113, 79), 'light': (229, 228, 226), 'dark': (26, 37, 43)}
    for name in tracked:
        if not name.lower().endswith('.png') or not (name.startswith('lib/_icons/') or (name.startswith('KL&A Tools_dev.tab/') and Path(name).name.startswith('icon'))):
            continue
        path = ROOT / name
        with Image.open(path) as original:
            rgba = original.convert('RGBA')
            pixels = list(rgba.getdata())
            solid = collections.Counter(pixel[:3] for pixel in pixels if pixel[3] >= 250)
            visible = sum(pixel[3] > 0 for pixel in pixels)
            token = path.stem.rsplit('_', 1)[-1]
            expected = palette.get(token)
            mismatch = sum(count for rgb, count in solid.items() if expected and max(abs(a-b) for a,b in zip(rgb, expected)) > 3)
            icons.append(dict(path=name, width=original.width, height=original.height, mode=original.mode,
                              alpha_min=min(pixel[3] for pixel in pixels), alpha_max=max(pixel[3] for pixel in pixels),
                              visible_pixels=visible, opaque_color_count=len(solid),
                              dominant_opaque_color=('#%02X%02X%02X' % solid.most_common(1)[0][0]) if solid else '',
                              named_token=token if expected else '', off_token_opaque_pixels=mismatch if expected else '',
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write_csv('icons.csv', icons)
    summary = dict(baseline_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                   commands=len(commands), commands_by_panel=dict(collections.Counter(p['panel'] for p in commands)),
                   xaml=len(xamls), xaml_by_root=dict(collections.Counter(p['root'] for p in xamls)),
                   source_pngs=sum(p['path'].startswith('lib/_icons/') for p in icons),
                   ribbon_pngs=sum(p['path'].startswith('KL&A Tools_dev.tab/') for p in icons),
                   source_pngs_over_96=[p['path'] for p in icons if p['path'].startswith('lib/_icons/') and max(p['width'], p['height']) > 96],
                   named_source_token_mismatches=[p['path'] for p in icons if p['off_token_opaque_pixels']],
                   opaque_ribbon_icons=[p['path'] for p in icons if p['path'].startswith('KL&A Tools_dev.tab/') and p['alpha_min'] == 255],
                   source_files=dict(collections.Counter(Path(p).suffix.lower() for p in tracked if Path(p).suffix.lower() in ('.py', '.cs', '.xaml', '.csproj'))))
    (OUT / 'inventory-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
