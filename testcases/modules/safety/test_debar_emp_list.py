"""
安全管理平台PC端 - 人员黑名单测试用例

接口: POST /aqserver/zr/debarEmp/list

请求参数(均为非必填):
  pageNum, pageSize       - 分页
  orderByColumn, isAsc    - 排序
  empName                 - 人员姓名
  idcardNo                - 身份证号
  approveStatus           - 审批状态
  debarStatus             - 拉黑状态
  entrustDeptcode         - 委托部门编码
"""
import allure
import pytest

from utils.parametrize import load_parametrize
from testcases.modules.safety._list_mixin import ListTestMixin


@allure.feature("安全管理平台PC端")
@allure.story("人员黑名单")
@pytest.mark.safety
class TestDebarEmpList(ListTestMixin):
    """人员黑名单测试"""

    api_method = 'get_debar_emp_list'

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/debar_emp.json')
    def test_debar_emp_list(self, logged_in_api, tc):
        """人员黑名单 - 参数化测试"""
        self._run_list_test(logged_in_api, tc)
