"""
协力安全管理 - 业务流程测试

测试完整的业务链路：注册 -> 登录
验证两个API之间的数据传递和联动性

联动关系：
  注册接口返回 {account, password}
  -> 登录接口使用该 account/password 作为路径参数
  -> 登录成功返回 accesstoken
"""
import allure
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response
from utils.data_factory import make_register_data
from utils.logger import logger


@allure.feature("准入证模块")
@allure.story("业务流程")
@pytest.mark.coordination
class TestCoordinationFlow:
    """协力安全管理 - 端到端业务流程测试"""

    @allure.title("完整流程: 注册->登录")
    @allure.description(
        "验证相关方单位从注册到登录的完整业务链路：\n"
        "1. 注册相关方单位，获取返回的 account 和 password\n"
        "2. 使用该 account 和 password 登录\n"
        "3. 验证登录成功并返回 accesstoken"
    )
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.p0
    def test_register_to_login_flow(self, unit_api):
        """
        完整业务流程测试：注册 -> 登录

        此测试验证两个API的核心联动：
        - register 返回的 data.account 和 data.password 是 login 的输入
        - login 使用路径参数 /login/{account}/{password} 进行认证
        """

        # ========== Step 1: 注册 ==========
        with allure.step("Step 1: 注册相关方单位"):
            register_data = make_register_data(prefix="流程测试公司")
            logger.info(f"流程测试开始: 公司名称={register_data['supplierName']}")

            reg_response = unit_api.register(data=register_data)
            attach_request_response(register_data, reg_response)

            AssertUtils.assert_status_ok(reg_response)
            AssertUtils.assert_business_success(
                reg_response,
                expected_msg="通过审核",
                msg_mode='contains'
            )

            # 提取注册返回的 account 和 password -- 这是两个API的联动点
            reg_json = reg_response.json()
            account = reg_json['data']['account']
            password = reg_json['data']['password']

            logger.info(f"Step 1 完成: 注册成功, account={account}")

        # ========== Step 2: 登录 ==========
        with allure.step("Step 2: 使用注册返回的凭据登录"):
            login_response = unit_api.login(account=account, password=password)
            attach_request_response(
                {"account": account, "password": password},
                login_response
            )

            AssertUtils.assert_status_ok(login_response)
            AssertUtils.assert_login_success(login_response)

            login_data = login_response.json().get('data', {})
            logger.info(f"Step 2 完成: 登录成功, userName={login_data.get('userName')}")

        # ========== Step 3: 验证返回数据完整性 ==========
        with allure.step("Step 3: 验证登录返回数据"):
            AssertUtils.assert_field_not_empty(login_data, 'accesstoken')
            AssertUtils.assert_field_not_empty(login_data, 'userName')
            logger.info("Step 3 完成: 数据验证通过")

        logger.info("完整业务流程测试执行完成: 注册->登录 全部通过")
