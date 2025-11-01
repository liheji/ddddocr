"""
标准化响应工具类
参考 Java R 类实现统一响应格式
"""
from flask import jsonify
from typing import Any, Optional, Dict


class R(dict):
    """统一响应格式类"""

    def __init__(self, code: int = 0, msg: str = "success", data: Any = None):
        """
        初始化响应对象
        :param code: 状态码，0表示成功，非0表示失败
        :param msg: 响应消息
        :param data: 响应数据
        """
        super().__init__()
        self['code'] = code
        self['msg'] = msg
        if data is not None:
            self['data'] = data

    @classmethod
    def ok(cls, msg: str = "success", data: Any = None) -> 'R':
        """
        成功响应
        :param msg: 响应消息
        :param data: 响应数据
        :return: R对象
        """
        return cls(code=0, msg=msg, data=data)

    @classmethod
    def error(cls, code: int = 1, msg: str = "failure", data: Any = None) -> 'R':
        """
        错误响应
        :param code: 错误码
        :param msg: 错误消息
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
        return cls.error(code=1, msg=msg)

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

    def json(self):
        """转换为Flask JSON响应"""
        return jsonify(self.to_dict())
