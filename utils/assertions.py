"""
断言工具模块
提供业务相关的自定义断言方法，支持统一断言入口

支持两种API响应格式：
1. 注册格式: {code: 0/500, msg: "...", data: {...}}
2. 登录格式: {success: true/false, status: "1"/"500", message: "...", data: {...}}
"""
import json
from typing import Any, Dict, Optional

from requests import Response

from utils.logger import logger


class AssertUtils:
    """断言工具类"""

    @staticmethod
    def assert_status_ok(response: Response, expected_code: int = 200):
        """断言HTTP状态码"""
        actual = response.status_code
        assert actual == expected_code, (
            f"HTTP状态码断言失败: 期望={expected_code}, 实际={actual}, "
            f"响应={response.text}"
        )

    @staticmethod
    def _parse_json(response: Response) -> dict:
        """解析响应JSON，失败时抛出明确的断言错误"""
        try:
            return response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"响应不是合法JSON: {response.text}")

    @staticmethod
    def _match_message(actual_msg: str, expected_msg: str, msg_mode: str) -> bool:
        """消息匹配"""
        if msg_mode == 'exact':
            return actual_msg == expected_msg
        return expected_msg in actual_msg

    @staticmethod
    def _assert_message(actual_msg: str, expected_msg: str, msg_mode: str, label: str):
        """消息断言，失败时给出清晰错误信息"""
        if not AssertUtils._match_message(actual_msg, expected_msg, msg_mode):
            mode_label = "精确匹配" if msg_mode == 'exact' else "包含匹配"
            assert False, (
                f"消息断言失败({mode_label}): 期望{label}'{expected_msg}', 实际='{actual_msg}'"
            )

    # ---- 注册格式断言 (code-based) ----

    @staticmethod
    def assert_business_success(
        response: Response,
        expected_msg: Optional[str] = None,
        msg_mode: str = 'contains'
    ):
        """
        断言业务成功（code=0）

        适用于注册接口响应格式: {code: 0, msg: "...", data: {...}}
        """
        resp_json = AssertUtils._parse_json(response)

        actual_code = resp_json.get('code')
        assert actual_code == 0, (
            f"业务码断言失败: 期望code=0(成功), 实际={actual_code}, "
            f"消息={resp_json.get('msg')}"
        )

        if expected_msg:
            AssertUtils._assert_message(
                resp_json.get('msg', ''), expected_msg, msg_mode, "包含"
            )

        logger.info(f"[Assert] 业务成功: code={actual_code}, msg={resp_json.get('msg')}")

    @staticmethod
    def assert_business_fail(
        response: Response,
        expected_code: Optional[int] = None,
        expected_msg: Optional[str] = None,
        msg_mode: str = 'contains'
    ):
        """
        断言业务失败

        适用于注册接口响应格式: {code: 500, msg: "..."}
        """
        resp_json = AssertUtils._parse_json(response)

        actual_code = resp_json.get('code')

        if expected_code is not None:
            assert actual_code == expected_code, (
                f"业务码断言失败: 期望={expected_code}, 实际={actual_code}"
            )
        else:
            assert actual_code != 0, (
                f"业务码断言失败: 期望非0(失败), 实际={actual_code}"
            )

        if expected_msg:
            AssertUtils._assert_message(
                resp_json.get('msg', ''), expected_msg, msg_mode, "包含"
            )

        logger.info(f"[Assert] 业务失败: code={actual_code}, msg={resp_json.get('msg')}")

    # ---- 登录格式断言 (success/status-based) ----

    @staticmethod
    def assert_login_success(response: Response):
        """
        断言登录成功

        适用于登录接口响应格式:
        {success: true, status: "1", data: {accesstoken: "...", ...}, message: null}
        """
        resp_json = AssertUtils._parse_json(response)

        assert resp_json.get('success') is True, (
            f"登录失败: success={resp_json.get('success')}, "
            f"message={resp_json.get('message')}"
        )

        assert resp_json.get('status') == '1', (
            f"登录状态异常: 期望status='1', 实际='{resp_json.get('status')}'"
        )

        # 验证返回了 accesstoken
        data = resp_json.get('data') or {}
        assert data.get('accesstoken'), (
            f"登录成功但未返回accesstoken: {response.text}"
        )

        logger.info(
            f"[Assert] 登录成功: status={resp_json.get('status')}, "
            f"userName={data.get('userName')}"
        )

    @staticmethod
    def assert_login_fail(
        response: Response,
        expected_message: Optional[str] = None,
        msg_mode: str = 'contains'
    ):
        """
        断言登录失败

        适用于登录接口响应格式:
        {success: false, status: "500", message: "...", data: null}
        """
        resp_json = AssertUtils._parse_json(response)

        assert resp_json.get('success') is False, (
            f"预期登录失败但成功: {response.text}"
        )

        assert resp_json.get('status') != '1', (
            f"预期登录失败但status='1': {response.text}"
        )

        if expected_message:
            actual_msg = resp_json.get('message') or ''
            AssertUtils._assert_message(actual_msg, expected_message, msg_mode, "包含")

        logger.info(
            f"[Assert] 登录失败: status={resp_json.get('status')}, "
            f"message={resp_json.get('message')}"
        )

    # ---- 通用字段断言 ----

    @staticmethod
    def assert_field_not_empty(data: Dict, field: str):
        """断言字段非空"""
        value = data.get(field)
        assert value is not None and value != '', (
            f"字段断言失败: {field} 不应为空"
        )

    @staticmethod
    def assert_field_value(data: Dict, field: str, expected: Any):
        """断言字段值"""
        actual = data.get(field)
        assert actual == expected, (
            f"字段断言失败: {field} 期望={expected}, 实际={actual}"
        )

    @staticmethod
    def assert_response_time(response: Response, max_seconds: float = 3.0):
        """断言响应时间"""
        actual = response.elapsed.total_seconds()
        assert actual <= max_seconds, (
            f"响应时间断言失败: 期望<={max_seconds}s, 实际={actual:.3f}s"
        )

    # ---- 统一断言入口 ----

    @classmethod
    def assert_by_expected(cls, response: Response, expected: dict):
        """
        根据 expected 字典自动选择断言方式

        支持两种API响应格式，通过 expected.format 指定：
        - "register"（默认）: 检查 code / msg
        - "login": 检查 success / status / message

        Args:
            response: Response对象
            expected: 期望结果字典，结构:
                {
                    "http_status": 200,
                    "format": "register" | "login",   # 可选，默认register
                    # register 格式:
                    "code": 0/非0,
                    "msg_contains": "xxx",
                    "msg_mode": "contains"|"exact",
                    # login 格式:
                    "success": true/false,
                    "status": "1"/"500"
                }
        """
        cls.assert_status_ok(response, expected.get('http_status', 200))

        api_format = expected.get('format', 'register')

        if api_format == 'login':
            expected_success = expected.get('success', True)
            if expected_success:
                cls.assert_login_success(response)
            else:
                cls.assert_login_fail(
                    response,
                    expected_message=expected.get('msg_contains'),
                    msg_mode=expected.get('msg_mode', 'contains')
                )
        else:
            msg_mode = expected.get('msg_mode', 'contains')
            expected_code = expected.get('code')

            if expected_code == 0:
                cls.assert_business_success(
                    response,
                    expected_msg=expected.get('msg_contains'),
                    msg_mode=msg_mode,
                )
            else:
                cls.assert_business_fail(
                    response,
                    expected_code=expected_code,
                    expected_msg=expected.get('msg_contains'),
                    msg_mode=msg_mode,
                )
