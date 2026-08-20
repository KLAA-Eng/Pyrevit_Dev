from __future__ import print_function

import os
import re
import sys
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.ui_gallery.catalog import catalog_xaml_sources
from lib.ui_gallery.launchers import gallery_launchers


OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'docs', 'ui-gallery', 'window-previews')

PALETTE = {
    'background': (26, 37, 43),
    'panel': (229, 228, 226),
    'surface': (245, 246, 247),
    'surface_dark': (40, 96, 72),
    'accent': (51, 113, 79),
    'accent_hover': (64, 112, 88),
    'text': (32, 38, 43),
    'text_light': (229, 228, 226),
    'muted': (111, 121, 129),
    'line': (194, 202, 207),
    'warning': (198, 138, 31),
}


def main():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    launchers = gallery_launchers()
    entries = catalog_xaml_sources(PROJECT_ROOT)
    window_titles = dict(
        (entry['relative_path'], entry.get('title') or '')
        for entry in entries
        if entry['root_kind'] == 'Window'
    )

    rows = []
    for launcher in launchers:
        relative_path = launcher.get('relative_path')
        if not relative_path:
            continue
        window_path = os.path.join(PROJECT_ROOT, relative_path.replace('/', os.sep))
        if not os.path.exists(window_path):
            rows.append((launcher['id'], relative_path, 'missing'))
            continue
        output_name = _safe_filename(launcher['id']) + '.png'
        output_path = os.path.join(OUTPUT_DIR, output_name)
        _draw_preview(launcher, window_path, window_titles.get(relative_path, ''), output_path)
        rows.append((launcher['id'], relative_path, output_name))

    _write_manifest(rows)
    print('Wrote {} window preview PNGs to {}'.format(
        len([row for row in rows if row[2] != 'missing']), OUTPUT_DIR))


def _draw_preview(launcher, window_path, xaml_title, output_path):
    profile = _profile_for(launcher, window_path)
    width, height = profile['size']
    image = Image.new('RGB', (width, height), profile['background'])
    draw = ImageDraw.Draw(image)
    fonts = _fonts()

    _draw_header(draw, width, profile['title'] or launcher['title'] or xaml_title, fonts)
    profile['draw'](draw, fonts, width, height, launcher, window_path)
    _draw_footer(draw, width, height, launcher, fonts)
    image.save(output_path)


def _profile_for(launcher, window_path):
    launcher_id = launcher['id']
    if launcher_id == 'kla-custom-alert':
        return _profile((520, 260), PALETTE['surface'], _draw_alert)
    if launcher_id in ('kla-select-from-dict', 'kla-steel-psf'):
        return _profile((440, 520), PALETTE['background'], _draw_selection)
    if launcher_id == 'kla-create-from-rooms':
        return _profile((440, 520), PALETTE['background'], _draw_create_from_rooms)
    if launcher_id in ('kla-find-replace', 'kla-find-replace-views',
                       'kla-find-replace-views-proto'):
        return _profile((520, 420), PALETTE['background'], _draw_find_replace)
    if launcher_id in ('kla-find-replace-sheets', 'kla-find-replace-sheets-proto'):
        return _profile((620, 560), PALETTE['background'], _draw_find_replace_sheets)
    if launcher_id == 'kla-duplicate-sheets':
        return _profile((720, 620), PALETTE['background'], _draw_duplicate_sheets)
    if launcher_id == 'kla-view-range':
        return _profile((650, 420), PALETTE['surface'], _draw_view_range)
    if launcher_id == 'kla-match-properties-recall':
        return _profile((460, 430), PALETTE['surface'], _draw_match_recall)
    if launcher_id == 'ui-gallery':
        return _profile((980, 560), PALETTE['surface'], _draw_gallery)
    return _profile((460, 260), PALETTE['surface'], _draw_fixture)


def _profile(size, background, draw_func):
    return {'size': size, 'background': background, 'draw': draw_func, 'title': ''}


