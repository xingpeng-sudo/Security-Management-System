"""
API基础类
封装requests，提供统一的请求方法、响应处理和扩展钩子
"""
import json
import time

import requests
from requests import Response

from config.config import config
from utils.logger import logger


def _is_unrecoverable_connection_error(exc: requests.exceptions.ConnectionError) -> bool:
    """
    判断连接错误是否不可重试

    不可重试：DNS解析失败、连接被拒绝
    可重试：临时网络抖动、连接被重置、服务暂时不可达
    """
    error_str = str(exc)
    if 'getaddrinfo failed' in error_str or 'NameResolutionError' in error_str:
        return True
    if 'ConnectionRefusedError' in error_str or 'Connection refused' in error_str:
        return True
    return False


# 服务端错误状态码，可重试
_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class BaseAPI:
    """
    API基础类
    所有API模块类继承此类，提供：
    1. 统一的请求方法（GET/POST/PUT/DELETE/UPLOAD）
    2. 自动携带认证信息
    3. 统一的日志记录
    4. 请求重试机制（网络异常 + 5xx服务端错误）
    5. 请求/响应钩子（子类可重写实现签名、解密等）
    """

    def __init__(self):
        self.base_url = config.base_url
        self.timeout = config.timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def set_token(self, token: str):
        """设置认证Token"""
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def clear_token(self):
        """清除认证Token"""
        self.session.headers.pop('Authorization', None)

    # ---- 钩子方法（子类可重写） ----

    def _before_request(self, method: str, url: str, **kwargs) -> tuple:
        """
        请求前钩子

        子类可重写以实现：请求签名、时间戳注入、参数预处理等。

        Returns:
            (url, kwargs) 元组，修改后传给实际请求
        """
        return url, kwargs

    def _after_response(self, response: Response) -> Response:
        """
        响应后钩子

        子类可重写以实现：响应解密、状态码特殊处理等。
        """
        return response

    # ---- 核心请求方法 ----

    def _request(self, method: str, url: str, retry_times: int = None, **kwargs) -> Response:
        """
        统一请求方法（含重试）

        retry_times 表示总尝试次数（至少 1 次）。

        Args:
            method: 请求方法 GET/POST/PUT/DELETE
            url: 请求路径（相对路径，自动拼接base_url）
            retry_times: 总尝试次数，默认使用配置值；0 也会至少请求 1 次
            **kwargs: requests参数（json/params/files/data等）
        """
        if retry_times is None:
            retry_times = config.retry_times
        max_attempts = max(retry_times, 1)  # 至少请求 1 次

        full_url = f"{self.base_url}{url}"
        kwargs.setdefault('timeout', self.timeout)

        # 文件上传：移除Content-Type，让requests自动设置multipart boundary
        is_upload = 'files' in kwargs
        if is_upload:
            headers = dict(self.session.headers)
            headers.pop('Content-Type', None)
            kwargs['headers'] = headers

        # 请求前钩子
        full_url, kwargs = self._before_request(method, full_url, **kwargs)

        action = 'Upload' if is_upload else 'Request'
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"[{action}] {method} {full_url} | Attempt: {attempt}/{max_attempts}"
                )
                if 'json' in kwargs:
                    logger.debug(f"[Request Body] {json.dumps(kwargs['json'], ensure_ascii=False)}")
                if 'params' in kwargs:
                    logger.debug(f"[Request Params] {kwargs['params']}")

                response = self.session.request(method, full_url, **kwargs)

                logger.info(
                    f"[Response] {response.status_code} | "
                    f"Time: {response.elapsed.total_seconds():.3f}s"
                )
                logger.debug(f"[Response Body] {response.text[:2000]}")

                # 5xx服务端错误：可重试
                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < max_attempts:
                    wait = 2 ** attempt
                    logger.warning(
                        f"[Server Error {response.status_code}] {method} {full_url} | "
                        f"Retry in {wait}s"
                    )
                    time.sleep(wait)
                    continue

                # 响应后钩子
                return self._after_response(response)

            except requests.exceptions.ConnectionError as e:
                if _is_unrecoverable_connection_error(e):
                    logger.error(f"[{action} Failed - Unrecoverable] {method} {full_url} | Error: {e}")
                    raise
                last_exception = e
                logger.warning(
                    f"[{action} Failed - Retriable] {method} {full_url} | "
                    f"Attempt: {attempt}/{max_attempts} | Error: {e}"
                )

            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    f"[{action} Failed - Timeout] {method} {full_url} | "
                    f"Attempt: {attempt}/{max_attempts} | Error: {e}"
                )

            except requests.exceptions.RequestException as e:
                logger.error(f"[{action} Failed] {method} {full_url} | Error: {e}")
                raise

            # 重试前等待（指数退避）
            if attempt < max_attempts:
                time.sleep(2 ** attempt)

        # 重试耗尽
        if last_exception:
            raise last_exception
        raise requests.exceptions.RetryError(f"请求重试耗尽: {method} {full_url}")

    def get(self, url: str, **kwargs) -> Response:
        return self._request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        return self._request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        return self._request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        return self._request('DELETE', url, **kwargs)

    def upload(self, url: str, files: dict, data: dict = None, **kwargs) -> Response:
        """
        文件上传

        Args:
            url: 请求路径
            files: 文件字典，如 {'file': ('name.txt', open('name.txt', 'rb'), 'text/plain')}
            data: 附带的表单数据
            **kwargs: 其他requests参数
        """
        upload_kwargs = {'files': files}
        if data is not None:
            upload_kwargs['data'] = data
        upload_kwargs.update(kwargs)
        return self._request('POST', url, **upload_kwargs)
