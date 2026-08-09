"""pytest 公共 fixture：真实 ddddocr 实例与会话级 Flask 客户端"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from const.mode import Mode
from core.captcha import CAPTCHA


@pytest.fixture(scope="session")
def captcha():
    """真实 ddddocr 实例（非 mock），会话级复用以节省模型加载时间"""
    return CAPTCHA(show_ad=False)


@pytest.fixture(scope="session")
def ocr_only_captcha():
    """仅 OCR 模式实例：目标检测应不可用"""
    return CAPTCHA(mode=Mode.OCR, show_ad=False)


@pytest.fixture(scope="session")
def det_only_captcha():
    """仅检测模式实例：OCR 应不可用，滑块应可用"""
    return CAPTCHA(mode=Mode.DET, show_ad=False)


@pytest.fixture(scope="session")
def client():
    """Flask 测试客户端（导入 app 时会初始化真实模型）"""
    import app as flask_app

    flask_app.app.config["TESTING"] = True
    return flask_app.app.test_client()


@pytest.fixture()
def det_client():
    """det 模式 Flask 测试客户端：真实 det-only 实例，测试结束后恢复 both 实例"""
    import app as flask_app
    from api import routes

    flask_app.app.config["TESTING"] = True
    original = routes.captcha
    routes.captcha = CAPTCHA(mode=Mode.DET, show_ad=False)
    yield flask_app.app.test_client()
    routes.captcha = original
