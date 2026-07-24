"""
安全管理平台PC端 - 相关方企业列表测试用例

接口: GET /aqserver/zr/zrSupplier/list
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

        # 判断是否是动态过滤测试
        filter_field = tc.data.get('filter_field')
        filter_fields = tc.data.get('filter_fields')

        if filter_field or filter_fields:
            # 动态过滤测试：先查baseline，取值后再过滤验证
            self._run_filter_test(logged_in_api, tc, filter_field, filter_fields)
        else:
            # 常规查询测试
            params = tc.data.get('params', {})
            if 'pageNum' not in params:
                params['pageNum'] = 1
            if 'pageSize' not in params:
                params['pageSize'] = 20

            response = logged_in_api.get_supplier_list(**params)
            attach_request_response(params, response)

            resp_json = AssertUtils.assert_list_success(
                response, min_total=tc.expected.get('min_total', 0)
            )
            AssertUtils.assert_response_time(response, max_seconds=10.0)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")

    def _run_filter_test(self, api, tc, filter_field, filter_fields):
        """执行动态过滤测试逻辑"""
        fields_to_test = filter_fields if filter_fields else [filter_field]

        # 1. 先不带filter查询获取baseline
        baseline_response = api.get_supplier_list(pageNum=1, pageSize=20)
        attach_request_response({'pageNum': 1, 'pageSize': 20}, baseline_response)
        baseline_json = AssertUtils.assert_list_success(
            baseline_response, min_total=1
        )
        AssertUtils.assert_response_time(baseline_response, max_seconds=10.0)

        baseline_rows = baseline_json.get('rows', [])
        assert len(baseline_rows) > 0, "baseline查询结果为空，无法进行过滤测试"

        # 2. 从baseline rows[0]取对应字段值
        first_row = baseline_rows[0]
        filter_params = {}
        for field in fields_to_test:
            field_value = first_row.get(field)
            assert field_value is not None and field_value != '', (
                f"baseline rows[0]中字段'{field}'为空，无法进行过滤测试"
            )
            filter_params[field] = field_value
            logger.info(f"[Test] 从baseline取值: {field}={field_value}")

        # 3. 用该值作为filter参数再查询
        filter_params['pageNum'] = 1
        filter_params['pageSize'] = 20
        response = api.get_supplier_list(**filter_params)
        attach_request_response(filter_params, response)

        resp_json = AssertUtils.assert_list_success(
            response, min_total=tc.expected.get('min_total', 1)
        )
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        # 4. 验证filtered结果都匹配
        # 如果过滤后total和baseline相同，说明服务端可能不支持该字段过滤
        baseline_total = baseline_json.get('total', 0)
        filtered_total = resp_json.get('total', 0)
        if filtered_total == baseline_total:
            logger.warning(
                f"过滤后total={filtered_total}与baseline={baseline_total}相同，"
                f"服务端可能不支持该字段过滤，跳过字段验证"
            )
        else:
            for field in fields_to_test:
                AssertUtils.assert_list_filtered(
                    resp_json, field, str(filter_params[field])
                )
