"""图片工具单测（不依赖模型）"""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import requests

from const.setting import MAX_IMAGE_BYTES
from utils.image import get_image_bytes

from helpers import captcha_image, to_b64


class _StaticHandler(BaseHTTPRequestHandler):
    """返回固定字节的本地静态文件服务（真实 HTTP 回环，非 mock）"""
    payload = b""
    status = 200

    def do_GET(self):
        self.send_response(self.status)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        if self.status == 200:
            self.wfile.write(self.payload)

    def log_message(self, *args):
        pass


@pytest.fixture()
def image_server():
    server = HTTPServer(("127.0.0.1", 0), _StaticHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


class TestGetImageBytes:
    def test_bytes_passthrough(self):
        raw = b"abc"
        assert get_image_bytes(raw) == raw

    def test_base64(self):
        raw = captcha_image("1234")
        assert get_image_bytes(to_b64(raw)) == raw

    def test_data_uri(self):
        raw = captcha_image("1234")
        uri = "data:image/png;base64," + to_b64(raw)
        assert get_image_bytes(uri) == raw

    def test_invalid_base64(self):
        with pytest.raises(ValueError):
            get_image_bytes("not-a-base64!!!")

    def test_oversize_rejected(self):
        with pytest.raises(ValueError):
            get_image_bytes(b"x" * (MAX_IMAGE_BYTES + 1))

    def test_non_http_url_rejected(self):
        with pytest.raises(ValueError, match="仅支持 http/https"):
            get_image_bytes("ftp://example.com/x.png")


class TestParseRanges:
    def test_builtin_indices(self):
        from const.charset import CharsetRange, parse_ranges

        for charset_range in CharsetRange:
            assert parse_ranges(charset_range.value) == charset_range
            assert charset_range.charset

    def test_string_rejected(self):
        from const.charset import parse_ranges

        with pytest.raises(ValueError, match="仅支持内置索引"):
            parse_ranges("0123456789")
        with pytest.raises(ValueError, match="仅支持内置索引"):
            parse_ranges(["0", "1"])

    def test_out_of_range_rejected(self):
        from const.charset import parse_ranges

        with pytest.raises(ValueError, match="内置字符集索引无效"):
            parse_ranges(8)

    def test_bool_rejected(self):
        from const.charset import parse_ranges

        with pytest.raises(ValueError, match="仅支持内置索引"):
            parse_ranges(True)


class TestParseColorFilters:
    def test_preset_list(self):
        from const.color import ColorPreset, parse_color_filters

        assert parse_color_filters(["red"]) == [ColorPreset.RED]

    def test_preset_string(self):
        from const.color import ColorPreset, parse_color_filters

        assert parse_color_filters("red") == [ColorPreset.RED]

    def test_none(self):
        from const.color import parse_color_filters

        assert parse_color_filters(None) is None
        assert parse_color_filters([]) is None

    def test_custom_range_passthrough(self):
        from const.color import parse_color_filters

        custom = [[[0, 50, 50], [10, 255, 255]]]
        assert parse_color_filters(custom) == custom

    def test_unsupported_preset(self):
        from const.color import parse_color_filters

        with pytest.raises(ValueError, match="不支持的颜色预设"):
            parse_color_filters(["pink"])

    def test_invalid_item(self):
        from const.color import parse_color_filters

        with pytest.raises(ValueError, match="无效的颜色过滤参数"):
            parse_color_filters([123])


class TestUrlDownload:
    def test_http_download(self, image_server):
        raw = captcha_image("1234")
        _StaticHandler.status = 200
        _StaticHandler.payload = raw
        url = f"http://127.0.0.1:{image_server.server_port}/captcha.png"
        assert get_image_bytes(url) == raw

    def test_http_download_oversize(self, image_server):
        _StaticHandler.status = 200
        _StaticHandler.payload = b"x" * (MAX_IMAGE_BYTES + 1)
        url = f"http://127.0.0.1:{image_server.server_port}/big.png"
        with pytest.raises(ValueError, match="大小限制"):
            get_image_bytes(url)

    def test_http_download_error_status(self, image_server):
        _StaticHandler.status = 404
        _StaticHandler.payload = b""
        url = f"http://127.0.0.1:{image_server.server_port}/missing.png"
        with pytest.raises(requests.exceptions.HTTPError):
            get_image_bytes(url)
