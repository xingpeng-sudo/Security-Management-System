"""
配置管理模块
支持多环境配置，通过.env切换环境，支持 CFG_ 前缀环境变量自动映射
"""
import os
import threading
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# 项目根目录（所有路径基于此解析）
PROJECT_ROOT = Path(__file__).parent.parent


class Config:
    """配置管理类（线程安全单例）"""

    _instance: Optional['Config'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._config_data: dict = {}
        self._load_config()
        self._initialized = True

    def _load_config(self):
        """加载配置文件"""
        load_dotenv(PROJECT_ROOT / '.env')

        self.env = os.getenv('TEST_ENV', 'test')

        config_file = Path(__file__).parent / f'{self.env}.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            self._config_data = {}

        self._override_from_env()

    def _override_from_env(self):
        """
        从环境变量覆盖配置

        1. 固定映射（向后兼容）: BASE_URL → base_url, TIMEOUT → timeout, LOG_LEVEL → log_level
        2. CFG_ 前缀自动映射: CFG_DATABASE__HOST → database.host
           双下划线表示嵌套层级，如 CFG_DB__HOST → db.host
        """
        # 固定映射
        env_mappings = {
            'BASE_URL': 'base_url',
            'TIMEOUT': 'timeout',
            'LOG_LEVEL': 'log_level',
        }
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                self._set_nested(config_key, env_value)

        # CFG_ 前缀自动映射
        for key, value in os.environ.items():
            if key.startswith('CFG_') and key not in env_mappings:
                # CFG_DATABASE__HOST → database.host
                config_key = key[4:].lower().replace('__', '.')
                self._set_nested(config_key, value)

    def _set_nested(self, key: str, value: Any):
        """
        设置嵌套配置值

        注意：环境变量值始终保持字符串类型，不做隐式类型转换。
        类型转换由调用方根据 yaml 中的 schema 自行处理，
        避免 '123' 被静默转成 int 这种隐性 bug。
        """
        keys = key.split('.')
        data = self._config_data
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持嵌套key，如: database.host"""
        keys = key.split('.')
        data = self._config_data
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return data

    @classmethod
    def reset(cls):
        """重置单例（用于测试或环境切换后重新加载）"""
        with cls._lock:
            cls._instance = None

    def reload(self):
        """重新加载配置"""
        self._load_config()

    @property
    def base_url(self) -> str:
        return str(self.get('base_url', 'http://localhost:8080'))

    @property
    def timeout(self) -> float:
        return float(self.get('timeout', 30))

    @property
    def log_level(self) -> str:
        return str(self.get('log_level', 'INFO'))

    @property
    def retry_times(self) -> int:
        return int(self.get('retry_times', 3))


# 全局配置实例
config = Config()
