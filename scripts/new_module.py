#!/usr/bin/env python3
"""
模块脚手架生成器

用法:
    python scripts/new_module.py <module_name>

示例:
    python scripts/new_module.py user_center

会自动创建:
    - api/modules/<name>/<name>_api.py   API封装骨架
    - testcases/modules/<name>/conftest.py  模块fixture
    - testdata/<name>/.gitkeep           测试数据目录
    - 并在 pytest.ini 中添加 marker（需手动确认）
"""
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def create_module(name: str):
    """创建新模块的目录结构和骨架文件"""
    # 目录列表
    dirs = [
        PROJECT_ROOT / f'api/modules/{name}',
        PROJECT_ROOT / f'testcases/modules/{name}',
        PROJECT_ROOT / f'testdata/{name}',
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        init_file = d / '__init__.py'
        if not init_file.exists():
            init_file.write_text(f'# {name}模块\n', encoding='utf-8')
        print(f"[OK] 目录已就绪: {d.relative_to(PROJECT_ROOT)}")

    # API 骨架
    api_file = PROJECT_ROOT / f'api/modules/{name}/{name}_api.py'
    if not api_file.exists():
        class_name = ''.join(word.capitalize() for word in name.split('_')) + 'API'
        api_file.write_text(f'''"""
{name}模块API
"""
from api.base_api import BaseAPI


class {class_name}(BaseAPI):
    """{''.join(word.capitalize() for word in name.split('_'))} API类"""

    # 在此定义接口路径常量和方法
    # EXAMPLE_ENDPOINT = '/api/{name}/example'

    # def example(self, data: dict, **kwargs):
    #     """示例接口"""
    #     return self.post(self.EXAMPLE_ENDPOINT, json=data, **kwargs)
''', encoding='utf-8')
        print(f"[OK] API骨架已创建: {api_file.relative_to(PROJECT_ROOT)}")
    else:
        print(f"[SKIP] API文件已存在: {api_file.relative_to(PROJECT_ROOT)}")

    # conftest 骨架
    conftest_file = PROJECT_ROOT / f'testcases/modules/{name}/conftest.py'
    if not conftest_file.exists():
        class_name = ''.join(word.capitalize() for word in name.split('_')) + 'API'
        conftest_file.write_text(f'''"""
{name}模块 - conftest.py
只放本模块的fixtures
"""
import pytest

from api.modules.{name}.{name}_api import {class_name}


@pytest.fixture(scope="session")
def {name}_api():
    """{name} API实例"""
    return {class_name}()
''', encoding='utf-8')
        print(f"[OK] conftest已创建: {conftest_file.relative_to(PROJECT_ROOT)}")
    else:
        print(f"[SKIP] conftest已存在: {conftest_file.relative_to(PROJECT_ROOT)}")

    # testdata 目录占位
    gitkeep = PROJECT_ROOT / f'testdata/{name}/.gitkeep'
    gitkeep.touch(exist_ok=True)

    # 提示
    print(f"\n[!] 别忘了在 pytest.ini 中添加 marker:")
    print(f"    {name}: {name}模块")
    print(f"\n[DONE] 模块 '{name}' 创建完成！")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python scripts/new_module.py <module_name>")
        print("示例: python scripts/new_module.py user_center")
        sys.exit(1)

    module_name = sys.argv[1]
    if not module_name.replace('_', '').isalnum():
        print(f"[ERROR] 模块名 '{module_name}' 不合法，只允许字母、数字和下划线")
        sys.exit(1)

    create_module(module_name)
