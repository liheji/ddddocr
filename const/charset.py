"""
内置字符集定义与校验

字符集参数仅支持官方 README 中定义的内置索引（简称）0-7，
不接受自定义字符集字符串或列表（全集），以保证行为可维护、可预期。
外部传入的索引在 API 层统一转换为 CharsetRange 枚举。
"""
from enum import IntEnum
from typing import Dict


class CharsetRange(IntEnum):
    """内置字符集索引（与官方 README 0-7 语义一致）"""
    DIGITS = 0        # 纯数字
    LOWER = 1         # 纯小写英文
    UPPER = 2         # 纯大写英文
    LOWER_UPPER = 3   # 小写 + 大写
    LOWER_DIGITS = 4  # 小写 + 数字
    UPPER_DIGITS = 5  # 大写 + 数字
    ALNUM = 6         # 小写 + 大写 + 数字
    FULL = 7          # 默认字符库

    @property
    def charset(self) -> str:
        """当前索引对应的内置字符集字符串（与官方 README 0-7 语义一致）"""
        return _CHARSETS[self]


# 内置字符集索引 -> 字符集字符串（与官方 README 0-7 语义一致）
_CHARSETS: Dict[CharsetRange, str] = {
    CharsetRange.DIGITS: '0123456789',
    CharsetRange.LOWER: 'abcdefghijklmnopqrstuvwxyz',
    CharsetRange.UPPER: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    CharsetRange.LOWER_UPPER: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
    CharsetRange.LOWER_DIGITS: 'abcdefghijklmnopqrstuvwxyz0123456789',
    CharsetRange.UPPER_DIGITS: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    CharsetRange.ALNUM: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    CharsetRange.FULL: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
}


def parse_ranges(value) -> CharsetRange:
    """
    将外部传入的内置字符集索引转换为 CharsetRange。

    仅允许内置索引 int 0-7（简称）；其余输入（字符串/列表/越界索引）
    一律抛出 ValueError。
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("字符集仅支持内置索引 0-7，不接受自定义字符集字符串或列表")
    try:
        return CharsetRange(value)
    except ValueError:
        raise ValueError(f"内置字符集索引无效: {value}（支持 0-7）") from None
