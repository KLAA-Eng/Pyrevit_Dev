"""Create compact SVG titlebar wordmarks with live text.

The KLCode SVG is hand-drawn path geometry, not a font. These titlebar marks use
an installed Windows font with natural letter widths and no horizontal scaling.
"""

from __future__ import print_function

from pathlib import Path


OUT = Path("lib/_logos")
WHITE = "#EBEBEB"
GREEN = "#33714F"


def svg_for(text, width, height):
    left, two, right = text.partition("2")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" viewBox="0 0 {0} {1}" role="img" aria-labelledby="title">'.format(width, height),
        '  <title id="title">{}</title>'.format(text),
        '  <text x="50%" y="68" text-anchor="middle" font-family="Bahnschrift, Segoe UI, Arial, sans-serif" font-size="50" font-weight="700" letter-spacing="0">',
        '    <tspan fill="{}">{}</tspan><tspan fill="{}">{}</tspan><tspan fill="{}">{}</tspan>'.format(WHITE, left, GREEN, two, WHITE, right),
        '  </text>',
        "</svg>",
        "",
    ]
    return "\n".join(lines)


def main():
    outputs = {
        "etabs2concept-titlebar-text.svg": ("ETABS2Concept", 461, 105),
        "concept2etabs-titlebar-text.svg": ("Concept2ETABS", 462, 105),
    }
    for filename, (text, width, height) in outputs.items():
        path = OUT / filename
        path.write_text(svg_for(text, width, height), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
