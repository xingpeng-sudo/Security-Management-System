"""
安全管理平台PC端 - 相关方企业列表测试用例

接口: POST /aqserver/zr/zrSupplier/list

请求参数(均为非必填):
  pageNum, pageSize       - 分页
  orderByColumn, isAsc    - 排序
  supplierName            - 企业名称
  businessLicenseNo       - 营业执照号
  legalRepresentative     - 法人代表
  blIssuingAuthority      - 发证机关
"""
import allure
import pytest

from utils.parametrize import load_parametrize
from testcases.modules.safety._list_mixin import ListTestMixin


@allure.feature("安全管理平台PC端")
@allure.story("相关方企业列表")
@pytest.mark.safety
class TestSupplierList(ListTestMixin):
    """相关方企业列表测试"""

    api_method = 'get_supplier_list'

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/supplier_list.json')
    def test_supplier_list(self, logged_in_api, tc):
        """相关方企业列表 - 参数化测试"""
        self._run_list_test(logged_in_api, tc)
