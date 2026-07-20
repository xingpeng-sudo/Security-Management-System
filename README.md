# SecurityManagementSystem - API自动化测试框架

## 技术栈
- Python 3.11+ / pytest / requests / Allure / Faker / loguru / Docker / GitHub Actions

## 项目结构
```
SecurityManagementSystem/
├── api/                        # API接口封装层
│   ├── base_api.py            # 基础API类（统一请求/智能重试/钩子扩展/文件上传）
│   └── modules/coordination/
│       └── unit_api.py        # 相关方单位API（注册/登录/材料管理）
├── config/                     # 配置管理
│   ├── config.py              # 多环境配置类（线程安全单例/CFG_前缀自动映射/支持重置）
│   ├── dev.yaml / test.yaml / prod.yaml
├── testcases/                 # 测试用例
│   └── modules/coordination/
│       ├── conftest.py             # 模块fixture
│       ├── test_unit_register.py   # 注册测试（12组参数化）
│       ├── test_unit_login.py      # 登录异常测试（4组参数化）
│       └── test_flow.py            # 业务流程测试（注册->登录端到端）
├── testdata/coordination/     # 测试数据（JSON，支持defaults继承）
├── utils/                     # 工具类
│   ├── logger.py              # loguru日志（延迟初始化/控制台+文件双输出）
│   ├── data_loader.py         # JSON数据加载器
│   ├── assertions.py          # 业务断言工具（统一断言入口/msg_mode可配置）
│   ├── template.py            # 模板变量处理（正则匹配/环境变量/可扩展注册表）
│   ├── parametrize.py         # 参数化封装（消灭重复模板代码/TestCase数据类）
│   ├── data_factory.py        # 动态数据工厂（统一Faker+时间戳构造）
│   └── attachments.py         # Allure附件工具
├── scripts/
│   └── new_module.py          # 模块脚手架生成器
├── reports/allure-results/    # Allure报告
├── logs/                      # 日志
├── docker/                    # Docker支持
└── .github/workflows/         # CI/CD
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入实际的 BASE_URL

# 3. 运行测试
pytest                                    # 全部
pytest -m coordination                    # 指定模块
pytest -n auto                            # 并行执行（需先 pip install pytest-xdist）
pytest --alluredir=reports/allure-results # 生成Allure报告
allure serve reports/allure-results       # 查看报告

# 4. Docker运行
docker-compose -f docker/docker-compose.yml up --build
```

## 新增模块

```bash
# 一键生成模块骨架
python scripts/new_module.py user_center

# 自动创建:
#   api/modules/user_center/user_center_api.py
#   testcases/modules/user_center/conftest.py
#   testdata/user_center/

# 别忘了在 pytest.ini 中添加 marker
```

## 编写测试用例

### 参数化测试（推荐）

```python
import allure
import pytest
from utils.parametrize import load_parametrize
from utils.assertions import AssertUtils
from utils.template import process_template

@allure.feature("用户中心")
@allure.story("登录")
@pytest.mark.user_center
class TestUserLogin:
    @load_parametrize('user_center/login.json')  # 一行搞定参数化
    def test_login(self, user_center_api, tc):
        data = process_template(tc.data)
        response = user_center_api.login(data=data)
        AssertUtils.assert_by_expected(response, tc.expected)
```

### 业务流程测试

```python
from utils.data_factory import make_register_data

def test_flow(self, user_center_api):
    # 用工厂方法构造动态数据，避免手写Faker
    register_data = make_register_data(prefix="流程测试")
    response = user_center_api.register(data=register_data)
    AssertUtils.assert_business_success(response)
```

## 配置管理

### 多环境切换

```bash
# .env 文件
TEST_ENV=test          # 切换环境: dev / test / prod
BASE_URL=http://...    # 覆盖yaml中的base_url
```

### CFG_ 前缀自动映射

任何配置项都可通过环境变量覆盖，无需改代码：

```bash
# 双下划线表示嵌套层级
CFG_DATABASE__HOST=localhost    -> config.get('database.host')
CFG_DATABASE__PORT=3306         -> config.get('database.port')
CFG_REDIS__HOST=127.0.0.1      -> config.get('redis.host')
```

### API钩子扩展

子类可重写 `_before_request` / `_after_response` 实现签名、解密等：

```python
class SignedAPI(BaseAPI):
    def _before_request(self, method, url, **kwargs):
        # 添加请求签名
        sign = calculate_sign(kwargs.get('json', {}))
        kwargs.setdefault('headers', {})
        kwargs['headers']['X-Sign'] = sign
        return url, kwargs
```

## 测试数据格式

JSON 文件支持 `defaults` 继承，减少重复：

```json
{
  "defaults": {
    "expected": {"http_status": 200, "code": 500, "msg_contains": "参数错误"}
  },
  "test_cases": [
    {
      "case_id": "TC_001",
      "case_name": "缺少必填字段",
      "data": {...}
      // expected 为空时自动继承 defaults
    },
    {
      "case_id": "TC_002",
      "case_name": "正常场景",
      "data": {...},
      "expected": {"code": 0, "msg_contains": "成功"}  // 覆盖 defaults
    }
  ]
}
```

## 模板变量

测试数据 JSON 中支持 `{{变量名}}` 模板语法：

| 变量 | 说明 |
|------|------|
| `{{timestamp}}` | 当前时间戳 |
| `{{timestamp_short}}` | 当前时间戳后6位 |
| `{{random}}` | 6位随机数字 |
| `{{phone}}` | 随机手机号 |
| `{{long_500}}` | 500字符超长串 |
| `{{test_username}}` | 环境变量 TEST_USERNAME |
| `{{test_password}}` | 环境变量 TEST_PASSWORD |
| `{{env.VAR_NAME}}` | 任意环境变量 |

自定义变量：

```python
from utils.template import register_template_var
register_template_var('order_id', lambda: generate_order_id())
```

## 已覆盖的测试场景

### 相关方单位注册 (12)
- TC_REG_001~002: 正常注册（完整信息/15位营业执照号）
- TC_REG_003~011: 异常注册（缺字段/无效电话/执照长度不合法/空值/缺联系人）
- TC_REG_012: 安全测试（SQL注入）

### 相关方单位登录异常 (4)
- TC_LOGIN_002: 错误密码
- TC_LOGIN_003: 不存在账号
- TC_LOGIN_004: 空密码
- TC_LOGIN_005: 空账号

### 业务流程 (1)
- 注册->登录 完整链路（含凭据验证、accesstoken验证）

## 待确认事项
- ⚠️ BASE_URL 需替换为实际测试环境地址
- ⚠️ 登录接口参数名待确认（当前 username/password 占位）
- ⚠️ 9项材料接口请求体结构待确认
- ⚠️ 重复注册预期行为待确认
