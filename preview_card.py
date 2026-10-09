"""Make assets/img/preview.png, the image shown when the site is shared (LinkedIn, Slack, iMessage…).

    python3 preview_card.py
"""
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent
W, H = 1200, 630
BG, INK, ACCENT, RULE = "#f7f5f0", "#1c1e24", "#2b3f7e", "#e2ddd2"
FONTS = Path("/System/Library/Fonts/Supplemental")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def main():
    site = yaml.safe_load((ROOT / "_data" / "site.yml").read_text(encoding="utf-8"))
    card = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(card)

    # Portrait on the left, rounded corners
    photo = Image.open(ROOT / site["photo"]).convert("RGB")
    photo = ImageOps.fit(photo, (360, 450), centering=(0.5, 0.2))
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *photo.size], radius=16, fill=255)
    card.paste(photo, (80, 90), mask)

    # Text on the right
    x = 500
    draw.text((x, 120), site["name"], font=font("Georgia.ttf", 72), fill=ACCENT)
    draw.text((x, 225), site["role"], font=font("Georgia Bold.ttf", 34), fill=INK)
    draw.text((x, 278), site["department"], font=font("Georgia.ttf", 28), fill=INK)
    draw.text((x, 316), site["institution"], font=font("Georgia.ttf", 28), fill=INK)
    draw.line((x, 385, W - 80, 385), fill=RULE, width=2)
    topics = " · ".join(t["title"] for t in site["research_themes"])
    words, lines, line = topics.split(" "), [], ""
    for w in words:  # wrap the topic line to the card width
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font("Georgia.ttf", 26)) > W - 80 - x:
            lines.append(line); line = w
        else:
            line = trial
    lines.append(line)
    for i, l in enumerate(lines):
        draw.text((x, 410 + i * 38), l, font=font("Georgia.ttf", 26), fill=ACCENT)
    draw.text((x, 540), site["url"].replace("https://", ""), font=font("Georgia Italic.ttf", 26), fill=INK)

    out = ROOT / "assets" / "img" / "preview.png"
    card.save(out, optimize=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
