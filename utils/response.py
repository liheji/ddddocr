"""
标准化响应工具类
参考 Java R 类实现统一响应格式
"""
from typing import Any, Optional, Dict

from flask import Response, jsonify

from const.errno import Errno


class R(dict):
    """统一响应格式类"""

    def __init__(self, code: Errno = Errno.SUCCESS, msg: Optional[str] = None, data: Any = None):
        """
        初始化响应对象
        :param code: 错误码（Errno 枚举）
        :param msg: 响应消息，缺省使用 code.message
        :param data: 响应数据
        """
        if not isinstance(code, Errno):
            raise ValueError(f"code 必须是 Errno 枚举，当前: {code}")
        super().__init__()
        self['code'] = code
        self['msg'] = msg if msg is not None else code.message
        if data is not None:
            self['data'] = data

    @classmethod
    def ok(cls, msg: Optional[str] = None, data: Any = None) -> 'R':
        """
        成功响应
        :param msg: 响应消息，缺省为 success
        :param data: 响应数据
        :return: R对象
        """
        return cls(code=Errno.SUCCESS, msg=msg, data=data)

    @classmethod
    def error(cls, code: Errno = Errno.FAILURE, msg: Optional[str] = None, data: Any = None) -> 'R':
        """
        错误响应
        :param code: 错误码（Errno 枚举），缺省为 FAILURE
        :param msg: 错误消息，缺省使用 code.message
        :param data: 错误数据
        :return: R对象
        """
        return cls(code=code, msg=msg, data=data)

    @classmethod
    def error_msg(cls, msg: str) -> 'R':
        """
        错误响应（使用默认错误码1）
        :param msg: 错误消息
        :return: R对象
        """
        return cls.error(code=Errno.FAILURE, msg=msg)

    def put(self, key: str, value: Any) -> 'R':
        """
        添加键值对
        :param key: 键
        :param value: 值
        :return: 自身，支持链式调用
        """
        self[key] = value
        return self

    def get_code(self) -> int:
        """获取状态码"""
        return self.get('code', 0)

    def get_msg(self) -> str:
        """获取消息"""
        return self.get('msg', '')

    def get_data(self) -> Any:
        """获取数据"""
        return self.get('data')

    def is_ok(self) -> bool:
        """判断是否成功"""
        return self.get('code', 0) == 0

    def is_error(self) -> bool:
        """判断是否失败"""
        return self.get('code', 0) != 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return dict(self)

    def json(self) -> Response:
        """转换为Flask JSON响应"""
        return jsonify(self.to_dict())
