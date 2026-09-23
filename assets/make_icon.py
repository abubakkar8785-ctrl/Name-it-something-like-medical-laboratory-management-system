"""
Generates a professional medical-laboratory application icon
(assets/medical_lab.ico) at all the sizes Windows needs for the .exe,
desktop shortcut, Start Menu shortcut, and taskbar (16, 24, 32, 48,
64, 128, 256 px), plus a standalone 512px PNG master for other uses
(installer banner, in-app branding, etc).

Design: a stylized microscope silhouette (recognizable medical/lab
symbol) in white on a solid teal-to-blue circular badge, similar in
spirit to modern flat Windows app icons (think Teams/Outlook-style
badge-with-glyph).

Run with:  python assets/make_icon.py
"""

from PIL import Image, ImageDraw

OUT_DIR = "/home/claude/medlab/assets"

BADGE_COLOR = (18, 85, 122)       # deep medical blue
BADGE_COLOR_2 = (23, 165, 137)    # teal accent (unused as flat fill, kept for reference)
GLYPH_COLOR = (255, 255, 255)


def draw_microscope(draw: ImageDraw.ImageDraw, cx, cy, scale):
    """
    Draws a bold, simplified microscope silhouette that stays legible
    down to 16px: a straight vertical body, a round objective/turret
    circle, a stage crossbar, and a wide base. Symmetric and chunky
    on purpose so it doesn't turn to mush at small sizes.
    """
    s = scale

    # --- Base (wide rounded bar) ---
    base_w = s * 1.05
    base_h = s * 0.16
    base_y = cy + s * 0.62
    draw.rounded_rectangle(
        [cx - base_w / 2, base_y, cx + base_w / 2, base_y + base_h],
        radius=base_h * 0.5, fill=GLYPH_COLOR,
    )

    # --- Vertical body/spine (straight, thick) ---
    body_w = s * 0.20
    body_top = cy - s * 0.66
    body_bottom = base_y
    draw.rounded_rectangle(
        [cx - body_w / 2, body_top, cx + body_w / 2, body_bottom],
        radius=body_w * 0.4, fill=GLYPH_COLOR,
    )

    # --- Eyepiece: short diagonal stub off the top, ending in a knob ---
    eye_end = (cx - s * 0.34, body_top - s * 0.06)
    eye_start = (cx + s * 0.02, body_top + s * 0.10)
    draw.line([eye_start, eye_end], fill=GLYPH_COLOR, width=int(s * 0.20))
    knob_r = s * 0.115
    draw.ellipse(
        [eye_end[0] - knob_r, eye_end[1] - knob_r, eye_end[0] + knob_r, eye_end[1] + knob_r],
        fill=GLYPH_COLOR,
    )

    # --- Objective turret: single bold circle centered on the body ---
    turret_cy = cy + s * 0.02
    turret_r = s * 0.20
    draw.ellipse(
        [cx - turret_r, turret_cy - turret_r, cx + turret_r, turret_cy + turret_r],
        fill=GLYPH_COLOR,
    )
    # Punch a small hole in the middle so it reads as a lens, not a blob
    hole_r = s * 0.075
    draw.ellipse(
        [cx - hole_r, turret_cy - hole_r, cx + hole_r, turret_cy + hole_r],
        fill=BADGE_COLOR,
    )

    # --- Stage: horizontal crossbar through the body, below the turret ---
    stage_y = turret_cy + s * 0.34
    stage_w = s * 0.62
    stage_h = s * 0.10
    draw.rounded_rectangle(
        [cx - stage_w / 2, stage_y - stage_h / 2, cx + stage_w / 2, stage_y + stage_h / 2],
        radius=stage_h * 0.4, fill=GLYPH_COLOR,
    )


def make_master(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size * 0.04
    draw.ellipse([margin, margin, size - margin, size - margin], fill=BADGE_COLOR)

    cx, cy = size / 2, size / 2 + size * 0.02
    draw_microscope(draw, cx, cy, scale=size * 0.34)

    return img


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    master = make_master(512)
    master.save(os.path.join(OUT_DIR, "medical_lab_512.png"))

    sizes = [16, 24, 32, 48, 64, 128, 256]
    icons = [master.resize((s, s), Image.LANCZOS) for s in sizes]

    ico_path = os.path.join(OUT_DIR, "medical_lab.ico")
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:],
    )
    print(f"Wrote {ico_path} with sizes {sizes}")
    print(f"Wrote {os.path.join(OUT_DIR, 'medical_lab_512.png')} (master PNG)")


if __name__ == "__main__":
    main()
