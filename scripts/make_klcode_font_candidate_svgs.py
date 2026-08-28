"""Create KLCode logo SVG candidates from local TTF files."""

from __future__ import print_function

from pathlib import Path

from PIL import ImageFont


OUT = Path("lib/_logos")
FONT_DIR = OUT / "_font_candidates"
WIDTH = 2137
HEIGHT = 736
GREEN = "#33714F"
WHITE = "#EBEBEB"
TEXT = "KLCode"


CANDIDATES = [
    ("orbitron-black", "Orbitron Black", "Orbitron-Black.ttf", 900),
    ("michroma-regular", "Michroma Regular", "Michroma-Regular.ttf", 400),
    ("oxanium-extrabold", "Oxanium ExtraBold", "Oxanium-ExtraBold.ttf", 800),
    ("exo2-extrabold", "Exo 2 ExtraBold", "Exo2-ExtraBold.ttf", 800),
    ("rajdhani-bold", "Rajdhani Bold", "Rajdhani-Bold.ttf", 700),
    ("audiowide-regular", "Audiowide Regular", "Audiowide-Regular.ttf", 400),
    ("share-tech-mono-regular", "Share Tech Mono Regular", "ShareTechMono-Regular.ttf", 400),
    ("jetbrains-mono-bold", "JetBrains Mono Bold", "JetBrainsMono-Bold.ttf", 700),
    ("chivo-mono-bold", "Chivo Mono Bold", "ChivoMono-Bold.ttf", 700),
    ("space-mono-bold", "Space Mono Bold", "SpaceMono-Bold.ttf", 700),
    ("oxanium-medium", "Oxanium Medium", "Oxanium-Medium.ttf", 500),
    ("oxanium-bold", "Oxanium Bold", "Oxanium-Bold.ttf", 700),
    ("rajdhani-medium", "Rajdhani Medium", "Rajdhani-Medium.ttf", 500),
    ("rajdhani-semibold", "Rajdhani SemiBold", "Rajdhani-SemiBold.ttf", 600),
]


def escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_size_for(font_path):
    target_height = 327
    size = 330
    while size > 40:
        font = ImageFont.truetype(str(font_path), size=size)
        left, top, right, bottom = font.getbbox(TEXT)
        text_width = right - left
        text_height = bottom - top
        if text_height <= target_height and text_width <= 1700:
            return size, left, top, right, bottom
        size -= 4
    font = ImageFont.truetype(str(font_path), size=size)
    return (size,) + font.getbbox(TEXT)


def svg_for(slug, label, font_file, weight):
    font_path = FONT_DIR / font_file
    size, left, top, right, bottom = font_size_for(font_path)
    text_width = right - left
    text_height = bottom - top
    slash_x = 82
    slash_width = 60
    slash_gap = 78
    text_x = slash_x + 204 + slash_gap
    baseline_y = 173 + ((327 - text_height) / 2.0) - top

    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
  <title id="title">KLCode logo - {label}</title>
  <defs>
    <style>
      @font-face {{
        font-family: "{family}";
        src: url("_font_candidates/{font_file}") format("truetype");
        font-weight: {weight};
        font-style: normal;
      }}
    </style>
  </defs>
  <path id="slash" fill="{green}" d="M226 173h60L142 500H82z"/>
  <text id="wordmark" x="{text_x}" y="{baseline_y:.3f}" fill="{white}" font-family="{family}" font-size="{size}" font-weight="{weight}" letter-spacing="0">{text}</text>
</svg>
""".format(
        width=WIDTH,
        height=HEIGHT,
        label=escape(label),
        family="KLCode " + label,
        font_file=font_file,
        weight=weight,
        green=GREEN,
        white=WHITE,
        text_x=text_x,
        baseline_y=baseline_y,
        size=size,
        text=TEXT,
    )


def main():
    for slug, label, font_file, weight in CANDIDATES:
        path = OUT / ("KLCode-logo-font-{}.svg".format(slug))
        path.write_text(svg_for(slug, label, font_file, weight), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
