"""
API 层辅助函数：请求参数解析与统一错误响应
"""
import logging
from typing import Any

from flask import Request, Response
from werkzeug.exceptions import HTTPException

from core import FeatureDisabledError
from const.errno import Errno
from utils import R, get_image_bytes

logger = logging.getLogger(__name__)


def require_single_image(request: Request, field: str) -> bytes:
    """获取单图参数并归一化为二进制字节（JSON 字段或 multipart 文件），缺失/非法时抛 ValueError"""
    data = request.get_json(silent=True)
    if data and field in data:
        image = data[field]
    else:
        file = request.files.get(field)
        image = file.read() if file is not None else None
    if not image:
        raise ValueError(f'缺少必需参数: {field}')
    return get_image_bytes(image)


def error_response(e: Exception) -> Response:
    """按异常类型返回错误响应：功能未启用 -> 503，其余参数/输入错误 -> 400"""
    if isinstance(e, HTTPException):
        # 透传 werkzeug 异常（如请求体过大 413），交给 Flask 错误处理器
        raise e
    if isinstance(e, FeatureDisabledError):
        return R.error(Errno.SERVICE, str(e)).json()
    return R.error(Errno.PARAM, str(e)).json()


def service_result(result: Any, fail_msg: str) -> Response:
    """识别成功返回 data；失败（None）返回统一服务错误响应"""
    if result is None:
        logger.error(fail_msg)
        return R.error(Errno.SERVICE, fail_msg).json()
    return R.ok(data=result).json()
