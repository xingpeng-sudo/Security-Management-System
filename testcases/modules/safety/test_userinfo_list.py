"""
安全管理平台PC端 - 相关方人力资源库测试用例

接口: POST /aqserver/xl/userinfo/list

请求参数(均为非必填):
  pageNum, pageSize       - 分页
  orderByColumn, isAsc    - 排序
  cooperaDept             - 合作单位
  userName                - 人员姓名
  proName                 - 项目名称
  needDeptcode            - 需求部门编码
  identityCard            - 身份证号
  approveStatus           - 审批状态
"""
import allure
import pytest

from utils.parametrize import load_parametrize
from testcases.modules.safety._list_mixin import ListTestMixin


@allure.feature("安全管理平台PC端")
@allure.story("相关方人力资源库")
@pytest.mark.safety
class TestUserinfoList(ListTestMixin):
    """相关方人力资源库测试"""

    api_method = 'get_userinfo_list'

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/userinfo_list.json')
    def test_userinfo_list(self, logged_in_api, tc):
        """相关方人力资源库 - 参数化测试"""
        self._run_list_test(logged_in_api, tc)
