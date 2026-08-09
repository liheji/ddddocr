"""测试用真实图片生成工具"""
import base64
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        # Pillow >= 10.1 支持可缩放默认字体
        return ImageFont.load_default(size=size)
    except TypeError:  # pragma: no cover - 旧版 Pillow 回退
        return ImageFont.load_default()


def to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def captcha_image(text="3A7K", width=120, height=48, noise=False, font_size=28):
    """白底深色文字验证码图片"""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)
    if noise:
        rng = np.random.default_rng(42)
        for _ in range(4):
            draw.line(
                [tuple(rng.integers(0, width, 2).tolist()),
                 tuple(rng.integers(0, width, 2).tolist())],
                fill=(180, 180, 180), width=1,
            )
    draw.text((10, 6), text, fill=(30, 30, 30), font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def rgba_captcha_image(text="1234", width=120, height=48):
    """透明背景、深色文字的 RGBA 图片（png_fix 测试用）"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 6), text, fill=(0, 0, 0, 255), font=_load_font(28))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def red_text_image(text="1234", width=120, height=48):
    """白底红字图片（颜色过滤测试用）"""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 6), text, fill=(200, 20, 20), font=_load_font(28))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def slider_pair(offset=120):
    """生成滑块图与背景图，滑块水平中心为 offset + 23"""
    width, height = 320, 160
    rng = np.random.default_rng(7)
    bg = Image.new("RGB", (width, height), (235, 232, 225))
    draw = ImageDraw.Draw(bg)
    for _ in range(200):
        draw.point(
            (int(rng.integers(0, width)), int(rng.integers(0, height))),
            fill=tuple(int(v) for v in rng.integers(200, 255, 3)),
        )
    draw.rectangle([offset, 50, offset + 46, 94], fill=(120, 120, 125))
    draw.ellipse([offset + 8, 50, offset + 38, 94], fill=(120, 120, 125))
    slider = bg.crop((offset - 8, 42, offset + 54, 102))
    sbuf, bbuf = io.BytesIO(), io.BytesIO()
    slider.save(sbuf, "PNG")
    bg.save(bbuf, "PNG")
    return sbuf.getvalue(), bbuf.getvalue(), offset + 23


def comparison_pair(offset=150):
    """生成带缺口图与完整图（同尺寸），缺口中心为 offset + 20"""
    width, height = 320, 160
    base = Image.new("RGB", (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(base)
    for i in range(20):
        draw.line([(0, i * 8), (width, i * 8)], fill=(200 + (i % 3) * 10,) * 3, width=1)
    target = base.copy()
    draw2 = ImageDraw.Draw(target)
    draw2.rectangle([offset, 60, offset + 40, 100], fill=(160, 160, 160))
    tbuf, bbuf = io.BytesIO(), io.BytesIO()
    target.save(tbuf, "PNG")
    base.save(bbuf, "PNG")
    return tbuf.getvalue(), bbuf.getvalue(), offset + 20


def banded_image(width=400, height=300, y=100):
    """上中下三色块图片：0..y 红，y..y+(h-y)/2 绿，其余蓝"""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, y], fill=(255, 0, 0))
    draw.rectangle([0, y, width, y + (height - y) // 2], fill=(0, 255, 0))
    draw.rectangle([0, y + (height - y) // 2, width, height], fill=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()
