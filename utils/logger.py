"""
日志工具模块
基于loguru实现，支持控制台和文件双输出
延迟初始化：首次调用 init_logging() 时配置，避免导入时依赖 Config 单例状态
"""
import sys
from pathlib import Path

from loguru import logger

from config.config import config, PROJECT_ROOT

_initialized = False


def init_logging():
    """
    初始化日志配置

    幂等：多次调用只初始化一次。
    建议在 conftest.py 的 session_setup 中显式调用。
    如果未显式调用，首次使用 logger 时也会自动初始化。
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    # 移除默认handler
    logger.remove()

    # 日志目录
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(exist_ok=True)

    # 控制台输出 - 彩色格式
    # enqueue=True 保证多进程（pytest-xdist）下线程安全
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=config.log_level,
        colorize=True,
        enqueue=True
    )

    # 文件输出 - 按日期轮转
    logger.add(
        str(log_dir / "test_{time:YYYY-MM-DD}.log"),
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True
    )

    # Allure日志集成 - 纯文本格式，便于Allure附件抓取
    logger.add(
        str(log_dir / "allure_{time:YYYY-MM-DD}.log"),
        format="{message}",
        level="INFO",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=True
    )
