"""
安全管理平台 - 列表过滤查询测试通用Mixin

消除4个列表测试文件中重复的断言/排序/过滤/分页验证逻辑。

修复点(vs 原始重复代码):
1. 排序验证按字段类型比较: 数字字段用数值比较, 避免"10" < "2"字典序错误
2. 过滤验证区分字段类型: 枚举/身份证/营业执照号字段精确匹配, 其他字段包含匹配
3. 新增分页不重叠验证: 第1页和第2页rows不应有交集
4. 新增过滤完整性验证: 接口过滤查询应与全量本地过滤结果一致
"""
import pytest

from utils.assertions import AssertUtils
from utils.attachments import attach_request_response, set_severity_from_priority
from utils.logger import logger


# 非过滤参数(分页/排序), 过滤验证时排除
NON_FILTER_KEYS = {'pageNum', 'pageSize', 'orderByColumn', 'isAsc'}

# 需要精确匹配的字段(枚举/身份证/营业执照号/部门编码等)
# 其他字段默认用包含匹配
EXACT_MATCH_FIELDS = {
    'approveStatus', 'debarStatus',
    'identityCard', 'idcardNo',
    'businessLicenseNo',
    'needDeptcode', 'proxyDeptcode', 'entrustDeptcode',
}

# 过滤完整性验证时, 全量查询的pageSize(假设测试环境数据不超过此值)
COMPLETENESS_FETCH_SIZE = 500


def _row_signature(row: dict) -> tuple:
    """生成row的签名, 用于翻页重复检测(字段值统一转字符串)"""
    return tuple(sorted((k, str(v)) for k, v in row.items()))


