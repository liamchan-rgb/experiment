#!/usr/bin/env python3
"""Produce normal-speed whole-body review GIFs and pose comparisons."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1] / "Art/Review/Equipment"
NEW = R / "b2-batch-v5"
OLD = R / "b2-batch-v4"
BOARDS = NEW / "contact-sheets"
BOARDS.mkdir(exist_ok=True)
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
labels = {"left": "正左", "right": "正右"}
rows = {"left": 2, "right": 6}
atlases = {}
for version, folder in (("r4", OLD), ("r5", NEW)):
    for appearance in ("forester", "wayfarer"):
        atlases[version, appearance] = Image.open(
            folder / "runeArmor" / (appearance + "-walk.png")
        ).convert("RGBA")


def actor(version, appearance, direction, col, scale=2):
    row = rows[direction]
    image = atlases[version, appearance].crop(
        (col * 256 + 64, row * 256 + 56, col * 256 + 192, row * 256 + 220)
    )
    return image.resize((128 * scale, 164 * scale), Image.Resampling.NEAREST)


for direction in ("left", "right"):
    for appearance in ("forester", "wayfarer"):
        for group, columns in (("walk", range(1, 9)), ("transition", (0, 9, 10, 11, 12))):
            out = Image.new("RGB", (len(columns) * 256, 700), "#20372a")
            draw = ImageDraw.Draw(out)
            for row, version in enumerate(("r4", "r5")):
                for col, pose in enumerate(columns):
                    im = actor(version, appearance, direction, pose)
                    x, y = col * 256, row * 350
                    out.paste(im, (x, y), im)
                    draw.text((x + 5, y + 329), f"{version} {direction} {appearance} pose {pose}",
                              font=font, fill="#ffedc7")
            out.save(BOARDS / f"{direction}-{appearance}-{group}-compare.png")

    frames = []
    for n in range(1, 9):
        board = Image.new("RGBA", (512, 350), "#20372a")
        draw = ImageDraw.Draw(board)
        for col, (appearance, label) in enumerate(
            (("forester", "棕发"), ("wayfarer", "银发"))
        ):
            board.alpha_composite(actor("r5", appearance, direction, n), (col * 256, 0))
            draw.text((col * 256 + 8, 329), "符文甲 · " + labels[direction] + " · " + label,
                      font=font, fill="#ffedc7")
        frames.append(board.convert("RGB"))
    frames[0].save(NEW / f"rune-{direction}-walk-normal.gif", save_all=True,
                   append_images=frames[1:], duration=120, loop=0, disposal=2, optimize=True)

    entry = 4 if direction == "left" else 0
    sequence = [0, 9, 10] + [1 + (entry + i) % 8 for i in range(16)] + [11, 12, 0]
    durations = [480] + [120] * 20 + [480]
    frames = []
    for col in sequence:
        board = Image.new("RGBA", (512, 350), "#20372a")
        draw = ImageDraw.Draw(board)
        for index, (appearance, label) in enumerate((("forester", "棕发"), ("wayfarer", "银发"))):
            board.alpha_composite(actor("r5", appearance, direction, col), (index * 256, 0))
            draw.text((index * 256 + 8, 329), "符文甲 · " + labels[direction] + " · " + label,
                      font=font, fill="#ffedc7")
        frames.append(board.convert("RGB"))
    frames[0].save(NEW / f"rune-{direction}-start-stop-normal.gif", save_all=True,
                   append_images=frames[1:], duration=durations, loop=0, disposal=2, optimize=True)

standing = Image.new("RGBA", (1024, 350), "#20372a")
draw = ImageDraw.Draw(standing)
for index, (direction, appearance) in enumerate(
    (("left", "forester"), ("left", "wayfarer"), ("right", "forester"), ("right", "wayfarer"))
):
    standing.alpha_composite(actor("r5", appearance, direction, 0), (index * 256, 0))
    draw.text((index * 256 + 8, 329), "符文甲 · " + labels[direction], font=font, fill="#ffedc7")
standing.convert("RGB").save(NEW / "rune-profile-standing.png")
native = Image.new("RGB", (13 * 128, 4 * 184), "#20372a")
draw = ImageDraw.Draw(native)
for row, (direction, appearance) in enumerate(
    (("left", "forester"), ("left", "wayfarer"), ("right", "forester"), ("right", "wayfarer"))
):
    for col in range(13):
        im = actor("r5", appearance, direction, col, scale=1)
        x, y = col * 128, row * 184
        native.paste(im, (x, y), im)
        draw.text((x + 1, y + 165), f"{direction} {col}", font=font, fill="#ffedc7")
native.save(BOARDS / "rune-profile-all-poses-1x.png")

for direction in ("left", "right"):
    gif = Image.open(NEW / f"rune-{direction}-walk-normal.gif")
    board = Image.new("RGB", (1024, 1400), "#20372a")
    draw = ImageDraw.Draw(board)
    for n in range(gif.n_frames):
        gif.seek(n)
        x, y = (n % 2) * 512, (n // 2) * 350
        board.paste(gif.convert("RGB"), (x, y))
        draw.text((x + 450, y + 329), f"{n+1}", font=font, fill="#ffedc7")
    board.save(BOARDS / f"rune-{direction}-gif-decoded.png")
print("2 normal walk GIFs, 2 normal start/stop GIFs, standing, 1x/2x whole-body comparisons and decoded GIF frames")
