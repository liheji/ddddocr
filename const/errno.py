"""
统一错误码

每个错误码与默认响应文案绑定定义，R 缺省使用 Errno.message。
"""
from enum import IntEnum
from typing import cast


class Errno(IntEnum):
    """统一错误码（code + 默认响应文案）"""
    SUCCESS = (0, "success")
    FAILURE = (1, "failure")
    PARAM = (400, "参数错误")
    UNAUTHORIZED = (401, "未授权")
    FORBIDDEN = (403, "禁止访问")
    NOTFOUND = (404, "接口不存在")
    INTERNAL = (500, "服务器内部错误")
    SERVICE = (503, "服务错误")

    def __new__(cls, value: int, message: str) -> "Errno":
        obj = cast("Errno", int.__new__(cls, value))
        obj._value_ = value
        obj.message = message
        return obj
