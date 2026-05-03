#!/usr/bin/env python3
"""Generate clean LSTM gate animations.

The script redraws the reference gate GIFs as compact, vector-style Pillow
animations. It intentionally avoids matplotlib so the output can be regenerated
in lightweight environments that have Pillow available.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, Sequence

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Pillow is required to render the animation. Install it with "
        "`python -m pip install pillow`."
    ) from exc


WIDTH = 950
HEIGHT = 500
DEFAULT_FRAMES = 120
DEFAULT_DURATION = 50


PALETTE = {
    "paper": (255, 255, 255, 255),
    "ink": (20, 22, 24, 255),
    "muted": (112, 112, 112, 255),
    "soft_gray": (231, 238, 242, 255),
    "cell_fill": (213, 232, 212, 255),
    "cell_edge": (125, 176, 96, 255),
    "green_fill": (214, 232, 207, 255),
    "green_edge": (126, 169, 112, 255),
    "blue_fill": (231, 238, 246, 255),
    "blue_edge": (108, 145, 196, 255),
    "gold_fill": (255, 230, 205, 255),
    "gold_edge": (211, 146, 0, 255),
    "rose_fill": (245, 95, 104, 255),
    "rose_edge": (178, 98, 103, 255),
    "rose_soft": (251, 207, 210, 255),
    "mint_track": (185, 218, 207, 255),
    "shadow": (0, 0, 0, 26),
}


def with_alpha(color: Sequence[int], alpha: int) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], alpha)


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def smoothstep(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def interval(t: float, start: float, end: float) -> float:
    if end <= start:
        return 1.0
    return smoothstep((t - start) / (end - start))


def fade_between(t: float, start: float, end: float) -> float:
    return interval(t, start, end) * (1.0 - interval(t, end, end + 0.08))


def blend(a: Sequence[int], b: Sequence[int], amount: float) -> tuple[int, int, int, int]:
    amount = clamp(amount)
    return tuple(
        int(round(a[i] * (1 - amount) + b[i] * amount)) for i in range(4)
    )


class FontBook:
    def __init__(self, scale: int) -> None:
        self.scale = scale
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
        self._families = {
            "serif": [
                "/System/Library/Fonts/Supplemental/STIXTwoText.ttf",
                "/System/Library/Fonts/NewYork.ttf",
                "/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            ],
            "serif_italic": [
                "/System/Library/Fonts/Supplemental/STIXTwoText-Italic.ttf",
                "/System/Library/Fonts/NewYorkItalic.ttf",
                "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            ],
            "serif_bold_italic": [
                "/System/Library/Fonts/Supplemental/STIXGeneralBolIta.otf",
                "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf",
                "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
            ],
            "sans": [
                "/System/Library/Fonts/Avenir.ttc",
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ],
            "sans_bold": [
                "/System/Library/Fonts/Avenir Next.ttc",
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ],
        }

    def get(self, family: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        key = (family, size)
        if key in self._cache:
            return self._cache[key]

        scaled_size = max(1, int(round(size * self.scale)))
        for candidate in self._families.get(family, []):
            path = Path(candidate)
            if path.exists():
                font = ImageFont.truetype(str(path), scaled_size)
                self._cache[key] = font
                return font

        try:
            font = ImageFont.truetype("DejaVuSerif.ttf", scaled_size)
        except OSError:
            font = ImageFont.load_default()
        self._cache[key] = font
        return font


class Canvas:
    def __init__(self, scale: int) -> None:
        self.scale = scale
        self.image = Image.new("RGBA", (WIDTH * scale, HEIGHT * scale), PALETTE["paper"])
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        self.fonts = FontBook(scale)

    def s(self, value: float) -> int:
        return int(round(value * self.scale))

    def xy(self, point: tuple[float, float]) -> tuple[int, int]:
        return (self.s(point[0]), self.s(point[1]))

    def box(self, xyxy: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
        return tuple(self.s(v) for v in xyxy)

    def line(
        self,
        points: Iterable[tuple[float, float]],
        fill: Sequence[int],
        width: float = 4,
        joint: str | None = None,
    ) -> None:
        kwargs = {"fill": tuple(fill), "width": self.s(width)}
        if joint is not None:
            kwargs["joint"] = joint
        self.draw.line([self.xy(point) for point in points], **kwargs)

    def rounded_rect(
        self,
        xyxy: tuple[float, float, float, float],
        radius: float,
        fill: Sequence[int],
        outline: Sequence[int] | None = None,
        width: float = 1,
    ) -> None:
        self.draw.rounded_rectangle(
            self.box(xyxy),
            radius=self.s(radius),
            fill=tuple(fill),
            outline=None if outline is None else tuple(outline),
            width=self.s(width),
        )

    def ellipse(
        self,
        center: tuple[float, float],
        radius: float,
        fill: Sequence[int],
        outline: Sequence[int] | None = None,
        width: float = 1,
    ) -> None:
        x, y = center
        self.draw.ellipse(
            self.box((x - radius, y - radius, x + radius, y + radius)),
            fill=tuple(fill),
            outline=None if outline is None else tuple(outline),
            width=self.s(width),
        )

    def text(
        self,
        xy: tuple[float, float],
        text: str,
        family: str = "serif_italic",
        size: int = 24,
        fill: Sequence[int] = PALETTE["ink"],
        anchor: str = "mm",
    ) -> None:
        self.draw.text(
            self.xy(xy),
            text,
            font=self.fonts.get(family, size),
            fill=tuple(fill),
            anchor=anchor,
        )

    def text_box(
        self,
        xy: tuple[float, float],
        text: str,
        family: str = "sans_bold",
        size: int = 13,
        fill: Sequence[int] = PALETTE["ink"],
        padding: tuple[int, int] = (9, 5),
    ) -> None:
        font = self.fonts.get(family, size)
        x, y = self.xy(xy)
        bbox = self.draw.textbbox((x, y), text, font=font, anchor="mm")
        pad_x, pad_y = self.s(padding[0]), self.s(padding[1])
        bg = (bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y)
        self.draw.rounded_rectangle(
            bg,
            radius=self.s(8),
            fill=(255, 255, 255, 226),
            outline=PALETTE["soft_gray"],
            width=self.s(1.2),
        )
        self.draw.text((x, y), text, font=font, fill=tuple(fill), anchor="mm")

    def math_label(
        self,
        xy: tuple[float, float],
        base: str,
        subscript: str | None = None,
        size: int = 25,
        fill: Sequence[int] = PALETTE["ink"],
        anchor: str = "mm",
    ) -> None:
        main_font = self.fonts.get("serif_italic", size)
        sub_font = self.fonts.get("serif_italic", max(10, int(size * 0.58)))
        x, y = self.xy(xy)
        if subscript is None:
            self.draw.text((x, y), base, font=main_font, fill=tuple(fill), anchor=anchor)
            return

        base_bbox = self.draw.textbbox((0, 0), base, font=main_font, anchor="ls")
        sub_bbox = self.draw.textbbox((0, 0), subscript, font=sub_font, anchor="ls")
        width = base_bbox[2] - base_bbox[0] + sub_bbox[2] - sub_bbox[0]
        height = max(base_bbox[3] - base_bbox[1], sub_bbox[3] - sub_bbox[1])
        if anchor == "mm":
            start_x = x - width // 2
            base_y = y + height // 3
        elif anchor == "rm":
            start_x = x - width
            base_y = y + height // 3
        elif anchor == "lm":
            start_x = x
            base_y = y + height // 3
        else:
            start_x = x
            base_y = y
        self.draw.text((start_x, base_y), base, font=main_font, fill=tuple(fill), anchor="ls")
        self.draw.text(
            (start_x + base_bbox[2] - base_bbox[0], base_y + self.s(size * 0.17)),
            subscript,
            font=sub_font,
            fill=tuple(fill),
            anchor="ls",
        )

    def downsample(self) -> Image.Image:
        return self.image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("P", palette=Image.Palette.ADAPTIVE)


def arrow_head(
    canvas: Canvas,
    start: tuple[float, float],
    end: tuple[float, float],
    color: Sequence[int],
    size: float = 18,
) -> None:
    sx, sy = start
    ex, ey = end
    angle = math.atan2(ey - sy, ex - sx)
    left = (
        ex - size * math.cos(angle) + size * 0.48 * math.sin(angle),
        ey - size * math.sin(angle) - size * 0.48 * math.cos(angle),
    )
    right = (
        ex - size * math.cos(angle) - size * 0.48 * math.sin(angle),
        ey - size * math.sin(angle) + size * 0.48 * math.cos(angle),
    )
    canvas.draw.polygon([canvas.xy(end), canvas.xy(left), canvas.xy(right)], fill=tuple(color))


def arrow(
    canvas: Canvas,
    start: tuple[float, float],
    end: tuple[float, float],
    color: Sequence[int] = PALETTE["ink"],
    width: float = 4,
    head: float = 18,
) -> None:
    sx, sy = start
    ex, ey = end
    length = math.hypot(ex - sx, ey - sy)
    if length == 0:
        return
    trim = head * 0.66
    line_end = (ex - (ex - sx) / length * trim, ey - (ey - sy) / length * trim)
    canvas.line([start, line_end], color, width=width)
    arrow_head(canvas, line_end, end, color, size=head)


def elbow_arrow(
    canvas: Canvas,
    points: Sequence[tuple[float, float]],
    color: Sequence[int] = PALETTE["ink"],
    width: float = 4,
    head: float = 15,
) -> None:
    if len(points) < 2:
        return
    start = points[-2]
    end = points[-1]
    sx, sy = start
    ex, ey = end
    length = math.hypot(ex - sx, ey - sy)
    if length == 0:
        return
    trim = head * 0.64
    line_end = (ex - (ex - sx) / length * trim, ey - (ey - sy) / length * trim)
    canvas.line([*points[:-1], line_end], color, width=width)
    arrow_head(canvas, line_end, end, color, size=head)


def route_length(points: Sequence[tuple[float, float]]) -> float:
    return sum(
        math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        for i in range(len(points) - 1)
    )


def route_point(points: Sequence[tuple[float, float]], progress: float) -> tuple[float, float]:
    progress = clamp(progress)
    target = route_length(points) * progress
    traversed = 0.0
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        segment = math.hypot(b[0] - a[0], b[1] - a[1])
        if traversed + segment >= target:
            local = 0.0 if segment == 0 else (target - traversed) / segment
            return (a[0] + (b[0] - a[0]) * local, a[1] + (b[1] - a[1]) * local)
        traversed += segment
    return points[-1]


def partial_route(
    points: Sequence[tuple[float, float]], start_progress: float, end_progress: float
) -> list[tuple[float, float]]:
    start_progress = clamp(start_progress)
    end_progress = clamp(end_progress)
    if end_progress <= start_progress:
        return [route_point(points, start_progress)]

    total = route_length(points)
    start_d = total * start_progress
    end_d = total * end_progress
    out = [route_point(points, start_progress)]
    traversed = 0.0
    for i in range(len(points) - 1):
        segment = math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        next_d = traversed + segment
        if start_d < next_d and traversed < end_d:
            if start_d <= traversed and next_d <= end_d:
                out.append(points[i + 1])
        traversed = next_d
    out.append(route_point(points, end_progress))
    return out


def draw_operator(canvas: Canvas, center: tuple[float, float], symbol: str, pulse: float = 0.0) -> None:
    pulse = clamp(pulse)
    if pulse > 0:
        canvas.ellipse(center, 24 + 9 * pulse, with_alpha(PALETTE["gold_fill"], int(155 * (1 - pulse))))
    x, y = center
    canvas.rounded_rect(
        (x - 17, y - 17, x + 17, y + 17),
        radius=5,
        fill=PALETTE["ink"],
        outline=PALETTE["ink"],
        width=1,
    )
    canvas.text(center, symbol, family="sans_bold", size=23, fill=PALETTE["paper"])


def draw_sigmoid_icon(canvas: Canvas, center: tuple[float, float], radius: float) -> None:
    cx, cy = center
    points = []
    for step in range(36):
        u = step / 35
        x = cx - radius * 0.45 + u * radius * 0.9
        y = cy + radius * 0.42 - (1.0 / (1.0 + math.exp(-10 * (u - 0.5)))) * radius * 0.84
        points.append((x, y))
    canvas.line(points, PALETTE["ink"], width=3.5)


def draw_tanh_icon(canvas: Canvas, center: tuple[float, float], radius: float) -> None:
    draw_sigmoid_icon(canvas, center, radius)


def draw_gate(
    canvas: Canvas,
    center: tuple[float, float],
    fill: Sequence[int],
    edge: Sequence[int],
    label: str,
    active: float = 0.0,
    kind: str = "sigmoid",
    label_offset: tuple[float, float] = (-38, 52),
) -> None:
    radius = 30
    active = clamp(active)
    if active > 0:
        canvas.ellipse(center, radius + 9 * active, with_alpha(edge, int(70 * (1 - active))))
    canvas.ellipse(center, radius, fill, outline=edge, width=3.2)
    draw_sigmoid_icon(canvas, center, radius)
    if label:
        base, sub = parse_simple_subscript(label)
        canvas.math_label(
            (center[0] + label_offset[0], center[1] + label_offset[1]),
            base,
            sub,
            size=24,
            fill=PALETTE["ink"],
        )


def parse_simple_subscript(label: str) -> tuple[str, str | None]:
    if "_" not in label:
        return label, None
    base, sub = label.split("_", 1)
    return base, sub


def draw_token(
    canvas: Canvas,
    center: tuple[float, float],
    label: str,
    fill: Sequence[int],
    outline: Sequence[int],
    radius: float = 16,
    alpha: int = 255,
    label_offset: tuple[float, float] | None = None,
) -> None:
    if alpha <= 0:
        return
    shadow = with_alpha(PALETTE["shadow"], max(0, int(alpha * 0.10)))
    canvas.ellipse((center[0] + 1.4, center[1] + 2.0), radius + 1.2, shadow)
    canvas.ellipse(center, radius, with_alpha(fill, alpha), outline=with_alpha(outline, alpha), width=3)
    token_text_size = max(17, int(round(radius * 1.12))) if len(label) < 5 else max(13, int(round(radius * 0.78)))
    canvas.text(center, label, family="serif_bold_italic", size=token_text_size, fill=with_alpha(PALETTE["ink"], alpha))
    if label_offset is not None:
        lx = center[0] + label_offset[0]
        ly = center[1] + label_offset[1]
        canvas.text_box((lx, ly), label, family="serif_italic", size=15, fill=with_alpha(PALETTE["ink"], alpha))


def draw_static_lstm(canvas: Canvas, t: float, animation: str) -> None:
    ink = PALETTE["ink"]

    body = (128, 76, 790, 382)
    top_y = 146
    hidden_y = 344
    forget_mul = (260, top_y)
    add_node = (548, top_y)
    input_mul = (548, 206)
    output_mul = (735, 266)
    soft_ink = with_alpha(ink, 155)

    canvas.rounded_rect(body, 16, PALETTE["cell_fill"], PALETTE["cell_edge"], width=5)

    arrow(canvas, (72, top_y), (850, top_y), ink, width=4.2, head=19)
    arrow(canvas, (72, hidden_y), (850, hidden_y), ink, width=3.7, head=17)
    arrow(canvas, (162, 430), (162, hidden_y + 2), ink, width=3.7, head=16)

    # Forget-gate branch: all emphasis lines are horizontal or vertical.
    canvas.line([(260, hidden_y), (260, 298)], ink, width=3.8)
    arrow(canvas, (260, 232), (260, 164), ink, width=3.8, head=14)

    # Contextual LSTM branches are lighter and routed orthogonally.
    canvas.line([(388, hidden_y), (388, 298)], soft_ink, width=3.0)
    elbow_arrow(canvas, [(388, 236), (388, 206), (530, 206)], soft_ink, width=3.0, head=11)
    canvas.line([(508, hidden_y), (508, 298)], soft_ink, width=3.0)
    elbow_arrow(canvas, [(508, 232), (508, 206), (530, 206)], soft_ink, width=3.0, head=10)
    arrow(canvas, (548, 189), (548, 164), soft_ink, width=3.0, head=11)
    canvas.line([(642, hidden_y), (642, 302)], soft_ink, width=3.0)
    arrow(canvas, (672, 266), (716, 266), soft_ink, width=3.0, head=11)
    canvas.line([(735, top_y), (735, 162)], soft_ink, width=3.0)
    arrow(canvas, (735, 220), (735, 247), soft_ink, width=3.0, head=11)
    arrow(canvas, (735, 285), (735, hidden_y - 4), soft_ink, width=3.0, head=11)

    forget_pulse = interval(t, 0.68, 0.78) * (1 - interval(t, 0.88, 0.98)) if animation == "forget" else 0.0
    input_pulse = interval(t, 0.70, 0.82) * (1 - interval(t, 0.90, 1.0)) if animation == "input" else 0.0
    output_pulse = interval(t, 0.64, 0.76) * (1 - interval(t, 0.86, 0.98)) if animation == "cell" else 0.0
    draw_operator(canvas, forget_mul, "x", pulse=forget_pulse)
    draw_operator(canvas, add_node, "+", pulse=0.0)
    draw_operator(canvas, input_mul, "x", pulse=input_pulse)
    draw_operator(canvas, output_mul, "x", pulse=output_pulse)

    draw_gate(
        canvas,
        (260, 266),
        PALETTE["rose_soft"],
        PALETTE["rose_edge"],
        "f_t",
        active=fade_between(t, 0.20, 0.42) if animation == "forget" else 0.0,
        label_offset=(-45, 53),
    )
    draw_gate(
        canvas,
        (388, 266),
        PALETTE["rose_soft"],
        PALETTE["rose_edge"],
        "i_t",
        active=fade_between(t, 0.54, 0.72) if animation == "input" else 0.0,
        label_offset=(-42, 53),
    )
    draw_gate(
        canvas,
        (508, 266),
        PALETTE["blue_fill"],
        PALETTE["blue_edge"],
        "Ĉ_t",
        active=fade_between(t, 0.54, 0.72) if animation == "input" else 0.0,
        kind="tanh",
        label_offset=(-42, 53),
    )
    draw_gate(
        canvas,
        (642, 266),
        PALETTE["rose_soft"],
        PALETTE["rose_edge"],
        "o_t",
        active=fade_between(t, 0.46, 0.64) if animation == "cell" else 0.0,
        label_offset=(-42, 53),
    )
    draw_gate(
        canvas,
        (735, 190),
        PALETTE["blue_fill"],
        PALETTE["blue_edge"],
        "",
        active=fade_between(t, 0.56, 0.76) if animation == "cell" else 0.0,
        kind="tanh",
    )

    canvas.math_label((66, top_y - 30), "C", "t-1", size=27, anchor="lm")
    canvas.math_label((66, hidden_y - 31), "h", "t-1", size=26, anchor="lm")
    canvas.math_label((118, 424), "x", "t", size=26)
    canvas.math_label((864, top_y - 30), "C", "t", size=27)
    canvas.math_label((864, hidden_y + 31), "h", "t", size=27)

    title = {"cell": "cell state", "input": "input gate"}.get(animation, "forget gate")
    canvas.text((260, 105), title, family="sans_bold", size=17, fill=PALETTE["muted"])


def draw_forget_animation_state(canvas: Canvas, t: float) -> None:
    top_route = [(72, 146), (260, 146)]
    f_route = [(260, 266), (260, 146)]
    result_route = [(278, 146), (404, 146)]
    h_route = [(72, 344), (260, 344), (260, 266)]
    x_route = [(162, 430), (162, 344), (260, 344), (260, 266)]

    h_progress = interval(t, 0.04, 0.26)
    x_progress = interval(t, 0.07, 0.31)
    draw_token(
        canvas,
        route_point(h_route, h_progress),
        "h",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.30, 0.43))),
    )
    draw_token(
        canvas,
        route_point(x_route, x_progress),
        "x",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.34, 0.46))),
    )

    c_alpha = int(248 * interval(t, 0.34, 0.42) * (1 - interval(t, 0.72, 0.80)))
    draw_token(
        canvas,
        route_point(top_route, interval(t, 0.42, 0.72)),
        "C",
        PALETTE["gold_fill"],
        PALETTE["gold_edge"],
        radius=19,
        alpha=c_alpha,
        label_offset=None,
    )

    f_alpha = int(248 * interval(t, 0.42, 0.50) * (1 - interval(t, 0.72, 0.80)))
    draw_token(
        canvas,
        route_point(f_route, interval(t, 0.50, 0.72)),
        "f",
        PALETTE["rose_fill"],
        PALETTE["rose_edge"],
        radius=19,
        alpha=f_alpha,
        label_offset=None,
    )

    product_alpha = int(248 * interval(t, 0.80, 0.88) * (1 - interval(t, 0.98, 1.0)))
    draw_token(
        canvas,
        route_point(result_route, interval(t, 0.82, 0.98)),
        "C",
        PALETTE["gold_fill"],
        PALETTE["gold_edge"],
        radius=19,
        alpha=product_alpha,
        label_offset=None,
    )


def draw_input_animation_state(canvas: Canvas, t: float) -> None:
    h_route = [(72, 344), (330, 344)]
    x_route = [(162, 430), (162, 344), (330, 344)]
    h_to_i_route = [(330, 334), (378, 334), (378, 276)]
    x_to_i_route = [(330, 354), (398, 354), (398, 276)]
    h_to_g_route = [(330, 334), (498, 334), (498, 276)]
    x_to_g_route = [(330, 354), (518, 354), (518, 276)]
    i_route = [(388, 266), (388, 206), (548, 206)]
    g_route = [(508, 266), (508, 206), (548, 206)]
    product_route = [(548, 206), (548, 146)]

    h_progress = interval(t, 0.04, 0.26)
    x_progress = interval(t, 0.07, 0.30)
    draw_token(
        canvas,
        route_point(h_route, h_progress),
        "h",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.30, 0.40))),
    )
    draw_token(
        canvas,
        route_point(x_route, x_progress),
        "x",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.32, 0.42))),
    )

    pair_alpha = int(210 * interval(t, 0.32, 0.42) * (1 - interval(t, 0.58, 0.68)))
    pair_progress = interval(t, 0.40, 0.62)
    for label, route in (
        ("h", h_to_i_route),
        ("x", x_to_i_route),
        ("h", h_to_g_route),
        ("x", x_to_g_route),
    ):
        draw_token(
            canvas,
            route_point(route, pair_progress),
            label,
            PALETTE["soft_gray"],
            PALETTE["muted"],
            radius=16,
            alpha=pair_alpha,
        )

    i_alpha = int(248 * interval(t, 0.64, 0.72) * (1 - interval(t, 0.82, 0.90)))
    draw_token(
        canvas,
        route_point(i_route, interval(t, 0.70, 0.84)),
        "i",
        PALETTE["rose_fill"],
        PALETTE["rose_edge"],
        radius=19,
        alpha=i_alpha,
    )

    g_alpha = int(248 * interval(t, 0.64, 0.72) * (1 - interval(t, 0.82, 0.90)))
    draw_token(
        canvas,
        route_point(g_route, interval(t, 0.70, 0.84)),
        "Ĉ",
        PALETTE["blue_fill"],
        PALETTE["blue_edge"],
        radius=19,
        alpha=g_alpha,
    )

    product_alpha = int(248 * interval(t, 0.88, 0.94) * (1 - interval(t, 0.98, 1.0)))
    draw_token(
        canvas,
        route_point(product_route, interval(t, 0.88, 0.98)),
        "Ĉ",
        PALETTE["gold_fill"],
        PALETTE["gold_edge"],
        radius=19,
        alpha=product_alpha,
    )


def draw_cell_animation_state(canvas: Canvas, t: float) -> None:
    h_route = [(72, 344), (596, 344), (632, 308), (632, 278)]
    x_route = [(162, 430), (162, 344), (616, 344), (652, 308), (652, 278)]
    o_route = [(642, 266), (735, 266)]
    cell_to_output_mul_route = [(548, 146), (735, 146), (735, 190), (735, 266)]
    hidden_route = [(735, 285), (735, 344), (850, 344)]
    cell_output_route = [(548, 146), (850, 146)]

    h_progress = interval(t, 0.03, 0.48)
    x_progress = interval(t, 0.06, 0.50)
    draw_token(
        canvas,
        route_point(h_route, h_progress),
        "h",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.50, 0.60))),
    )
    draw_token(
        canvas,
        route_point(x_route, x_progress),
        "x",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=int(205 * (1 - interval(t, 0.52, 0.62))),
    )

    o_alpha = int(248 * interval(t, 0.58, 0.66) * (1 - interval(t, 0.78, 0.86)))
    draw_token(
        canvas,
        route_point(o_route, interval(t, 0.64, 0.80)),
        "o",
        PALETTE["rose_fill"],
        PALETTE["rose_edge"],
        radius=19,
        alpha=o_alpha,
    )

    c_branch_alpha = int(248 * (1 - interval(t, 0.78, 0.86)))
    draw_token(
        canvas,
        route_point(cell_to_output_mul_route, interval(t, 0.30, 0.80)),
        "C",
        PALETTE["gold_fill"],
        PALETTE["gold_edge"],
        radius=19,
        alpha=c_branch_alpha,
    )

    hidden_alpha = int(248 * interval(t, 0.86, 0.92) * (1 - interval(t, 0.99, 1.0)))
    draw_token(
        canvas,
        route_point(hidden_route, interval(t, 0.88, 0.99)),
        "h",
        PALETTE["soft_gray"],
        PALETTE["muted"],
        radius=18,
        alpha=hidden_alpha,
    )

    cell_out_alpha = int(248 * interval(t, 0.82, 0.90) * (1 - interval(t, 0.99, 1.0)))
    draw_token(
        canvas,
        route_point(cell_output_route, interval(t, 0.86, 0.99)),
        "C",
        PALETTE["gold_fill"],
        PALETTE["gold_edge"],
        radius=19,
        alpha=cell_out_alpha,
    )


def render_frame(frame_index: int, frame_count: int, scale: int, animation: str) -> Image.Image:
    # Leave a short hold at the beginning/end so the GIF reads well in slides.
    raw = frame_index / max(1, frame_count - 1)
    t = clamp((raw - 0.035) / 0.93)
    canvas = Canvas(scale)
    draw_static_lstm(canvas, t, animation)
    if animation == "cell":
        draw_cell_animation_state(canvas, t)
    elif animation == "input":
        draw_input_animation_state(canvas, t)
    else:
        draw_forget_animation_state(canvas, t)
    return canvas.downsample()


def render_gif(output: Path, frames: int, duration: int, scale: int, animation: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    images = [render_frame(i, frames, scale, animation) for i in range(frames)]
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=False,
        disposal=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).with_name("forget-gate.gif"),
        help="Destination GIF path. Defaults to assets/animations/forget-gate.gif.",
    )
    parser.add_argument(
        "--animation",
        choices=("forget", "input", "cell"),
        default=None,
        help="Animation to render. Defaults from the output name when possible.",
    )
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="Number of animation frames.")
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help="Frame duration in milliseconds.",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=3,
        help="Supersampling scale used while drawing for antialiasing.",
    )
    args = parser.parse_args()

    if args.frames < 2:
        raise SystemExit("--frames must be at least 2.")
    if args.duration <= 0:
        raise SystemExit("--duration must be positive.")
    if args.scale < 1:
        raise SystemExit("--scale must be at least 1.")

    animation = args.animation
    if animation is None:
        output_name = args.output.name
        if "input" in output_name:
            animation = "input"
        elif "cell" in output_name:
            animation = "cell"
        else:
            animation = "forget"

    render_gif(args.output, args.frames, args.duration, args.scale, animation)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
