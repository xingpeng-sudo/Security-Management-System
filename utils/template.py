"""
模板变量处理工具
用于处理测试数据中的动态模板变量

支持：
1. 内置变量：{{timestamp}}、{{random}}、{{phone}} 等
2. 环境变量：{{env.VAR_NAME}} 读取任意环境变量
3. 便捷别名：{{test_username}}、{{test_password}} 对应 TEST_USERNAME/TEST_PASSWORD 环境变量
4. 自定义变量：通过 register_template_var() 注册
"""
import json
import os
import re
import time

from faker import Faker

fake_zh = Faker('zh_CN')

# 模板变量注册表：变量名 -> 替换函数
_TEMPLATE_VARS = {
    'timestamp': lambda: str(int(time.time())),
    'timestamp_short': lambda: str(int(time.time()))[-6:],
    'random': lambda: fake_zh.numerify('#' * 6),
    'random_short': lambda: fake_zh.numerify('#' * 7),
    'phone': lambda: fake_zh.phone_number(),
    'name': lambda: fake_zh.name(),
    'mobile': lambda: '13' + fake_zh.numerify('#' * 9),
    'long_500': lambda: 'A' * 500,
    'test_username': lambda: os.getenv('TEST_USERNAME', ''),
    'test_password': lambda: os.getenv('TEST_PASSWORD', ''),
}

# 匹配 {{variable_name}} 或 {{env.VAR_NAME}} 模式
_TEMPLATE_PATTERN = re.compile(r'\{\{(\w+)(?:\.(\w+))?\}\}')


def register_template_var(name: str, func):
    """
    注册自定义模板变量

    Args:
        name: 变量名（不含花括号）
        func: 无参可调用对象，返回替换值

    Example:
        register_template_var('order_id', lambda: generate_order_id())
    """
    _TEMPLATE_VARS[name] = func


def _json_escape(value: str) -> str:
    """将字符串转义为安全的 JSON 字符串内容（不含外层引号）"""
    return json.dumps(value)[1:-1]


def process_template(data: dict) -> dict:
    """
    处理测试数据中的模板变量

    内置变量:
    - {{timestamp}}: 当前时间戳（完整）
    - {{timestamp_short}}: 当前时间戳后6位
    - {{random}}: 6位随机数字串
    - {{phone}}: 随机手机号
    - {{name}}: 随机中文姓名
    - {{mobile}}: 随机11位手机号(13开头)
    - {{long_500}}: 500个字符的超长字符串
    - {{test_username}}: 环境变量 TEST_USERNAME
    - {{test_password}}: 环境变量 TEST_PASSWORD
    - {{env.VAR_NAME}}: 任意环境变量

    可通过 register_template_var() 扩展自定义变量。
    """
    raw = json.dumps(data, ensure_ascii=False)

    def _replace(match):
        var_name = match.group(1)
        sub_key = match.group(2)

        # {{env.VAR_NAME}} -> 读取环境变量
        if var_name == 'env' and sub_key:
            return _json_escape(os.getenv(sub_key, match.group(0)))

        # 注册表中的变量
        if var_name in _TEMPLATE_VARS:
            return _json_escape(_TEMPLATE_VARS[var_name]())

        # 未注册的变量保持原样
        return match.group(0)

    raw = _TEMPLATE_PATTERN.sub(_replace, raw)
    return json.loads(raw)
