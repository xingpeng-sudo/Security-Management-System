FROM python:3.11-slim

LABEL maintainer="SecurityManagementSystem Test Team"
LABEL description="API Automation Test Framework"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TEST_ENV=test \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Allure命令行工具（2.27.0，2024年发布）
ARG ALLURE_VERSION=2.27.0
RUN curl -fsSL -o allure.tgz https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz \
    && tar -zxvf allure.tgz -C /opt/ \
    && ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/bin/allure \
    && rm allure.tgz \
    && allure --version

# 复制依赖文件并安装（利用Docker缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p reports/allure-results logs

# ENTRYPOINT + CMD 模式：默认跑全部测试，可传参覆盖
# 用法:
#   docker run image                          # 跑全部测试
#   docker run image -m coordination          # 只跑 coordination 模块
#   docker run image -m smoke                 # 只跑 smoke 标记
ENTRYPOINT ["pytest", "-v", "--alluredir=reports/allure-results", "--clean-alluredir"]
CMD ["testcases/"]
