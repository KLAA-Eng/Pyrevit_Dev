"""Create final Audiowide SVG logo assets."""

from pathlib import Path

from PIL import ImageFont


OUT = Path("lib/_logos")
FONT_FILE = "_font_candidates/Audiowide-Regular.ttf"
FONT_PATH = OUT / FONT_FILE
FONT_FAMILY = "Audiowide"
GREEN = "#33714F"
WHITE = "#EBEBEB"


ASSETS = [
    {
        "filename": "KLCode-logo-transparent-recolored.svg",
        "label": "KLCode logo",
        "text": "KLCode",
        "width": 2137,
        "height": 736,
        "target_text_height": 327,
        "slash": True,
        "text_left": 343,
        "vertical_band": (173, 500),
    },
    {
        "filename": "etabs2concept-titlebar-text.svg",
        "label": "ETABS2Concept titlebar wordmark",
        "text": "ETABS2Concept",
        "width": 461,
        "height": 105,
        "max_text_width": 400,
        "target_text_height": 45,
        "slash": False,
    },
    {
        "filename": "concept2etabs-titlebar-text.svg",
        "label": "Concept2ETABS titlebar wordmark",
        "text": "Concept2ETABS",
        "width": 462,
        "height": 105,
        "max_text_width": 400,
        "target_text_height": 45,
        "slash": False,
    },
]


def escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fitted_font_size(text, target_height, max_width=None):
    size = max(12, int(target_height * 2))
    while size > 8:
        font = ImageFont.truetype(str(FONT_PATH), size)
        left, top, right, bottom = font.getbbox(text)
        text_width = right - left
        text_height = bottom - top
        if text_height <= target_height and (max_width is None or text_width <= max_width):
            return size, left, top, right, bottom
        size -= 1
    font = ImageFont.truetype(str(FONT_PATH), size)
    return (size,) + font.getbbox(text)


def colored_wordmark_tspans(text):
    if "2" not in text:
        return '<tspan fill="{0}">{1}</tspan>'.format(WHITE, escape(text))
    left, sep, right = text.partition("2")
    return (
        '<tspan fill="{white}">{left}</tspan>'
        '<tspan fill="{green}">{sep}</tspan>'
        '<tspan fill="{white}">{right}</tspan>'
    ).format(white=WHITE, green=GREEN, left=escape(left), sep=sep, right=escape(right))


def make_svg(asset):
    size, left, top, right, bottom = fitted_font_size(
        asset["text"],
        asset["target_text_height"],
        asset.get("max_text_width"),
    )
    text_height = bottom - top
    width = asset["width"]
    height = asset["height"]

    if asset["slash"]:
        text_x = asset["text_left"]
        band_top, band_bottom = asset["vertical_band"]
        baseline_y = band_top + ((band_bottom - band_top - text_height) / 2.0) - top
        anchor = "start"
        slash = '  <path id="slash" fill="{0}" d="M226 173h60L142 500H82z"/>\n'.format(GREEN)
    else:
        text_x = width / 2.0
        baseline_y = (height - text_height) / 2.0 - top
        anchor = "middle"
        slash = ""

    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
  <title id="title">{label}</title>
  <defs>
    <style>
      @font-face {{
        font-family: "{family}";
        src: url("{font_file}") format("truetype");
        font-weight: 400;
        font-style: normal;
      }}
    </style>
  </defs>
{slash}  <text id="wordmark" x="{text_x:.3f}" y="{baseline_y:.3f}" text-anchor="{anchor}" font-family="{family}, sans-serif" font-size="{size}" font-weight="400" letter-spacing="0">{tspans}</text>
</svg>
""".format(
        width=width,
        height=height,
        label=escape(asset["label"]),
        family=FONT_FAMILY,
        font_file=FONT_FILE,
        slash=slash,
        text_x=text_x,
        baseline_y=baseline_y,
        anchor=anchor,
        size=size,
        tspans=colored_wordmark_tspans(asset["text"]),
    )


def main():
    for asset in ASSETS:
        path = OUT / asset["filename"]
        path.write_text(make_svg(asset), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
