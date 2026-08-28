"""Render a PNG review sheet for Oxanium and Rajdhani KLCode candidates."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("lib/_logos")
FONT_DIR = ROOT / "_font_candidates"
OUT = Path(
    r"C:\Users\lmadden\.codex\visualizations\2026\08\28\01a0491e-b081-7c93-a3f0-f5d76871c343\klcode-oxanium-rajdhani-candidate-sheet.png"
)

CANDIDATES = [
    ("Oxanium Medium", "Oxanium-Medium.ttf"),
    ("Oxanium Bold", "Oxanium-Bold.ttf"),
    ("Oxanium ExtraBold", "Oxanium-ExtraBold.ttf"),
    ("Rajdhani Medium", "Rajdhani-Medium.ttf"),
    ("Rajdhani SemiBold", "Rajdhani-SemiBold.ttf"),
    ("Rajdhani Bold", "Rajdhani-Bold.ttf"),
]

GREEN = (51, 113, 79, 255)
WHITE = (235, 235, 235, 255)
MUTED = (190, 190, 190, 255)


def main():
    image = Image.new("RGBA", (1600, 1080), (34, 34, 34, 255))
    draw = ImageDraw.Draw(image)
    label_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 28)

    for index, (label, filename) in enumerate(CANDIDATES):
        y = 40 + index * 170
        draw.text((40, y), label, fill=MUTED, font=label_font)
        draw.polygon([(75, y + 66), (118, y + 66), (72, y + 156), (30, y + 156)], fill=GREEN)

        logo_font = ImageFont.truetype(str(FONT_DIR / filename), 112)
        draw.text((145, y + 48), "KLCode", fill=WHITE, font=logo_font)

        title_font = ImageFont.truetype(str(FONT_DIR / filename), 42)
        draw.text((860, y + 68), "ETABS", fill=WHITE, font=title_font)
        x = 860 + draw.textlength("ETABS", font=title_font)
        draw.text((x, y + 68), "2", fill=GREEN, font=title_font)
        x += draw.textlength("2", font=title_font)
        draw.text((x, y + 68), "Concept", fill=WHITE, font=title_font)

        draw.text((860, y + 118), "Concept", fill=WHITE, font=title_font)
        x = 860 + draw.textlength("Concept", font=title_font)
        draw.text((x, y + 118), "2", fill=GREEN, font=title_font)
        x += draw.textlength("2", font=title_font)
        draw.text((x, y + 118), "ETABS", fill=WHITE, font=title_font)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
