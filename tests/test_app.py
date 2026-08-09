"""Flask API 路由集成测试：真实模型 + 真实 HTTP 调用路径"""
import base64
import io

from PIL import Image

from const.setting import MAX_IMAGE_BYTES
from helpers import (
    banded_image,
    captcha_image,
    comparison_pair,
    red_text_image,
    slider_pair,
    to_b64,
)


def post_json(client, path, payload):
    return client.post(path, json=payload)


class TestBasicRoutes:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["status"] == "running"
        assert body["data"]["version"]

    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["status"] == "running"
        assert body["data"]["version"]

    def test_not_found(self, client):
        resp = client.get("/no-such-api")
        assert resp.status_code == 404
        assert resp.get_json()["code"] == 404

    def test_too_large_request(self, client):
        resp = client.post("/classification", data=b"x" * (MAX_IMAGE_BYTES + 1))
        assert resp.status_code == 413
        assert resp.get_json()["code"] == 400

    def test_missing_image(self, client):
        resp = post_json(client, "/classification", {})
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 400

    def test_disabled_feature_maps_to_503(self):
        import app as flask_app
        from api.helpers import error_response
        from core import FeatureDisabledError

        with flask_app.app.app_context():
            resp = error_response(FeatureDisabledError("OCR 功能未启用（当前启动模式: det）"))
            body = resp.get_json()
        assert body["code"] == 503
        assert "OCR 功能未启用" in body["msg"]


