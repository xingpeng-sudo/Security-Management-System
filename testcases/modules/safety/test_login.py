"""
安全管理平台PC端 - 登录测试用例

接口: POST /aqserver/api/login
"""
import allure
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger
from utils.parametrize import load_parametrize

"""测试"""
@allure.feature("安全管理平台PC端")
@allure.story("登录")
@pytest.mark.safety
class TestLogin:
    """PC端登录测试"""

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/login.json')
    def test_login(self, safety_api, tc):
        """登录 - 参数化测试"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        username = tc.data.get('username', '')
        password = tc.data.get('password', '')
        remember_me = tc.data.get('rememberMe', None)

        response = safety_api.login(
            username=username,
            password=password,
            remember_me=remember_me
        )
        attach_request_response(tc.data, response)

        # 基本HTTP状态码断言
        AssertUtils.assert_status_ok(response)
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        # 根据期望判断登录成功/失败
        should_success = tc.expected.get('should_success', False)
        resp_json = response.json()

        if should_success:
            # 登录成功：兼容多种响应格式
            # 格式1: {code: 0, msg: "...", token: "..."}
            # 格式2: {success: true, status: "1", message: "...", data: {...}}
            # 格式3: {code: 0, msg: "...", data: {...}}
            is_success = (
                resp_json.get('code') == 0
                or resp_json.get('success') is True
                or resp_json.get('status') == '1'
            )
            assert is_success, (
                f"期望登录成功但实际失败: {response.text[:500]}"
            )
            logger.info(f"[Test] 登录成功: {tc.case_id}")
        else:
            # 登录失败
            is_fail = (
                resp_json.get('code') != 0
                or resp_json.get('success') is False
                or resp_json.get('status') != '1'
            )
            assert is_fail, (
                f"期望登录失败但实际成功: {response.text[:500]}"
            )
            logger.info(f"[Test] 登录失败(符合预期): {tc.case_id}")

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")
