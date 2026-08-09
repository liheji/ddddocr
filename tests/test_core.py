"""核心 CAPTCHA 类集成测试：真实 ddddocr 模型 + 真实生成的图片"""
import base64
import io
import re
import threading

import pytest
from PIL import Image

from const.charset import CharsetRange
from const.color import ColorPreset
from core.captcha import CAPTCHA
from helpers import (
    banded_image,
    captcha_image,
    comparison_pair,
    red_text_image,
    rgba_captcha_image,
    slider_pair,
)


class TestClassification:
    def test_basic_ocr(self, captcha):
        result = captcha.classification(captcha_image("3A7K"))
        assert isinstance(result, str) and result

    def test_probability_shape(self, captcha):
        result = captcha.classification(captcha_image("3A7K"), probability=True)
        assert isinstance(result, dict)
        assert {"text", "probabilities", "charset", "confidence"} <= set(result)

    def test_digits_charset(self, captcha):
        result = captcha.classification(
            captcha_image("1234"), charset_range=CharsetRange.DIGITS
        )
        assert isinstance(result, str) and result
        assert set(result) <= set("0123456789")

    def test_png_fix_with_probability(self, captcha):
        # 透明背景深色文字：png_fix 合成白底，概率模式下也必须生效
        result = captcha.classification(
            rgba_captcha_image("1234"), probability=True, png_fix=True,
            charset_range=CharsetRange.DIGITS,
        )
        assert isinstance(result, dict)
        assert len(result["text"]) >= 1
        assert set(result["text"]) <= set("0123456789")

    def test_charset_does_not_leak(self, captcha):
        captcha.clear_ranges()
        try:
            restricted = captcha.classification(
                captcha_image("3A7K"), charset_range=CharsetRange.DIGITS
            )
            assert set(restricted) <= set("0123456789")
            # 请求结束后字符集状态应恢复
            assert captcha._charset_manager().charset_range == []
            # 不带字符集的后续请求不应被污染
            unrestricted = captcha.classification(captcha_image("3A7K"))
            assert re.search(r"[A-Za-z]", unrestricted)
        finally:
            captcha.clear_ranges()

    def test_color_filter_preset(self, captcha):
        result = captcha.classification(
            red_text_image("1234"), color_filter_colors=[ColorPreset.RED]
        )
        assert isinstance(result, str) and result

    def test_color_filter_custom_range(self, captcha):
        result = captcha.classification(
            red_text_image("1234"),
            color_filter_colors=[[[0, 50, 50], [10, 255, 255]]],
        )
        assert isinstance(result, str) and result


class TestSetRanges:
    def test_int_mapping(self, captcha):
        captcha.set_ranges(CharsetRange.DIGITS)
        try:
            mgr = captcha._charset_manager()
            assert set(mgr.charset_range) == set("0123456789") | {""}
        finally:
            captcha.clear_ranges()

    def test_int7(self, captcha):
        captcha.set_ranges(CharsetRange.FULL)
        try:
            mgr = captcha._charset_manager()
            assert set("0123456789") <= set(mgr.charset_range)
        finally:
            captcha.clear_ranges()

    def test_invalid_int(self, captcha):
        with pytest.raises(ValueError):
            captcha.set_ranges(99)

    def test_full_charset_string_rejected(self, captcha):
        with pytest.raises(ValueError, match="仅支持内置索引"):
            captcha.set_ranges("0123456789")
        with pytest.raises(ValueError, match="仅支持内置索引"):
            captcha.classification(captcha_image("3A7K"), charset_range="0123456789")


class TestSlides:
    def test_slide_match(self, captcha):
        slider, background, center = slider_pair(120)
        result = captcha.capcode(slider, background, simple_target=True)
        assert abs(result - center) <= 15

    def test_slide_comparison(self, captcha):
        target, background, center = comparison_pair(150)
        result = captcha.slide_comparison(target, background)
        assert abs(result - center) <= 15


class TestOthers:
    def test_detection(self, captcha):
        result = captcha.detection(captcha_image("3A7K"))
        assert isinstance(result, list)

    def test_select(self, captcha):
        # 240x96 放大图可被检测模型检出多个目标，真正执行裁剪+OCR 分支
        result = captcha.select(captcha_image("3A7K", width=240, height=96, font_size=56))
        assert isinstance(result, list) and len(result) >= 1
        for item in result:
            assert {"text", "bbox"} <= set(item)
            assert isinstance(item["text"], str)
            assert len(item["bbox"]) == 4

    def test_crop(self, captcha):
        result = captcha.crop(banded_image(), 100)
        upper = Image.open(io.BytesIO(base64.b64decode(result["slidingImage"])))
        lower = Image.open(io.BytesIO(base64.b64decode(result["backImage"])))
        assert upper.size == (400, 100)
        assert lower.size == (400, 200)
        # 下半部分应从 y=100 开始（绿色），旧实现错误地从 y=200 开始（蓝色）
        assert lower.convert("RGB").getpixel((0, 0)) == (0, 255, 0)

    def test_crop_invalid_y(self, captcha):
        with pytest.raises(ValueError):
            captcha.crop(banded_image(), 0)

    def test_calculate(self, captcha):
        result = captcha.calculate(
            captcha_image("12+30", width=140), charset_range=CharsetRange.DIGITS
        )
        assert result is None or isinstance(result, (int, float))

    def test_get_charset(self, captcha):
        charset = captcha.get_charset()
        assert isinstance(charset, list) and len(charset) > 100


class TestConcurrency:
    def test_concurrent_charset_isolation(self, captcha):
        digits_img = captcha_image("1234")
        letters_img = captcha_image("3A7K")
        errors = []
        digits_results = []

        def worker(use_digits):
            try:
                for _ in range(5):
                    if use_digits:
                        resp = captcha.classification(
                            digits_img, charset_range=CharsetRange.DIGITS
                        )
                        digits_results.append(resp)
                    else:
                        captcha.classification(letters_img)
            except Exception as e:  # pragma: no cover
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(True,)),
            threading.Thread(target=worker, args=(False,)),
            threading.Thread(target=worker, args=(True,)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        for r in digits_results:
            assert set(r) <= set("0123456789")


class TestModes:
    def test_ocr_mode_blocks_detection(self, ocr_only_captcha):
        result = ocr_only_captcha.classification(captcha_image("1234"))
        assert isinstance(result, str) and result
        with pytest.raises(RuntimeError, match="目标检测功能未启用"):
            ocr_only_captcha.detection(captcha_image("3A7K"))

    def test_det_mode_blocks_ocr(self, det_only_captcha):
        result = det_only_captcha.detection(captcha_image("3A7K"))
        assert isinstance(result, list)
        with pytest.raises(RuntimeError, match="OCR 功能未启用"):
            det_only_captcha.classification(captcha_image("3A7K"))

    def test_det_mode_blocks_select(self, det_only_captcha):
        # select 需要 det + OCR 两个引擎，det 模式应明确报 OCR 未启用
        with pytest.raises(RuntimeError, match="OCR 功能未启用"):
            det_only_captcha.select(captcha_image("3A7K"))

    def test_slide_works_in_det_mode(self, det_only_captcha):
        slider, background, center = slider_pair(120)
        result = det_only_captcha.capcode(
            slider, background, simple_target=True
        )
        assert abs(result - center) <= 15

    def test_invalid_mode(self):
        with pytest.raises(ValueError, match="mode 必须是"):
            CAPTCHA(mode="nonsense", show_ad=False)