class TestClassificationRoute:
    def test_basic(self, client):
        resp = post_json(client, "/classification", {"image": to_b64(captcha_image("3A7K"))})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 0
        assert isinstance(body["data"], str) and body["data"]

    def test_probability(self, client):
        resp = post_json(client, "/classification", {
            "image": to_b64(captcha_image("3A7K")), "probability": True,
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert {"text", "probabilities", "charset", "confidence"} <= set(data)

    def test_charset_no_leak(self, client):
        first = post_json(client, "/classification", {
            "image": to_b64(captcha_image("3A7K")), "charset_ranges": 0,
        })
        assert set(first.get_json()["data"]) <= set("0123456789")
        second = post_json(client, "/classification", {"image": to_b64(captcha_image("3A7K"))})
        assert any(ch.isalpha() for ch in second.get_json()["data"])

    def test_file_upload(self, client):
        raw = captcha_image("1234")
        data = {"image": (io.BytesIO(raw), "captcha.png")}
        resp = client.post(
            "/classification", data=data, content_type="multipart/form-data"
        )
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

    def test_color_filter_preset(self, client):
        resp = post_json(client, "/classification", {
            "image": to_b64(red_text_image("1234")), "color_filter_colors": ["red"],
        })
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

    def test_unsupported_color_preset(self, client):
        resp = post_json(client, "/classification", {
            "image": to_b64(red_text_image("1234")), "color_filter_colors": ["pink"],
        })
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 400


class TestCaptchaBase64Compat:
    """MoviePilot 兼容接口：POST /captcha/base64"""

    @staticmethod
    def _moviepilot_get_captcha_text(client, image_b64):
        """复现 MoviePilot OcrHelper.get_captcha_text 的取值逻辑"""
        resp = client.post("/captcha/base64", json={"base64_img": image_b64})
        if resp.status_code >= 400:
            return ""
        return (resp.get_json() or {}).get("result") or ""

    def test_success_response_shape(self, client):
        resp = post_json(client, "/captcha/base64", {
            "base64_img": to_b64(captcha_image("3A7K")),
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert set(body) == {"result"}
        assert isinstance(body["result"], str) and body["result"]

    def test_moviepilot_usage_success(self, client):
        text = self._moviepilot_get_captcha_text(client, to_b64(captcha_image("3A7K")))
        assert isinstance(text, str) and text

    def test_moviepilot_usage_error_returns_empty(self, client):
        assert self._moviepilot_get_captcha_text(client, "") == ""
        assert self._moviepilot_get_captcha_text(client, "not-a-base64!!!") == ""

    def test_missing_param(self, client):
        resp = post_json(client, "/captcha/base64", {})
        assert resp.status_code == 400
        assert resp.get_json() == {"result": None}

    def test_invalid_base64(self, client):
        resp = post_json(client, "/captcha/base64", {
            "base64_img": "not-a-base64!!!",
        })
        assert resp.status_code == 400
        assert resp.get_json() == {"result": None}


class TestSetRangesRoute:
    def test_int_zero_mapping(self, client):
        resp = post_json(client, "/set_ranges", {"ranges": 0})
        assert resp.get_json()["code"] == 0
        try:
            resp = post_json(client, "/classification", {"image": to_b64(captcha_image("3A7K"))})
            data = resp.get_json()["data"]
            assert set(data) <= set("0123456789")
        finally:
            post_json(client, "/set_ranges", {"ranges": None})

    def test_clear(self, client):
        post_json(client, "/set_ranges", {"ranges": 0})
        post_json(client, "/set_ranges", {"ranges": None})
        resp = post_json(client, "/classification", {"image": to_b64(captcha_image("3A7K"))})
        assert any(ch.isalpha() for ch in resp.get_json()["data"])

    def test_full_charset_string_rejected(self, client):
        resp = post_json(client, "/set_ranges", {"ranges": "0123456789"})
        assert resp.get_json()["code"] == 400
        resp = post_json(client, "/classification", {
            "image": to_b64(captcha_image("3A7K")), "charset_ranges": "0123456789",
        })
        assert resp.get_json()["code"] == 400


class TestOtherRoutes:
    def test_crop(self, client):
        resp = post_json(client, "/crop", {
            "image": to_b64(banded_image()), "y_coordinate": 100,
        })
        assert resp.get_json()["code"] == 0
        data = resp.get_json()["data"]
        upper = Image.open(io.BytesIO(base64.b64decode(data["slidingImage"])))
        lower = Image.open(io.BytesIO(base64.b64decode(data["backImage"])))
        assert upper.size == (400, 100)
        assert lower.size == (400, 200)

    def test_crop_file_upload(self, client):
        data = {
            "image": (io.BytesIO(banded_image()), "band.png"),
            "y_coordinate": "100",
        }
        resp = client.post("/crop", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

    def test_capcode(self, client):
        slider, background, _ = slider_pair(120)
        resp = post_json(client, "/capcode", {
            "slidingImage": to_b64(slider),
            "backImage": to_b64(background),
            "simpleTarget": True,
        })
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], (int, float))

    def test_slide_comparison(self, client):
        target, background, _ = comparison_pair(150)
        resp = post_json(client, "/slideComparison", {
            "slidingImage": to_b64(target),
            "backImage": to_b64(background),
        })
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], (int, float))

    def test_detection(self, client):
        resp = post_json(client, "/detection", {"image": to_b64(captcha_image("3A7K"))})
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], list)

    def test_detection_file_upload(self, client):
        data = {"image": (io.BytesIO(captcha_image("3A7K")), "captcha.png")}
        resp = client.post("/detection", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], list)

    def test_select(self, client):
        resp = post_json(client, "/select", {"image": to_b64(captcha_image("3A7K"))})
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], list)

    def test_select_file_upload(self, client):
        data = {"image": (io.BytesIO(captcha_image("3A7K")), "captcha.png")}
        resp = client.post("/select", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0
        assert isinstance(resp.get_json()["data"], list)

    def test_calculate(self, client):
        resp = post_json(client, "/calculate", {
            "image": to_b64(captcha_image("12+30", width=140)),
            "charset_ranges": 0,
        })
        assert resp.status_code in (200, 503)

    def test_calculate_file_upload(self, client):
        data = {"image": (io.BytesIO(captcha_image("12+30", width=140)), "captcha.png")}
        resp = client.post("/calculate", data=data, content_type="multipart/form-data")
        assert resp.status_code in (200, 503)

    def test_status_includes_charset(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "running"
        assert data["version"]
        assert isinstance(data["charset"], list) and len(data["charset"]) > 100
        assert "ranges" in data

    def test_charset_endpoint_removed(self, client):
        assert client.get("/charset").status_code == 404

    def test_config_endpoint_removed(self, client):
        assert client.get("/config").status_code == 404


class TestParamValidation:
    """缺参请求统一返回业务码 400"""

    def test_capcode_missing_params(self, client):
        resp = post_json(client, "/capcode", {})
        assert resp.get_json()["code"] == 400

    def test_slide_comparison_missing_params(self, client):
        resp = post_json(client, "/slideComparison", {})
        assert resp.get_json()["code"] == 400

    def test_crop_missing_params(self, client):
        resp = post_json(client, "/crop", {})
        assert resp.get_json()["code"] == 400

    def test_crop_missing_y_coordinate(self, client):
        resp = post_json(client, "/crop", {"image": to_b64(banded_image())})
        assert resp.get_json()["code"] == 400

    def test_set_ranges_missing_param(self, client):
        resp = post_json(client, "/set_ranges", {})
        assert resp.get_json()["code"] == 400


class TestDetModeRoutes:
    """det 模式（仅目标检测）下 OCR 相关接口返回 503，/status 不含字符集"""

    def test_classification_returns_503(self, det_client):
        resp = det_client.post(
            "/classification", json={"image": to_b64(captcha_image("3A7K"))}
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 503
        assert "OCR 功能未启用" in body["msg"]

    def test_captcha_base64_returns_503(self, det_client):
        resp = det_client.post(
            "/captcha/base64", json={"base64_img": to_b64(captcha_image("3A7K"))}
        )
        assert resp.status_code == 503
        assert resp.get_json() == {"result": None}

    def test_status_without_charset(self, det_client):
        resp = det_client.get("/status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "running"
        assert "charset" not in data
        assert "ranges" not in data

    def test_select_returns_503(self, det_client):
        resp = det_client.post(
            "/select", json={"image": to_b64(captcha_image("3A7K"))}
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 503
        assert "OCR 功能未启用" in body["msg"]
