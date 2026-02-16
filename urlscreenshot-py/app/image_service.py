import logging
from io import BytesIO

from PIL import Image, ImageDraw

from app.models import ImageType

logger = logging.getLogger(__name__)


def resize_image(
    image_data: bytes,
    image_type: ImageType,
    image_width: int,
    image_height: int,
    image_band_color: str | None,
) -> bytes:
    """Resize screenshot to target dimensions with letterboxing.

    If width and height are both 0, only convert format (no resize).
    """
    img = Image.open(BytesIO(image_data))

    if image_width != 0 and image_height != 0:
        img = _resize(img, image_type, image_width, image_height, image_band_color)

    output = BytesIO()
    fmt = "PNG" if image_type == ImageType.PNG else "JPEG"

    if fmt == "JPEG":
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.save(output, format=fmt, quality=85)
    else:
        img.save(output, format=fmt)

    return output.getvalue()


def _resize(
    img: Image.Image,
    image_type: ImageType,
    target_width: int,
    target_height: int,
    image_band_color: str | None,
) -> Image.Image:
    """Aspect-ratio preserving resize with letterbox bands.

    Replicates Java ImageService.resize() exactly.
    """
    mode = "RGB" if image_type == ImageType.JPEG else "RGBA"
    canvas = Image.new(mode, (target_width, target_height))

    if image_type == ImageType.JPEG or (
        image_band_color and image_band_color.strip()
    ):
        if not image_band_color or not image_band_color.strip():
            fill_color = (0, 0, 0)
        else:
            r, g, b, a = _decode_hex_color(image_band_color)
            fill_color = (r, g, b, a) if mode == "RGBA" else (r, g, b)

        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, target_width - 1, target_height - 1], fill=fill_color)

    src_width, src_height = img.size
    width_ratio = target_width / src_width
    height_ratio = target_height / src_height

    if width_ratio < height_ratio:
        new_width = target_width
        new_height = int(src_height * width_ratio)
        x = 0
        y = (target_height - new_height) // 2
    else:
        new_height = target_height
        new_width = int(src_width * height_ratio)
        x = (target_width - new_width) // 2
        y = 0

    resized = img.resize((new_width, new_height), Image.LANCZOS)

    if mode == "RGBA" and resized.mode != "RGBA":
        resized = resized.convert("RGBA")
    elif mode == "RGB" and resized.mode != "RGB":
        resized = resized.convert("RGB")

    canvas.paste(resized, (x, y))
    return canvas


def _decode_hex_color(hex_str: str) -> tuple[int, int, int, int]:
    """Parse hex color string to (r, g, b, a).

    Supports 3/4/6/8 char hex with optional # prefix.
    Replicates Java ImageService.decodeFromHEXtoColor() exactly.
    """
    start = 0
    if hex_str.startswith("#"):
        start = 1

    remaining = len(hex_str) - start
    bit4_or_8 = 2 if remaining > 4 else 1

    r = int(hex_str[start : start + bit4_or_8], 16)
    start += bit4_or_8
    g = int(hex_str[start : start + bit4_or_8], 16)
    start += bit4_or_8
    b = int(hex_str[start : start + bit4_or_8], 16)
    start += bit4_or_8

    a = 255 if bit4_or_8 == 2 else 15

    if start < len(hex_str):
        a = int(hex_str[start : start + bit4_or_8], 16)

    if bit4_or_8 == 1:
        r = (r << 4) | r
        g = (g << 4) | g
        b = (b << 4) | b
        a = (a << 4) | a

    return (r, g, b, a)