def _draw_header(draw, width, title, fonts):
    draw.rectangle((0, 0, width, 32), fill=PALETTE['background'])
    draw.text((10, 7), 'KLCode', fill=PALETTE['text_light'], font=fonts['bold'])
    text_width = _text_size(draw, title, fonts['bold'])[0]
    draw.text(((width - text_width) // 2, 7), title, fill=PALETTE['text_light'], font=fonts['bold'])
    _button(draw, width - 68, 6, 58, 20, 'Close', fonts['small'])


def _draw_footer(draw, width, height, launcher, fonts):
    draw.rectangle((0, height - 28, width, height), fill=PALETTE['background'])
    draw.text((12, height - 21), 'Preview PNG', fill=PALETTE['muted'], font=fonts['small'])
    text = launcher.get('relative_path') or ''
    max_chars = max(20, int(width / 8))
    if len(text) > max_chars:
        text = '...' + text[-max_chars + 3:]
    tw = _text_size(draw, text, fonts['small'])[0]
    draw.text((width - tw - 12, height - 21), text, fill=PALETTE['muted'], font=fonts['small'])


def _draw_alert(draw, fonts, width, height, launcher, window_path):
    draw.rectangle((24, 54, width - 24, height - 58), fill=(255, 255, 255), outline=PALETTE['line'])
    draw.ellipse((46, 86, 92, 132), fill=PALETTE['accent'])
    draw.text((64, 95), 'i', fill=(255, 255, 255), font=fonts['title'])
    draw.text((112, 82), 'Information', fill=PALETTE['text'], font=fonts['title'])
    draw.text((112, 116), 'Preview data is fictional and cannot modify this model.',
              fill=PALETTE['text'], font=fonts['regular'])
    _button(draw, width // 2 - 55, height - 104, 110, 28, 'OK', fonts['regular'])


def _draw_selection(draw, fonts, width, height, launcher, window_path):
    label = 'Select fictional drawing types:'
    items = ['A101 - Floor Plan', 'A201 - Building Section', 'S101 - Foundation Plan', 'M101 - HVAC Plan']
    if launcher['id'] == 'kla-steel-psf':
        label = 'Select stories to review:'
        items = ['Level 01 - Lobby', 'Level 02 - Office', 'Roof - Mechanical']
    _draw_filter(draw, fonts, width, 58, label)
    _draw_list(draw, fonts, 28, 142, width - 56, 210, items, [0, 1])
    _button(draw, 34, 372, 105, 28, 'Select All', fonts['regular'])
    _button(draw, 150, 372, 105, 28, 'Select None', fonts['regular'])
    if launcher['id'] == 'kla-steel-psf':
        _button(draw, 34, 414, 120, 28, 'Review only', fonts['regular'])
        _button(draw, 166, 414, 120, 28, 'Initialize CSV', fonts['regular'])
        _button(draw, 298, 414, 110, 28, 'Append CSV', fonts['regular'])
    else:
        _button(draw, width // 2 - 70, 414, 140, 30, 'Use selection', fonts['regular'])


def _draw_create_from_rooms(draw, fonts, width, height, launcher, window_path):
    _draw_filter(draw, fonts, width, 58, 'Select fictional room type:')
    _draw_list(draw, fonts, 28, 142, width - 56, 165,
               ['Office Area Boundary', 'Conference Room Boundary', 'Storage Room Boundary'], [0])
    draw.line((32, 330, width - 32, 330), fill=PALETTE['accent'], width=1)
    draw.text((34, 352), 'Additional Settings:', fill=PALETTE['text_light'], font=fonts['regular'])
    draw.text((50, 388), 'Offset from level (cm):', fill=PALETTE['text_light'], font=fonts['regular'])
    _textbox(draw, 220, 384, 160, 24, '15', fonts['regular'])
    _button(draw, width // 2 - 105, 430, 210, 30, 'Close preview', fonts['regular'])


def _draw_find_replace(draw, fonts, width, height, launcher, window_path):
    draw.text((38, 66), 'Fictional drawing name', fill=PALETTE['text_light'], font=fonts['regular'])
    fields = [('Find', 'Office'), ('Replace', 'Studio'), ('Prefix', 'Sample - '), ('Suffix', ' - Review')]
    y = 112
    for label, value in fields:
        draw.text((54, y + 4), label, fill=PALETTE['text_light'], font=fonts['regular'])
        _textbox(draw, 150, y, 300, 28, value, fonts['regular'])
        y += 44
    buttons = ['UPPERCASE', 'Rename', 'lowercase'] if launcher['id'].endswith('-proto') else ['Rename']
    x = 96 if len(buttons) == 3 else width // 2 - 70
    for button in buttons:
        _button(draw, x, 306, 100, 30, button, fonts['regular'])
        x += 112


def _draw_find_replace_sheets(draw, fonts, width, height, launcher, window_path):
    y = 66
    draw.text((38, y), 'Sheet Number', fill=PALETTE['text_light'], font=fonts['bold'])
    y += 34
    for label, value in [('Find', 'A'), ('Replace', 'S'), ('Prefix', 'Sample-'), ('Suffix', '-R1')]:
        draw.text((54, y + 4), label, fill=PALETTE['text_light'], font=fonts['regular'])
        _textbox(draw, 170, y, 360, 26, value, fonts['regular'])
        y += 38
    y += 12
    draw.text((38, y), 'Sheet Name', fill=PALETTE['text_light'], font=fonts['bold'])
    y += 34
    for label, value in [('Find', 'Office'), ('Replace', 'Studio'), ('Prefix', 'Sample - '), ('Suffix', ' - Review')]:
        draw.text((54, y + 4), label, fill=PALETTE['text_light'], font=fonts['regular'])
        _textbox(draw, 170, y, 360, 26, value, fonts['regular'])
        y += 38
    buttons = ['UPPERCASE', 'Rename', 'lowercase'] if launcher['id'].endswith('-proto') else ['Rename']
    x = 146 if len(buttons) == 3 else width // 2 - 70
    for button in buttons:
        _button(draw, x, 470, 100, 30, button, fonts['regular'])
        x += 112


def _draw_duplicate_sheets(draw, fonts, width, height, launcher, window_path):
    draw.text((34, 56), 'Sheets to duplicate', fill=PALETTE['text_light'], font=fonts['bold'])
    _draw_list(draw, fonts, 34, 88, 280, 180,
               ['A101 - Floor Plan', 'A201 - Building Section', 'S101 - Foundation Plan'], [0, 2])
    draw.text((348, 56), 'View options', fill=PALETTE['text_light'], font=fonts['bold'])
    options = ['Duplicate views', 'Copy view templates', 'Include legends', 'Preserve sheet parameters']
    for index, option in enumerate(options):
        _checkbox(draw, 350, 92 + index * 34, option, fonts['regular'], index < 3)
    draw.text((34, 300), 'Duplicate mode', fill=PALETTE['text_light'], font=fonts['bold'])
    for index, option in enumerate(['Duplicate only', 'With detailing', 'As dependent']):
        _radio(draw, 56, 338 + index * 34, option, fonts['regular'], index == 0)
    _button(draw, width // 2 - 80, 536, 160, 32, 'Close preview', fonts['regular'])


def _draw_view_range(draw, fonts, width, height, launcher, window_path):
    rows = [
        ('Top', 'Level 02 - Office', "12' - 0\"", 'Dodger blue'),
        ('Cut', 'Level 01 - Lobby', "4' - 0\"", 'Orange'),
        ('Bottom', 'Level 01 - Lobby', "0' - 0\"", 'Sea green'),
        ('View Depth', 'Level 01 - Lobby', "-4' - 0\"", 'Purple'),
    ]
    x = 38
    y = 68
    draw.text((x, y), 'Plane', fill=PALETTE['text'], font=fonts['bold'])
    draw.text((x + 120, y), 'Level', fill=PALETTE['text'], font=fonts['bold'])
    draw.text((x + 340, y), 'Elevation', fill=PALETTE['text'], font=fonts['bold'])
    y += 30
    for name, level, elevation, color in rows:
        draw.rectangle((x, y - 4, width - 38, y + 26), fill=(255, 255, 255), outline=PALETTE['line'])
        draw.text((x + 10, y + 3), name, fill=PALETTE['text'], font=fonts['regular'])
        draw.text((x + 120, y + 3), level, fill=PALETTE['text'], font=fonts['regular'])
        draw.text((x + 340, y + 3), elevation, fill=PALETTE['text'], font=fonts['regular'])
        draw.text((x + 460, y + 3), color, fill=PALETTE['muted'], font=fonts['small'])
        y += 42
    _button(draw, width // 2 - 135, 308, 120, 30, 'Apply Changes', fonts['regular'])
    _button(draw, width // 2 + 5, 308, 130, 30, 'Reset to Original', fonts['regular'])


def _draw_match_recall(draw, fonts, width, height, launcher, window_path):
    draw.text((24, 58), 'Fictional saved match parameters', fill=PALETTE['text'], font=fonts['title'])
    _draw_list(draw, fonts, 24, 102, width - 48, 190,
               ['Mark = A-101', 'Comments = Coordination review',
                'Phase Created = Existing', 'Detail Level = Fine'], [0, 1, 2, 3],
               dark=False)
    draw.text((24, 318), 'Preview only. No Revit elements are read or changed.',
              fill=PALETTE['muted'], font=fonts['regular'])


def _draw_gallery(draw, fonts, width, height, launcher, window_path):
    draw.text((22, 52), 'Open representative pyRevit and KL&A dialogs with fictional sample data.',
              fill=PALETTE['text'], font=fonts['regular'])
    _textbox(draw, 22, 82, width - 44, 28, 'Filter by dialog family, title, path, or caller', fonts['regular'])
    headers = ['Family', 'Window', 'Relative Path', 'Called By', 'Data']
    xs = [22, 145, 322, 565, 820]
    y = 128
    draw.rectangle((22, y, width - 22, y + 30), fill=PALETTE['accent'])
    for x, header in zip(xs, headers):
        draw.text((x + 6, y + 7), header, fill=PALETTE['text_light'], font=fonts['small'])
    y += 30
    for row in gallery_launchers()[:8]:
        draw.rectangle((22, y, width - 22, y + 34), fill=(255, 255, 255), outline=PALETTE['line'])
        values = [
            row['category'], row['title'], row.get('relative_path') or 'pyRevit built-in',
            row['called_by'], 'Seeded sample data',
        ]
        for x, value in zip(xs, values):
            draw.text((x + 6, y + 9), _clip(value, 28), fill=PALETTE['text'], font=fonts['small'])
        y += 34
    _button(draw, width - 245, height - 68, 155, 28, 'Open Selected Window', fonts['small'])
    _button(draw, width - 80, height - 68, 58, 28, 'Close', fonts['small'])


def _draw_fixture(draw, fonts, width, height, launcher, window_path):
    draw.rectangle((50, 76, width - 50, height - 84), fill=(255, 255, 255), outline=PALETTE['line'])
    draw.text((74, 106), 'UI Gallery Preview Fixture', fill=PALETTE['text'], font=fonts['title'])
    draw.text((74, 142), 'Safe self-contained Window fixture.', fill=PALETTE['muted'], font=fonts['regular'])


def _draw_filter(draw, fonts, width, y, label):
    draw.text((34, y), 'Search', fill=PALETTE['text_light'], font=fonts['small'])
    _textbox(draw, 34, y + 24, width - 68, 26, 'sample', fonts['regular'], dark=True)
    draw.text((34, y + 66), label, fill=PALETTE['text_light'], font=fonts['regular'])


def _draw_list(draw, fonts, x, y, width, height, items, checked_indices, dark=True):
    fill = PALETTE['background'] if dark else (255, 255, 255)
    text = PALETTE['text_light'] if dark else PALETTE['text']
    draw.rounded_rectangle((x, y, x + width, y + height), radius=8, fill=fill, outline=PALETTE['accent'])
    row_y = y + 14
    for index, item in enumerate(items):
        _checkbox(draw, x + 16, row_y, item, fonts['regular'], index in checked_indices, text)
        row_y += 34


def _textbox(draw, x, y, width, height, text, font, dark=False):
    fill = PALETTE['background'] if dark else (255, 255, 255)
    foreground = PALETTE['text_light'] if dark else PALETTE['text']
    draw.rounded_rectangle((x, y, x + width, y + height), radius=5, fill=fill, outline=PALETTE['accent'])
    draw.text((x + 8, y + 5), text, fill=foreground, font=font)


def _button(draw, x, y, width, height, text, font):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=8,
                           fill=PALETTE['surface_dark'], outline=PALETTE['accent_hover'])
    tw, th = _text_size(draw, text, font)
    draw.text((x + (width - tw) // 2, y + (height - th) // 2 - 1),
              text, fill=(255, 255, 255), font=font)


def _checkbox(draw, x, y, text, font, checked, foreground=None):
    foreground = foreground or PALETTE['text_light']
    draw.rectangle((x, y + 2, x + 14, y + 16), fill=PALETTE['surface_dark'], outline=PALETTE['accent'])
    if checked:
        draw.line((x + 3, y + 9, x + 6, y + 13, x + 12, y + 5), fill=PALETTE['text_light'], width=2)
    draw.text((x + 24, y), text, fill=foreground, font=font)


def _radio(draw, x, y, text, font, checked):
    draw.ellipse((x, y + 1, x + 15, y + 16), fill=PALETTE['background'], outline=PALETTE['accent'])
    if checked:
        draw.ellipse((x + 4, y + 5, x + 11, y + 12), fill=PALETTE['accent'])
    draw.text((x + 24, y), text, fill=PALETTE['text_light'], font=font)


def _fonts():
    candidates = [
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ]
    bold_candidates = [
        'C:/Windows/Fonts/segoeuib.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
    ]
    regular_path = _first_existing(candidates)
    bold_path = _first_existing(bold_candidates) or regular_path
    if regular_path:
        return {
            'small': ImageFont.truetype(regular_path, 12),
            'regular': ImageFont.truetype(regular_path, 15),
            'bold': ImageFont.truetype(bold_path, 15),
            'title': ImageFont.truetype(bold_path, 22),
        }
    default = ImageFont.load_default()
    return {'small': default, 'regular': default, 'bold': default, 'title': default}


def _first_existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def _safe_filename(value):
    return re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('-').lower()


def _text_size(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _clip(value, limit):
    if len(value) <= limit:
        return value
    return value[:limit - 3] + '...'


def _write_manifest(rows):
    path = os.path.join(OUTPUT_DIR, 'README.md')
    with open(path, 'w') as output:
        output.write('# UI Gallery Window Previews\n\n')
        output.write('Generated seeded static preview PNGs for root `Window` XAML entries cataloged by the DevSandbox UI Gallery. These are review images, not live Revit screenshots.\n\n')
        output.write('| Launcher | Window XAML | Preview |\n')
        output.write('| --- | --- | --- |\n')
        for launcher_id, relative_path, output_name in rows:
            output.write('| `{}` | `{}` | `{}` |\n'.format(
                launcher_id, relative_path, output_name))


if __name__ == '__main__':
    main()
