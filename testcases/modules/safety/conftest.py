"""
安全管理平台PC端模块 - conftest.py
只放本模块的fixtures
"""
import pytest

from api.modules.safety.safety_api import SafetyAPI
from utils.logger import logger


@pytest.fixture(scope="session")
def safety_api():
    """
    安全管理平台API实例（未登录）
    session级别，整个测试会话共享
    """
    return SafetyAPI()


@pytest.fixture(scope="session")
def logged_in_api():
    """
    已登录的安全管理平台API实例
    session级别，先登录admin，再返回已认证的api实例供列表测试用
    """
    api = SafetyAPI()
    logger.info("[Fixture] 开始执行PC端登录: admin")
    response = api.login(username='admin', password='adminAq123', remember_me=False)
    logger.info(f"[Fixture] 登录响应状态码: {response.status_code}")
    return api