class ListTestMixin:
    """列表过滤查询测试通用Mixin

    子类需声明类属性:
        api_method: str  # SafetyAPI上的方法名, 如 'get_supplier_list'
    """
    api_method: str = ''

    def _call_api(self, logged_in_api, params: dict):
        """调用对应的列表接口"""
        return getattr(logged_in_api, self.api_method)(**params)

    def _run_list_test(self, logged_in_api, tc):
        """列表测试通用执行流程(子类test方法只需调用此方法)"""
        set_severity_from_priority(tc.priority)
        logger.info(f"执行测试用例: {tc.case_id} - {tc.case_name} [{tc.priority}]")

        params = tc.data.get('params', {})
        response = self._call_api(logged_in_api, params)
        attach_request_response(params, response)

        # 基础断言: HTTP状态码 + 响应时间 + 业务码 + rows结构
        resp_json = self._assert_basic(response, tc)

        # 过滤结果验证(基于本次响应)
        if resp_json is not None:
            self._verify_filter_result(resp_json, tc, params)
            if tc.expected.get('verify_sorting'):
                self._verify_sorting(resp_json, params)

        # 扩展验证(需要再次调用接口)
        if tc.expected.get('verify_pagination_no_overlap'):
            self._verify_pagination_no_overlap(logged_in_api, params)
        if tc.expected.get('verify_filter_completeness'):
            self._verify_filter_completeness(logged_in_api, params, tc)

        logger.info(f"测试用例执行完成: {tc.case_id} - {tc.case_name}")

    def _assert_basic(self, response, tc):
        """基础断言。返回resp_json; 边界用例(allow_error)返回None, 跳过后续验证"""
        expected = tc.expected

        AssertUtils.assert_status_ok(response)
        AssertUtils.assert_response_time(response, max_seconds=10.0)

        if expected.get('allow_error'):
            try:
                resp_json = response.json()
                logger.info(
                    f"[Test] 边界测试响应: code={resp_json.get('code')}, "
                    f"total={resp_json.get('total')}"
                )
            except Exception:
                pytest.fail(f"边界测试期望返回合法JSON, 实际: {response.text[:500]}")
            return None

        resp_json = AssertUtils.assert_list_success(
            response, min_total=expected.get('min_total', 0)
        )

        max_rows = expected.get('max_rows')
        if max_rows is not None:
            actual_rows = len(resp_json.get('rows', []))
            assert actual_rows <= max_rows, (
                f"rows数量断言失败: 期望<={max_rows}, 实际={actual_rows}"
            )

        if expected.get('expect_empty_rows'):
            rows = resp_json.get('rows', [])
            assert len(rows) == 0, f"期望返回空rows, 实际返回{len(rows)}条"

        return resp_json

    def _verify_sorting(self, resp_json, params):
        """验证排序: 按字段类型选择比较方式(数字/字符串)"""
        order_by = params.get('orderByColumn')
        if not order_by:
            return

        is_asc = params.get('isAsc', 'asc').lower() == 'asc'
        rows = resp_json.get('rows', [])

        if len(rows) < 2:
            pytest.skip(f"返回数据不足2条({len(rows)}), 无法验证排序, 跳过")

        # 数字字段按数值比较, 避免"10" < "2"字典序错误
        def _to_sortable(v):
            s = str(v) if v is not None else ''
            try:
                return (0, int(s))
            except ValueError:
                return (1, s)

        values = [_to_sortable(row.get(order_by)) for row in rows]
        sorted_values = sorted(values, reverse=not is_asc)

        assert values == sorted_values, (
            f"排序验证失败: orderByColumn={order_by}, isAsc={params.get('isAsc')}, "
            f"前5个值: {values[:5]}"
        )
        logger.info(
            f"[Test] 排序验证通过: {order_by} "
            f"{'升序' if is_asc else '降序'}, 共{len(rows)}条"
        )

    def _verify_filter_result(self, resp_json, tc, params):
        """
        验证过滤结果: 每条row的对应字段都符合请求条件。
        枚举/身份证/营业执照号字段精确匹配, 其他字段包含匹配。
        """
        filter_keys = [k for k in params.keys() if k not in NON_FILTER_KEYS]
        if not filter_keys:
            return

        if tc.expected.get('allow_error') or tc.expected.get('expect_empty_rows'):
            return

        logger.info(f"[Test] 验证过滤结果, 过滤字段: {filter_keys}")
        rows = resp_json.get('rows', [])
        for row in rows:
            for key in filter_keys:
                expected_value = str(params[key])
                actual_value = str(row.get(key, ''))
                if key in EXACT_MATCH_FIELDS:
                    assert actual_value == expected_value, (
                        f"过滤验证失败(精确匹配): {key} 期望='{expected_value}', "
                        f"实际='{actual_value}'"
                    )
                else:
                    assert expected_value in actual_value, (
                        f"过滤验证失败(包含匹配): {key} 期望包含'{expected_value}', "
                        f"实际='{actual_value}'"
                    )

    def _verify_pagination_no_overlap(self, logged_in_api, params):
        """
        验证分页: 第1页和第2页的rows不应有交集。
        用row的全字段签名做重复检测。
        """
        page1 = self._call_api(logged_in_api, params).json()

        page2_params = dict(params)
        page2_params['pageNum'] = params.get('pageNum', 1) + 1
        page2 = self._call_api(logged_in_api, page2_params).json()

        rows1 = page1.get('rows', [])
        rows2 = page2.get('rows', [])

        if not rows1 or not rows2:
            pytest.skip(
                f"返回数据不足(第1页{len(rows1)}条/第2页{len(rows2)}条), 无法验证翻页不重复"
            )

        sigs1 = {_row_signature(r) for r in rows1}
        sigs2 = {_row_signature(r) for r in rows2}
        overlap = sigs1 & sigs2

        assert not overlap, (
            f"翻页数据重复: 第1页和第2页有{len(overlap)}条重复记录, "
            f"pageSize={params.get('pageSize')}"
        )
        logger.info(
            f"[Test] 翻页验证通过: 第1页{len(rows1)}条 + 第2页{len(rows2)}条, 无重复"
        )

    def _verify_filter_completeness(self, logged_in_api, params, tc):
        """
        验证过滤完整性: 接口过滤查询返回的数据, 应与全量查询后本地过滤的结果一致。
        用于发现"应该返回但没返回"的漏数据bug。
        """
        filter_keys = [k for k in params.keys() if k not in NON_FILTER_KEYS]
        if not filter_keys:
            return

        # 全量查询(保留分页参数, 扩大pageSize拉全量)
        all_params = {k: v for k, v in params.items() if k in NON_FILTER_KEYS}
        all_params['pageSize'] = COMPLETENESS_FETCH_SIZE
        all_rows = self._call_api(logged_in_api, all_params).json().get('rows', [])

        # 本地过滤
        def _match(row):
            for key in filter_keys:
                expected_value = str(params[key])
                actual_value = str(row.get(key, ''))
                if key in EXACT_MATCH_FIELDS:
                    if actual_value != expected_value:
                        return False
                else:
                    if expected_value not in actual_value:
                        return False
            return True

        expected_rows = [r for r in all_rows if _match(r)]

        # 实际过滤查询返回的rows(重新调用, 确保与基础断言那次独立)
        actual_rows = self._call_api(logged_in_api, params).json().get('rows', [])

        assert len(expected_rows) == len(actual_rows), (
            f"过滤完整性失败: 全量本地过滤得到{len(expected_rows)}条, "
            f"接口过滤查询返回{len(actual_rows)}条, 可能存在漏数据或脏数据\n"
            f"全量总数: {len(all_rows)}, 过滤字段: {filter_keys}"
        )
        logger.info(
            f"[Test] 过滤完整性验证通过: 全量本地过滤{len(expected_rows)}条 = "
            f"接口过滤查询{len(actual_rows)}条"
        )
