"""
安全管理平台PC端 - API模块
包含：登录、相关方企业列表、人力资源库、企业黑名单、人员黑名单

注意：
- 登录使用表单提交(application/x-www-form-urlencoded)，通过Session Cookie认证
- 列表接口均为POST(非GET)，参数通过query string传递
"""
from api.base_api import BaseAPI
from utils.logger import logger


class SafetyAPI(BaseAPI):
    """
    安全管理平台PC端API类

    接口列表：
    - POST /aqserver/api/login              PC端登录(表单提交)
    - POST /aqserver/zr/zrSupplier/list     相关方企业列表
    - POST /aqserver/xl/userinfo/list       相关方人力资源库
    - POST /aqserver/zr/debarSupplier/list  相关方企业黑名单
    - POST /aqserver/zr/debarEmp/list       人员黑名单
    """

    LOGIN = '/aqserver/api/login'
    SUPPLIER_LIST = '/aqserver/zr/zrSupplier/list'
    USERINFO_LIST = '/aqserver/xl/userinfo/list'
    DEBAR_SUPPLIER_LIST = '/aqserver/zr/debarSupplier/list'
    DEBAR_EMP_LIST = '/aqserver/zr/debarEmp/list'

    def login(self, username: str, password: str, remember_me=None, **kwargs):
        """
        PC端登录

        使用表单提交(application/x-www-form-urlencoded)。
        登录成功后服务器返回JSESSIONID Cookie，Session自动维护认证状态。

        Args:
            username: 用户名（必填）
            password: 密码（必填）
            remember_me: 记住我（非必填，boolean）
        """
        payload = {
            'username': username,
            'password': password,
        }
        if remember_me is not None:
            payload['rememberMe'] = str(remember_me).lower()

        logger.info(f"[API] PC端登录: username={username}")
        # 表单提交，覆盖session默认的application/json
        response = self.post(
            self.LOGIN,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            **kwargs
        )

        # 登录成功后Session会自动保存Cookie(JSESSIONID)，无需手动设置token
        try:
            resp_json = response.json()
            if resp_json.get('code') == 0:
                logger.info(f"[API] 登录成功，Session Cookie已自动保存")
            else:
                logger.warning(f"[API] 登录可能失败: code={resp_json.get('code')}, msg={resp_json.get('msg')}")
        except Exception as e:
            logger.warning(f"[API] 解析登录响应失败: {e}")

        return response

    def get_supplier_list(self, **kwargs):
        """
        相关方企业列表（POST请求）

        Args:
            **kwargs: 查询参数，如 pageNum, pageSize, supplierName, businessLicenseNo 等
        """
        logger.info(f"[API] 查询相关方企业列表: {kwargs}")
        return self.post(self.SUPPLIER_LIST, params=kwargs)

    def get_userinfo_list(self, **kwargs):
        """
        相关方人力资源库（POST请求）

        Args:
            **kwargs: 查询参数，如 pageNum, pageSize, cooperaDept, userName 等
        """
        logger.info(f"[API] 查询相关方人力资源库: {kwargs}")
        return self.post(self.USERINFO_LIST, params=kwargs)

    def get_debar_supplier_list(self, **kwargs):
        """
        相关方企业黑名单（POST请求）

        Args:
            **kwargs: 查询参数，如 pageNum, pageSize, supplierName, supplierNo 等
        """
        logger.info(f"[API] 查询相关方企业黑名单: {kwargs}")
        return self.post(self.DEBAR_SUPPLIER_LIST, params=kwargs)

    def get_debar_emp_list(self, **kwargs):
        """
        人员黑名单（POST请求）

        Args:
            **kwargs: 查询参数，如 pageNum, pageSize, empName, idcardNo 等
        """
        logger.info(f"[API] 查询人员黑名单: {kwargs}")
        return self.post(self.DEBAR_EMP_LIST, params=kwargs)
