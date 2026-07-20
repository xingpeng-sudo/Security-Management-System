"""
动态测试数据工厂
统一 Faker + 时间戳等动态数据的构造逻辑，避免在各处重复拼接
"""
import time

from faker import Faker

fake_zh = Faker('zh_CN')


def make_register_data(prefix: str = "测试公司", **overrides) -> dict:
    """
    生成相关方单位注册测试数据

    所有必填字段均使用合法值，可通过 overrides 覆盖任意字段。

    Args:
        prefix: 公司名称前缀
        **overrides: 覆盖任意字段

    Returns:
        完整的注册数据字典
    """
    timestamp = str(int(time.time()))[-6:]
    # 生成18位统一社会信用代码（合法格式）
    license_no = f"91110000MA00{timestamp}X"
    data = {
        "supplierName": f"{prefix}_{timestamp}",
        "legalRepresentative": fake_zh.name(),
        "businessLicenseNo": license_no,
        "blIssuingAuthority": "北京市市场监督管理局",
        "blStartDate": "2024-01-01",
        "blEndDate": "2034-01-01",
        "nwslStartDate": "2024-01-01",
        "nwslEndDate": "2029-01-01",
        "contactsName": fake_zh.name(),
        "contactsPhone": fake_zh.phone_number(),
        "bussinessType": "short_jx",
        "isSelfAccess": "0",
    }
    data.update(overrides)
    return data
