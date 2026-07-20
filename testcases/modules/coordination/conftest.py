"""
协力安全管理模块 - conftest.py
只放本模块的fixtures
"""
import pytest

from api.modules.coordination.unit_api import UnitAPI


@pytest.fixture(scope="session")
def unit_api():
    """
    相关方单位API实例
    session级别，整个测试会话共享
    """
    return UnitAPI()
