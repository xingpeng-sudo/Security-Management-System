"""
全局conftest.py
只放公共fixtures和钩子，不放任何具体业务模块的fixture
"""
import pathlib
import sys

import pytest
import allure

from config.config import config
from utils.logger import init_logging, logger


# ---- 日志初始化（最先执行） ----

init_logging()


# ---- 公共 fixtures ----

@pytest.fixture(scope="session", autouse=True)
def session_setup():
    """
    测试会话初始化
    自动执行：设置全局环境 + 写入Allure环境信息
    """
    # 写入Allure环境信息
    allure_results_dir = pathlib.Path('reports/allure-results')
    allure_results_dir.mkdir(parents=True, exist_ok=True)
    env_file = allure_results_dir / 'environment.properties'
    env_file.write_text(
        f"Environment={config.env}\n"
        f"Base.URL={config.base_url}\n"
        f"Python.Version={sys.version}\n",
        encoding='utf-8'
    )

    logger.info("=" * 60)
    logger.info(f"测试会话开始 | 环境: {config.env} | URL: {config.base_url}")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("测试会话结束")
    logger.info("=" * 60)


# ---- pytest 钩子 ----

@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest钩子：测试失败时自动记录详细信息到Allure报告

    使用 hookimpl(wrapper=True)（pytest 8.x+ 推荐写法）。
    """
    report = yield

    if report.when == 'call' and report.failed:
        logger.error(f"测试失败: {item.nodeid}")
        logger.error(f"失败原因: {report.longrepr}")

        allure.attach(
            str(report.longrepr),
            name="失败详情",
            attachment_type=allure.attachment_type.TEXT
        )

    return report
