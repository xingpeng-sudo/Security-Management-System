"""
Allure 附件工具
消除测试用例中重复的 allure.attach 模板代码
"""
import json
from typing import Any, Dict, Optional

import allure
from requests import Response


def attach_json(data: Any, name: str = "数据") -> None:
    """附加 JSON 格式数据到 Allure 报告"""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, indent=2)
    allure.attach(data, name=name, attachment_type=allure.attachment_type.JSON)


def attach_text(text: str, name: str = "文本") -> None:
    """附加文本到 Allure 报告"""
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_request_response(request_data: Optional[Dict], response: Response) -> None:
    """
    附加请求和响应到 Allure 报告

    Args:
        request_data: 请求数据字典（None 时只附加响应）
        response: requests.Response 对象
    """
    if request_data is not None:
        attach_json(request_data, name="请求数据")
    if response is not None:
        # 尝试解析为 JSON，失败则附加原始文本
        try:
            response.json()
            attach_json(response.text, name="响应数据")
        except Exception:
            attach_text(response.text, name="响应数据")


def attach_response_body(response: Response, name: str = "响应数据") -> None:
    """仅附加响应体"""
    try:
        response.json()
        attach_json(response.text, name=name)
    except Exception:
        attach_text(response.text, name=name)


def set_severity_from_priority(priority: str) -> None:
    """
    根据优先级设置 Allure severity

    Args:
        priority: P0/P1/P2/P3
    """
    from utils.parametrize import PRIORITY_SEVERITY_MAP
    severity = PRIORITY_SEVERITY_MAP.get(priority, 'normal')
    allure.dynamic.severity(severity)
