"""
安全管理平台PC端 - 相关方企业列表测试用例

接口: POST /aqserver/zr/zrSupplier/list

请求参数(均为非必填):
  pageNum, pageSize       - 分页
  orderByColumn, isAsc    - 排序
  supplierName            - 企业名称
  businessLicenseNo       - 营业执照号
  legalRepresentative     - 法人代表
"""
import allure
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger
from utils.parametrize import load_parametrize


@allure.feature("安全管理平台PC端")
@allure.story("相关方企业列表")
@pytest.mark.safety
class TestSupplierList:
    """相关方企业列表测试"""

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/supplier_list.json')
    def test_supplier_list(self, logged_in_api, tc):
        """相关方企业列表 - 参数化测试"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        params = tc.data.get('params', {})

        response = logged_in_api.get_supplier_list(**params)
        attach_request_response(params, response)

        self._assert_response(response, tc, params)
        self._verify_filter_result(response, tc, params)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")

    def _assert_response(self, response, tc, params):
        """统一断言"""
        expected = tc.expected

        AssertUtils.assert_status_ok(response)
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        if expected.get('allow_error'):
            try:
                resp_json = response.json()
                logger.info(f"[Test] 边界测试响应: code={resp_json.get('code')}, total={resp_json.get('total')}")
            except Exception:
                pytest.fail(f"边界测试期望返回合法JSON，实际: {response.text[:500]}")
            return

        resp_json = AssertUtils.assert_list_success(
            response, min_total=expected.get('min_total', 0)
        )

        max_rows = expected.get('max_rows')
        if max_rows is not None:
            actual_rows = len(resp_json.get('rows', []))
            assert actual_rows <= max_rows, f"rows数量断言失败: 期望<={max_rows}, 实际={actual_rows}"

        if expected.get('expect_empty_rows'):
            rows = resp_json.get('rows', [])
            assert len(rows) == 0, f"期望返回空rows，实际返回{len(rows)}条"

        if expected.get('verify_sorting'):
            self._verify_sorting(resp_json, params)

    def _verify_sorting(self, resp_json, params):
        """验证排序结果是否正确"""
        order_by = params.get('orderByColumn')
        if not order_by:
            return

        is_asc = params.get('isAsc', 'asc').lower() == 'asc'
        rows = resp_json.get('rows', [])

        if len(rows) < 2:
            pytest.skip(f"返回数据不足2条({len(rows)})，无法验证排序，跳过")

        values = [str(row.get(order_by, '')) for row in rows]
        sorted_values = sorted(values, reverse=not is_asc)

        assert values == sorted_values, (
            f"排序验证失败: orderByColumn={order_by}, isAsc={params.get('isAsc')}, "
            f"前5个值: {values[:5]}"
        )
        logger.info(
            f"[Test] 排序验证通过: {order_by} "
            f"{'升序' if is_asc else '降序'}, 共{len(rows)}条"
        )

    def _verify_filter_result(self, response, tc, params):
        """
        验证过滤结果: 每条row的对应字段都包含请求参数中的值。
        排除分页和排序参数，只验证过滤字段。
        """
        non_filter_keys = {'pageNum', 'pageSize', 'orderByColumn', 'isAsc'}
        filter_keys = [k for k in params.keys() if k not in non_filter_keys]
        if not filter_keys:
            return

        if tc.expected.get('allow_error') or tc.expected.get('expect_empty_rows'):
            return

        try:
            resp_json = response.json()
        except Exception:
            return

        logger.info(f"[Test] 验证过滤结果，过滤字段: {filter_keys}")
        rows = resp_json.get('rows', [])
        for row in rows:
            for key in filter_keys:
                expected_value = str(params[key])
                actual_value = str(row.get(key, ''))
                assert expected_value in actual_value, (
                    f"过滤验证失败: {key} 期望包含'{expected_value}', 实际='{actual_value}'"
                )
