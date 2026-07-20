"""
准入证模块 - 相关方单位API
包含：注册账号、登录接口
"""
import urllib.parse

from api.base_api import BaseAPI
from utils.logger import logger


class UnitAPI(BaseAPI):
    """
    相关方单位API类

    接口列表：
    - POST /app/xl/unit/register                相关方单位注册账号
    - POST /app/xl/unit/login/{account}/{pwd}   相关方单位登录（路径参数）
    """

    REGISTER = '/app/xl/unit/register'
    LOGIN = '/app/xl/unit/login'

    def register(self, data: dict, **kwargs):
        """
        相关方单位注册账号

        Args:
            data: 注册数据字典，必填字段：
                - supplierName: 公司名称
                - legalRepresentative: 法定代表人
                - businessLicenseNo: 营业执照号（15位注册号或18位统一社会信用代码）
                - blIssuingAuthority: 发证机关
                - blStartDate: 营业执照起始日期 (YYYY-MM-DD)
                - blEndDate: 营业执照结束日期 (YYYY-MM-DD)
                - contactsName: 联系人姓名
                - contactsPhone: 联系人电话（符合电话号格式）
                - bussinessType: 协力种类
            可选字段：
                - nwslStartDate / nwslEndDate: 安全许可证起止日期
                - isSelfAccess: 是否自主准入 (0/1)
        """
        logger.info(f"[API] 注册相关方单位: {data.get('supplierName', 'N/A')}")
        return self.post(self.REGISTER, json=data, **kwargs)

    def login(self, account: str, password: str, **kwargs):
        """
        相关方单位登录

        登录接口使用路径参数传递账号密码：
            POST /app/xl/unit/login/{account}/{password}

        account 和 password 来源于 register 接口返回的 data.account / data.password。

        Args:
            account: 注册时返回的账号（如 WX0019）
            password: 注册时返回的密码（如 tpEN4*）
        """
        # URL编码路径参数，处理密码中的特殊字符
        encoded_account = urllib.parse.quote(str(account), safe='')
        encoded_password = urllib.parse.quote(str(password), safe='')
        url = f"{self.LOGIN}/{encoded_account}/{encoded_password}"

        logger.info(f"[API] 相关方单位登录: account={account}")
        return self.post(url, **kwargs)
