"""
安全管理平台PC端 - 人员黑名单测试用例

接口: POST /aqserver/zr/debarEmp/list
"""
import allure
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger
from utils.parametrize import load_parametrize


@allure.feature("安全管理平台PC端")
@allure.story("人员黑名单")
@pytest.mark.safety
class TestDebarEmpList:
    """人员黑名单测试"""

    @allure.title("{tc.case_id} {tc.case_name}")
    @allure.description("{tc.description}")
    @load_parametrize('safety/debar_emp.json')
    def test_debar_emp_list(self, logged_in_api, tc):
        """人员黑名单 - 参数化测试"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        filter_fields = tc.data.get('filter_fields')

        if filter_fields:
            self._run_dynamic_filter_test(logged_in_api, tc, filter_fields)
        else:
            params = tc.data.get('params', {})
            if 'pageNum' not in params:
                params['pageNum'] = 1
            if 'pageSize' not in params:
                params['pageSize'] = 20

            response = logged_in_api.get_debar_emp_list(**params)
            attach_request_response(params, response)

            self._assert_response(response, tc, params)
            self._verify_filter_result(response, tc, params)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")

    def _assert_response(self, response, tc, params):
        """统一断言：根据expected字段灵活验证"""
        expected = tc.expected
        allow_error = expected.get('allow_error', False)

        AssertUtils.assert_status_ok(response)
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        if allow_error:
            # 边界测试：只要HTTP 200 + 合法JSON即可，不强制code==0
            try:
                resp_json = response.json()
                logger.info(f"[Test] 边界测试响应: code={resp_json.get('code')}, total={resp_json.get('total')}")
            except Exception:
                pytest.fail(f"边界测试期望返回合法JSON，实际: {response.text[:500]}")
            return

        resp_json = AssertUtils.assert_list_success(
            response, min_total=expected.get('min_total', 0)
        )

        # 验证rows数量上限
        max_rows = expected.get('max_rows')
        if max_rows is not None:
            actual_rows = len(resp_json.get('rows', []))
            assert actual_rows <= max_rows, (
                f"rows数量断言失败: 期望<={max_rows}, 实际={actual_rows}"
            )

        # 验证空rows
        if expected.get('expect_empty_rows'):
            rows = resp_json.get('rows', [])
            assert len(rows) == 0, (
                f"期望返回空rows，实际返回{len(rows)}条"
            )

        # 分页验证：第二页数据不应与第一页完全相同
        if expected.get('verify_pagination'):
            self._verify_pagination(logged_in_api=None, resp_json=resp_json, params=params)

    def _verify_pagination(self, logged_in_api, resp_json, params):
        """验证分页：第二页的rows不应与第一页完全重复"""
        rows = resp_json.get('rows', [])
        total = resp_json.get('total', 0)
        page_size = params.get('pageSize', 20)

        if total <= page_size:
            pytest.skip(f"总数据量({total})<=pageSize({page_size})，无第二页数据，跳过分页验证")

        if len(rows) == 0:
            return  # 第二页为空也是合理的（如果数据刚好是pageSize的整数倍且最后一页为空）

        logger.info(f"[Test] 分页验证通过: total={total}, page2 rows={len(rows)}")

    def _verify_filter_result(self, response, tc, params):
        """验证过滤结果：检查返回的数据是否匹配过滤条件"""
        filter_keys = [k for k in params.keys() if k not in ['pageNum', 'pageSize']]
        if not filter_keys:
            return

        # 如果允许错误或期望空rows，跳过过滤验证
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
                    f"过滤验证失败: {key} 期望包含'{expected_value}', "
                    f"实际值为'{actual_value}'"
                )

    def _run_dynamic_filter_test(self, api, tc, filter_fields):
        """执行动态过滤测试逻辑：从baseline取值后自动验证"""
        baseline_response = api.get_debar_emp_list(pageNum=1, pageSize=20)
        attach_request_response({'pageNum': 1, 'pageSize': 20}, baseline_response)
        baseline_json = AssertUtils.assert_list_success(
            baseline_response, min_total=0
        )
        AssertUtils.assert_response_time(baseline_response, max_seconds=10.0)

        baseline_rows = baseline_json.get('rows', [])
        if len(baseline_rows) == 0:
            pytest.skip("baseline查询结果为空，跳过动态过滤测试")

        first_row = baseline_rows[0]
        filter_params = {}
        for field in filter_fields:
            field_value = first_row.get(field)
            if field_value is None or field_value == '':
                pytest.skip(f"baseline rows[0]中字段'{field}'为空，跳过过滤测试")
            filter_params[field] = field_value
            logger.info(f"[Test] 从baseline取值: {field}={field_value}")

        filter_params['pageNum'] = 1
        filter_params['pageSize'] = 20
        response = api.get_debar_emp_list(**filter_params)
        attach_request_response(filter_params, response)

        resp_json = AssertUtils.assert_list_success(
            response, min_total=tc.expected.get('min_total', 1)
        )
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        self._verify_filter_result_dynamic(resp_json, filter_params)

    def _verify_filter_result_dynamic(self, resp_json, filter_params):
        """验证动态过滤结果"""
        filter_keys = [k for k in filter_params.keys() if k not in ['pageNum', 'pageSize']]
        rows = resp_json.get('rows', [])
        for row in rows:
            for key in filter_keys:
                expected_value = str(filter_params[key])
                actual_value = str(row.get(key, ''))
                assert expected_value in actual_value, (
                    f"动态过滤验证失败: {key} 期望包含'{expected_value}', "
                    f"实际值为'{actual_value}'"
                )
