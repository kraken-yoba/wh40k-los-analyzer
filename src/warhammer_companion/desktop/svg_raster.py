from __future__ import annotations

import base64
from collections.abc import Callable
from io import BytesIO
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont

RGBA = tuple[int, int, int, int]


def rasterize_svg(svg: str, *, pixel_ratio: float = 1.0) -> bytes:
    root = ElementTree.fromstring(svg)
    width, height = _svg_size(root)
    ratio = _pixel_ratio(pixel_ratio)
    canvas = Image.new(
        "RGBA",
        (int(round(width * ratio)), int(round(height * ratio))),
        (255, 255, 255, 0),
    )

    for element in list(root):
        tag = _tag_name(element.tag)
        if tag == "rect":
            _draw_rect(canvas, element, ratio)
        elif tag == "image":
            _draw_image(canvas, element, ratio)
        elif tag == "polygon":
            _draw_polygon(canvas, element, ratio)
        elif tag == "polyline":
            _draw_polyline(canvas, element, ratio)
        elif tag == "line":
            _draw_line(canvas, element, ratio)
        elif tag == "circle":
            _draw_circle(canvas, element, ratio)
        elif tag == "text":
            _draw_text(canvas, element, ratio)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def _svg_size(root: ElementTree.Element) -> tuple[int, int]:
    view_box = root.attrib.get("viewBox")
    if view_box:
        parts = [float(part) for part in view_box.split()]
        if len(parts) == 4:
            return (int(round(parts[2])), int(round(parts[3])))
    width = int(round(float(root.attrib.get("width", "1"))))
    height = int(round(float(root.attrib.get("height", "1"))))
    return (width, height)


def _draw_rect(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    x = _number(element, "x") * pixel_ratio
    y = _number(element, "y") * pixel_ratio
    width = _number(element, "width") * pixel_ratio
    height = _number(element, "height") * pixel_ratio
    fill = _color(element, "fill", "fill-opacity")
    stroke = _color(element, "stroke", "stroke-opacity")
    stroke_width = _stroke_width(element, pixel_ratio)

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.rectangle(
            [x, y, x + width, y + height],
            fill=fill,
            outline=stroke,
            width=stroke_width if stroke else 1,
        )

    _composite(canvas, draw)


def _draw_image(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    href = element.attrib.get("href") or element.attrib.get("{http://www.w3.org/1999/xlink}href")
    if not href or "," not in href:
        return
    _, encoded = href.split(",", 1)
    image = Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
    width = int(round(_number(element, "width", image.width) * pixel_ratio))
    height = int(round(_number(element, "height", image.height) * pixel_ratio))
    if image.size != (width, height):
        image = image.resize((width, height), Image.Resampling.BILINEAR)
    canvas.alpha_composite(
        image,
        (
            int(round(_number(element, "x") * pixel_ratio)),
            int(round(_number(element, "y") * pixel_ratio)),
        ),
    )


def _draw_polygon(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    points = _points(element, pixel_ratio)
    if not points:
        return
    fill = _color(element, "fill", "fill-opacity")
    stroke = _color(element, "stroke", "stroke-opacity")
    stroke_width = _stroke_width(element, pixel_ratio)

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.polygon(points, fill=fill)
        if stroke:
            draw_context.line([*points, points[0]], fill=stroke, width=stroke_width, joint="curve")

    _composite(canvas, draw)


def _draw_polyline(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    points = _points(element, pixel_ratio)
    stroke = _color(element, "stroke", "stroke-opacity")
    if len(points) < 2 or not stroke:
        return
    stroke_width = _stroke_width(element, pixel_ratio)

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.line(points, fill=stroke, width=stroke_width, joint="curve")

    _composite(canvas, draw)


def _draw_line(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    stroke = _color(element, "stroke", "stroke-opacity")
    if not stroke:
        return
    stroke_width = _stroke_width(element, pixel_ratio)
    points = [
        (_number(element, "x1") * pixel_ratio, _number(element, "y1") * pixel_ratio),
        (_number(element, "x2") * pixel_ratio, _number(element, "y2") * pixel_ratio),
    ]

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.line(points, fill=stroke, width=stroke_width)

    _composite(canvas, draw)


def _draw_circle(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    cx = _number(element, "cx") * pixel_ratio
    cy = _number(element, "cy") * pixel_ratio
    radius = _number(element, "r") * pixel_ratio
    fill = _color(element, "fill", "fill-opacity")
    stroke = _color(element, "stroke", "stroke-opacity")
    stroke_width = _stroke_width(element, pixel_ratio)

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=fill,
            outline=stroke,
            width=stroke_width if stroke else 1,
        )

    _composite(canvas, draw)


def _draw_text(canvas: Image.Image, element: ElementTree.Element, pixel_ratio: float) -> None:
    text = element.text or ""
    if not text:
        return
    fill = _color(element, "fill", "fill-opacity") or (28, 37, 32, 255)
    font_size = int(round(_number(element, "font-size", 13) * pixel_ratio))
    font = _font(font_size)
    x = _number(element, "x") * pixel_ratio
    y = _number(element, "y") * pixel_ratio
    css_class = element.attrib.get("class", "")
    stroke_width = int(round(2 * pixel_ratio)) if "label" in css_class else 0
    stroke_fill: RGBA = (255, 253, 248, 210)

    def draw(draw_context: ImageDraw.ImageDraw) -> None:
        draw_context.text(
            (x, y),
            text,
            fill=fill,
            font=font,
            anchor="mm",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

    _composite(canvas, draw)


def _composite(canvas: Image.Image, draw_action: Callable[[ImageDraw.ImageDraw], None]) -> None:
    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw_action(ImageDraw.Draw(overlay))
    canvas.alpha_composite(overlay)


def _points(element: ElementTree.Element, pixel_ratio: float) -> list[tuple[float, float]]:
    values = element.attrib.get("points", "").split()
    points: list[tuple[float, float]] = []
    for value in values:
        if "," not in value:
            continue
        x, y = value.split(",", 1)
        points.append((float(x) * pixel_ratio, float(y) * pixel_ratio))
    return points


def _number(element: ElementTree.Element, name: str, default: float = 0.0) -> float:
    value = element.attrib.get(name)
    if value is None:
        return default
    return float(value)


def _color(
    element: ElementTree.Element,
    name: str,
    opacity_name: str,
) -> RGBA | None:
    value = element.attrib.get(name)
    if not value or value == "none":
        return None
    if not value.startswith("#") or len(value) != 7:
        return None
    opacity = float(element.attrib.get(opacity_name, element.attrib.get("opacity", "1")))
    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
        max(0, min(255, int(round(opacity * 255)))),
    )


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _stroke_width(element: ElementTree.Element, pixel_ratio: float) -> int:
    return max(1, int(round(_number(element, "stroke-width", 1) * pixel_ratio)))


def _pixel_ratio(pixel_ratio: float) -> float:
    if pixel_ratio <= 0:
        raise ValueError("pixel_ratio must be greater than zero")
    return pixel_ratio


def _tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
