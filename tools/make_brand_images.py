"""Generate the integration's brand images.

Since Home Assistant 2026.3 an integration can ship its own brand images in a
``brand/`` directory inside the integration, and they override the CDN with no
configuration and no pull request to the central brands repository:

    custom_components/viark/brand/
        icon.png       256x256
        icon@2x.png    512x512

The images follow the brands repository specification, which the developer docs
still defer to: PNG, 1:1 for icons, transparent, and trimmed of empty edges.

A ``logo.png`` (a landscape wordmark) is deliberately not generated. This draws a
**generic satellite dish, not the Viark logo** -- a community integration should
not imply an official association, and inventing a vendor wordmark would.
Replace these files directly if you obtain permission to use the vendor artwork.

No dark_ variants are needed: the palette reads on light and dark backgrounds,
and Home Assistant falls back to the non-prefixed image when a dark_ one is
absent.

    pip install pillow
    python tools/make_brand_images.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "custom_components" / "viark" / "brand"

# Readable against both light and dark backgrounds.
DISH = (3, 155, 229, 255)      # blue
ACCENT = (255, 167, 38, 255)   # amber, for the signal arcs
SUPERSAMPLE = 4


def draw_icon(size: int) -> Image.Image:
    s = size * SUPERSAMPLE
    image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    unit = s / 100.0

    def px(*values: float) -> tuple[float, ...]:
        return tuple(v * unit for v in values)

    # Dish drawn into its own layer and rotated, so it reads as a parabola seen
    # at an angle rather than a flat circle.
    dish = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(dish).ellipse(px(8, 20, 68, 74), fill=DISH)
    dish = dish.rotate(-20, resample=Image.BICUBIC, center=(s / 2, s / 2))
    image.alpha_composite(dish)

    # Mast and base.
    draw.polygon(
        [px(46, 52)[0:2], px(56, 58)[0:2], px(44, 88)[0:2], px(34, 84)[0:2]],
        fill=DISH,
    )
    draw.rounded_rectangle(px(22, 84, 62, 93), radius=4 * unit, fill=DISH)

    # Feed horn on its arm.
    draw.line([px(40, 48)[0:2], px(62, 30)[0:2]], fill=DISH, width=int(3.5 * unit))
    draw.ellipse(px(57, 24, 69, 36), fill=DISH)

    # Signal arcs radiating from the horn.
    for index, radius in enumerate((16, 25, 34)):
        box = px(63 - radius, 30 - radius, 63 + radius, 30 + radius)
        width = int((3.2 - index * 0.4) * unit)
        draw.arc(box, start=-70, end=10, fill=ACCENT, width=max(width, 1))

    return _trim_to_square(image, size)


def _trim_to_square(image: Image.Image, size: int, margin: float = 0.02) -> Image.Image:
    """Crop away empty edges, then recentre on a square canvas.

    The specification asks for images trimmed of surrounding empty space while
    staying 1:1, so crop to the drawn content and pad back out to a square.
    """
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)

    side = max(image.size)
    padded = int(side * (1 + margin * 2))
    canvas = Image.new("RGBA", (padded, padded), (0, 0, 0, 0))
    canvas.alpha_composite(
        image, ((padded - image.width) // 2, (padded - image.height) // 2)
    )
    return canvas.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        path = OUT / name
        draw_icon(size).save(path, "PNG", optimize=True)
        print(f"wrote {path.relative_to(Path.cwd())} ({size}x{size})")


if __name__ == "__main__":
    main()
