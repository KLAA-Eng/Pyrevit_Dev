"""Render a PNG preview sheet for the final Audiowide logo SVG set."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("lib/_logos")
FONT = ImageFont.truetype(str(ROOT / "_font_candidates" / "Audiowide-Regular.ttf"), 112)
TITLE_FONT = ImageFont.truetype(str(ROOT / "_font_candidates" / "Audiowide-Regular.ttf"), 42)
LABEL_FONT = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 28)
OUT = Path(
    r"C:\Users\lmadden\.codex\visualizations\2026\08\28\01a0491e-b081-7c93-a3f0-f5d76871c343\audiowide-final-preview-sheet.png"
)
GREEN = (51, 113, 79, 255)
WHITE = (235, 235, 235, 255)
MUTED = (190, 190, 190, 255)


def draw_colored_text(draw, xy, text, font):
    x, y = xy
    if "2" not in text:
        draw.text((x, y), text, fill=WHITE, font=font)
        return
    left, sep, right = text.partition("2")
    draw.text((x, y), left, fill=WHITE, font=font)
    x += draw.textlength(left, font=font)
    draw.text((x, y), sep, fill=GREEN, font=font)
    x += draw.textlength(sep, font=font)
    draw.text((x, y), right, fill=WHITE, font=font)


def main():
    image = Image.new("RGBA", (1600, 620), (34, 34, 34, 255))
    draw = ImageDraw.Draw(image)
    draw.text((40, 34), "Audiowide Regular final SVG set", fill=MUTED, font=LABEL_FONT)
    draw.polygon([(75, 140), (118, 140), (72, 230), (30, 230)], fill=GREEN)
    draw.text((145, 112), "KLCode", fill=WHITE, font=FONT)

    draw.text((40, 312), "Titlebar wordmarks", fill=MUTED, font=LABEL_FONT)
    draw_colored_text(draw, (40, 370), "ETABS2Concept", TITLE_FONT)
    draw_colored_text(draw, (40, 442), "Concept2ETABS", TITLE_FONT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
