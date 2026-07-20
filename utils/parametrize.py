"""
参数化工具模块
消除测试用例中重复的 @pytest.mark.parametrize 模板代码
"""
from dataclasses import dataclass
from typing import Any, Dict

import pytest

from utils.data_loader import DataLoader


# 优先级 → Allure severity 映射
PRIORITY_SEVERITY_MAP = {
    'P0': 'blocker',
    'P1': 'critical',
    'P2': 'normal',
    'P3': 'minor',
}


@dataclass
class TestCase:
    """统一的测试用例数据对象，替代多参数拆分"""
    case_id: str
    case_name: str
    description: str
    priority: str
    data: Dict[str, Any]
    expected: Dict[str, Any]

    @property
    def severity(self) -> str:
        """根据优先级返回 Allure severity 字符串"""
        return PRIORITY_SEVERITY_MAP.get(self.priority, 'normal')


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并字典：override 中的值覆盖 base，缺失的 key 保留 base 的值。

    用于 defaults 继承合并。
    """
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_parametrize(file_path: str):
    """
    从JSON文件加载参数化测试数据，返回 pytest.mark.parametrize 装饰器

    用法:
        @load_parametrize('coordination/unit_login.json')
        def test_unit_login(self, unit_api, tc):
            processed = process_template(tc.data)
            ...

    JSON 结构支持两层继承（defaults 是基础，单 case 可覆盖）：
    {
      "defaults": {
        "data": {...},      # 用例数据默认值
        "expected": {...}   # 期望结果默认值
      },
      "test_cases": [
        {"case_id": "...", "data": {...}, "expected": {...}},
        ...
      ]
    }

    Args:
        file_path: 数据文件路径（相对于testdata目录）

    Returns:
        pytest.mark.parametrize 装饰器
    """
    full_data = DataLoader.load_json(file_path)
    raw_cases = DataLoader.load_test_cases(data=full_data)

    defaults = full_data.get('defaults', {}) if isinstance(full_data, dict) else {}
    default_data = defaults.get('data', {})
    default_expected = defaults.get('expected', {})

    test_cases = []
    ids = []

    for raw in raw_cases:
        # data / expected 继承 defaults（用例级覆盖 defaults 级）
        merged_data = _deep_merge(default_data, raw.get('data', {}))
        merged_expected = _deep_merge(default_expected, raw.get('expected', {}))

        tc = TestCase(
            case_id=raw['case_id'],
            case_name=raw['case_name'],
            description=raw.get('description', ''),
            priority=raw.get('priority', 'P2'),
            data=merged_data,
            expected=merged_expected,
        )
        test_cases.append(pytest.param(tc))
        ids.append(tc.case_id)

    return pytest.mark.parametrize("tc", test_cases, ids=ids)
