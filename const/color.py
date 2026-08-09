"""
颜色过滤预设定义与校验

仅支持 ddddocr 1.6.1 原生 ColorFilter 支持的颜色预设，
pink 等未列入的一律视为不支持（明确报错）。
外部字符串在 API 层统一转换为 ColorPreset 枚举。
"""
from enum import Enum
from typing import FrozenSet, List, Optional, Tuple


class ColorPreset(Enum):
    """ddddocr 1.6.1 原生 ColorFilter 支持的颜色预设"""
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    ORANGE = 'orange'
    PURPLE = 'purple'
    CYAN = 'cyan'
    BLACK = 'black'
    WHITE = 'white'
    GRAY = 'gray'


# 预设颜色名称集合（供错误提示/展示使用）
SUPPORTED_COLOR_PRESETS: FrozenSet[str] = frozenset(p.value for p in ColorPreset)


def parse_color_filters(color_filter_colors) -> Optional[list]:
    """
    将外部颜色过滤参数归一化：预设字符串 -> ColorPreset，自定义 HSV 范围原样保留。
    未知预设或非法结构直接报错（明确不支持）。
    """
    if not color_filter_colors:
        return None
    if isinstance(color_filter_colors, str):
        color_filter_colors = [color_filter_colors]
    result = []
    for c in color_filter_colors:
        if isinstance(c, str):
            try:
                result.append(ColorPreset(c.lower()))
            except ValueError:
                raise ValueError(
                    f"不支持的颜色预设: {c}（可用: {sorted(SUPPORTED_COLOR_PRESETS)}）"
                ) from None
        elif isinstance(c, (list, tuple)) and len(c) == 2:
            result.append(c)
        else:
            raise ValueError(f"无效的颜色过滤参数: {c}")
    return result or None


def split_color_filters(
    color_filter_colors: Optional[list]
) -> Tuple[Optional[List[str]], Optional[list]]:
    """
    拆分归一化后的颜色过滤参数为库原生需要的两部分：
    预设颜色名称列表 + 自定义HSV范围列表。
    """
    presets, custom = [], []
    for c in color_filter_colors or []:
        if isinstance(c, ColorPreset):
            presets.append(c.value)
        else:
            custom.append(c)
    return (presets or None), (custom or None)
