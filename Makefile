.PHONY: help install test smoke regression mod report clean docker-up docker-test lint

PYTEST ?= pytest
ALLURE ?= allure

help:
	@echo "可用命令:"
	@echo "  make install      - 安装依赖"
	@echo "  make test         - 运行全部测试"
	@echo "  make smoke        - 运行冒烟测试 (P0)"
	@echo "  make regression   - 运行回归测试"
	@echo "  make mod MODULE=x - 运行指定模块"
	@echo "  make report       - 启动 Allure 报告服务"
	@echo "  make clean        - 清理报告和缓存"
	@echo "  make docker-up    - 启动 docker-compose"
	@echo "  make docker-test  - 在 Docker 中运行测试"
	@echo "  make lint         - 代码检查 (flake8)"

install:
	pip install -r requirements.txt

test:
	$(PYTEST) -v --alluredir=reports/allure-results --clean-alluredir

smoke:
	$(PYTEST) -v -m p0 --alluredir=reports/allure-results --clean-alluredir

regression:
	$(PYTEST) -v -m regression --alluredir=reports/allure-results --clean-alluredir

mod:
	@if [ -z "$(MODULE)" ]; then echo "用法: make mod MODULE=user_center"; exit 1; fi
	$(PYTEST) -v -m $(MODULE) --alluredir=reports/allure-results --clean-alluredir

report:
	$(ALLURE) serve reports/allure-results

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['reports/allure-results', 'reports/allure-report', '.pytest_cache']]; [p.unlink() for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()] or [d.rmdir() for d in pathlib.Path('.').rglob('__pycache__')]"

docker-up:
	docker-compose -f docker/docker-compose.yml up --build

docker-test:
	docker-compose -f docker/docker-compose.yml run --rm api-test

lint:
	flake8 api utils testcases --max-line-length=120 --exclude=__pycache__,.venv
