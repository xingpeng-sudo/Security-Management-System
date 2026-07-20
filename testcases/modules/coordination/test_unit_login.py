"""
协力安全管理 - 相关方单位登录测试用例

接口: POST /app/xl/unit/login/{account}/{password}

登录接口使用路径参数传递账号密码，account和password来源于注册接口返回。
本文件只测登录异常路径；正常登录由 test_flow.py 端到端流程覆盖。
"""
import allure
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger
from utils.parametrize import load_parametrize


@allure.feature("企业级角色模块")
@allure.story("相关方单位登录")
@pytest.mark.coordination
class TestUnitLogin:
    """相关方单位登录测试（异常路径）"""

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('coordination/unit_login.json')
    def test_unit_login_fail(self, unit_api, tc):
        """异常登录 - 参数化测试"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        account = tc.data.get('account', '')
        password = tc.data.get('password', '')

        response = unit_api.login(account=account, password=password)
        attach_request_response(
            {"account": account, "password": password},
            response
        )

        AssertUtils.assert_by_expected(response, tc.expected)
        AssertUtils.assert_response_time(response, max_seconds=5.0)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")
