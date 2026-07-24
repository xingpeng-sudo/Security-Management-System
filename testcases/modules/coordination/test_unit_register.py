"""
协力安全管理 - 相关方单位注册测试用例

接口: POST /app/xl/unit/register
"""
import allure
import pytest
'''测试测试'''
from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger
from utils.parametrize import load_parametrize
from utils.template import process_template


@allure.feature("准入证模块")
@allure.story("相关方单位注册")
@pytest.mark.coordination
class TestUnitRegister:
    """相关方单位注册测试"""

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('coordination/unit_register.json')
    def test_unit_register(self, unit_api, tc):
        """相关方单位注册 - 参数化测试"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        processed_data = process_template(tc.data)
        response = unit_api.register(data=processed_data)
        attach_request_response(processed_data, response)

        AssertUtils.assert_by_expected(response, tc.expected)
        AssertUtils.assert_response_time(response, max_seconds=5.0)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")
