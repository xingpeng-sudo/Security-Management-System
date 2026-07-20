"""
数据加载工具
支持从JSON文件加载测试数据，支持 defaults 继承
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from config.config import PROJECT_ROOT
from utils.logger import logger


class DataLoader:
    """测试数据加载器"""

    TESTDATA_DIR = PROJECT_ROOT / 'testdata'

    @classmethod
    def load_json(cls, file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件

        Args:
            file_path: JSON文件路径（相对于testdata目录）

        Returns:
            解析后的字典
        """
        full_path = cls.TESTDATA_DIR / file_path
        logger.debug(f"[DataLoader] 加载JSON: {full_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def load_test_cases(cls, data: Any = None, file_path: str = None) -> List[Dict[str, Any]]:
        """
        加载测试用例数据

        Args:
            data: 已加载的JSON数据（优先使用，避免重复读文件）
            file_path: 数据文件路径（相对于testdata目录，data为None时使用）

        Returns:
            测试用例列表
        """
        if data is None:
            if file_path is None:
                raise ValueError("data 和 file_path 至少提供一个")
            data = cls.load_json(file_path)

        # 如果数据是字典且包含test_cases键，返回该列表
        if isinstance(data, dict) and 'test_cases' in data:
            return data['test_cases']

        # 如果数据本身就是列表
        if isinstance(data, list):
            return data

        return [data]


# 便捷函数（避免到处实例化）
load_json = DataLoader.load_json
load_test_cases = DataLoader.load_test_cases
