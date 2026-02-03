"""SiliconFlow 服务商实现."""

import base64
import io
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from pdf2image import convert_from_path

from docparse.models import APIResponse, FileType
from docparse.providers.base_provider import BaseProvider, ProviderConfig


class RateLimiter:
    """速率限制器，基于令牌桶算法."""

    def __init__(self, rpm: int, tpm: int) -> None:
        """Initialize rate limiter.

        Parameters
        ----------
        rpm : int
            每分钟最大请求数
        tpm : int
            每分钟最大 token 数

        """
        self.rpm = rpm
        self.tpm = tpm
        self.request_tokens = 0
        self.last_time = time.time()
        self.lock = threading.Lock()

    def acquire(self, estimated_tokens: int = 2000) -> bool:
        """
        获取请求许可

        Parameters
        ----------
        estimated_tokens : int, optional
            预估的 token 数量，默认为 2000

        Returns
        -------
        bool
            是否获取成功

        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_time

            # 每分钟重置
            if elapsed >= 60:
                self.request_tokens = 0
                self.last_time = current_time
                elapsed = 0

            # 计算当前可用的配额
            time_fraction = elapsed / 60
            available_tokens = max(0, self.tpm * time_fraction)

            # 检查是否超出限制
            if self.request_tokens + estimated_tokens > available_tokens:
                return False

            self.request_tokens += estimated_tokens
            return True

    def wait_for_available(self, estimated_tokens: int = 2000) -> None:
        """
        等待直到有可用配额

        Parameters
        ----------
        estimated_tokens : int, optional
            预估的 token 数量，默认为 2000

        """
        while not self.acquire(estimated_tokens):
            time.sleep(0.1)


class SiliconFlowProvider(BaseProvider):
    """
    SiliconFlow API 服务商
    """

    API_URL = "https://api.siliconflow.cn/v1/chat/completions"

    def __init__(
        self, config: ProviderConfig, progress_callback: Callable | None = None
    ) -> None:
        """
        初始化 SiliconFlow 服务商

        Parameters
        ----------
        config : ProviderConfig
            服务商配置对象
        progress_callback : callable, optional
            进度回调函数，接收 (current, total, message) 参数
        """
        super().__init__(config, progress_callback)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
        )
        # 初始化速率限制器
        self.rate_limiter = RateLimiter(config.rpm, config.tpm)
        # 计算最大并发数
        if config.max_concurrent:
            self.max_concurrent = config.max_concurrent
        else:
            # 基于 RPM 自动计算，保守估计为 RPM 的 10%
            self.max_concurrent = max(1, min(10, config.rpm // 10))

    def convert_pdf_to_images(self, pdf_path: str) -> list[bytes]:
        """
        将 PDF 转换为图片列表

        Parameters
        ----------
        pdf_path : str
            PDF 文件路径

        Returns
        -------
        list[bytes]
            图片数据列表 (PNG 格式)

        """
        images = convert_from_path(pdf_path)
        image_data = []
        for img in images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            image_data.append(img_byte_arr.getvalue())
        return image_data

    def encode_file_to_base64(self, file_path: str) -> str:
        """
        将文件编码为 base64

        Parameters
        ----------
        file_path : str
            文件路径

        Returns
        -------
        str
            base64 编码的字符串

        """
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    def encode_bytes_to_base64(self, data: bytes) -> str:
        """
        将字节数据编码为 base64

        Parameters
        ----------
        data : bytes
            字节数据

        Returns
        -------
        str
            base64 编码的字符串

        """
        return base64.b64encode(data).decode("utf-8")

    def build_data_url(self, file_path: str, mime_type: FileType) -> str:
        """
        构建 data URL

        Parameters
        ----------
        file_path : str
            文件路径
        mime_type : FileType
            MIME 类型

        Returns
        -------
        str
            data URL 字符串

        """
        file_base64 = self.encode_file_to_base64(file_path)
        return f"data:{mime_type.value};base64,{file_base64}"

    def build_data_url_from_bytes(
        self, image_data: bytes, mime_type: str = "image/png"
    ) -> str:
        """
        从字节数据构建 data URL

        Parameters
        ----------
        image_data : bytes
            图片数据
        mime_type : str, optional
            MIME 类型，默认为 "image/png"

        Returns
        -------
        str
            data URL 字符串

        """
        image_base64 = self.encode_bytes_to_base64(image_data)
        return f"data:{mime_type};base64,{image_base64}"

    def build_payload(self, data_url: str, prompt: str | None = None) -> dict:
        """
        构建请求 payload

        Parameters
        ----------
        data_url : str
            图片的 data URL
        prompt : str, optional
            自定义提示词

        Returns
        -------
        dict
            请求 payload 字典

        """
        from docparse.config import ConfigManager

        app_config = ConfigManager.get_app_config()
        text_prompt = prompt or app_config.default_prompt

        return {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

    def build_payload_with_multiple_images(
        self, data_urls: list[str], prompt: str | None = None
    ) -> dict:
        """
        构建包含多张图片的请求 payload

        Parameters
        ----------
        data_urls : list[str]
            图片的 data URL 列表
        prompt : str, optional
            自定义提示词

        Returns
        -------
        dict
            请求 payload 字典

        """
        from docparse.config import ConfigManager

        app_config = ConfigManager.get_app_config()
        text_prompt = prompt or app_config.default_prompt

        content = [{"type": "text", "text": text_prompt}]
        for data_url in data_urls:
            content.append({"type": "image_url", "image_url": {"url": data_url}})

        return {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

    def _process_single_page(
        self, page_num: int, img_data: bytes, prompt: str | None
    ) -> tuple[int, str, str | None]:
        """Process single PDF page.

        Parameters
        ----------
        page_num : int
            页码 (从 0 开始)
        img_data : bytes
            图片数据
        prompt : str, optional
            提示词

        Returns
        -------
        tuple[int, str, Optional[str]]
            (页码, 内容, 错误信息)

        """
        try:
            # 等待速率限制器
            self.rate_limiter.wait_for_available(estimated_tokens=2000)

            data_url = self.build_data_url_from_bytes(img_data)
            payload = self.build_payload(data_url, prompt)

            kwargs = {}
            if self.config.timeout is not None:
                kwargs["timeout"] = self.config.timeout

            response = self.session.post(self.API_URL, json=payload, **kwargs)

            if response.status_code == 200:
                data = response.json()
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                return (page_num, content, None)
            else:
                error_msg = response.text
                return (page_num, "", error_msg)
        except Exception as e:
            return (page_num, "", str(e))

    def process_image(
        self,
        file_path: str,
        mime_type: FileType,
        prompt: str | None = None,
    ) -> APIResponse:
        """Process image file.

        Parameters
        ----------
        file_path : str
            文件路径
        mime_type : FileType
            MIME 类型
        prompt : str, optional
            自定义提示词

        Returns
        -------
        APIResponse
            API 响应对象

        """
        try:
            # 如果是 PDF，先转换为图片，然后并行处理
            if mime_type == FileType.PDF:
                self._report_progress(0, 1, "正在转换 PDF 为图片...")

                time.sleep(0.1)  # 确保进度条显示
                images = self.convert_pdf_to_images(file_path)
                total_pages = len(images)
                self._report_progress(1, 1, f"PDF 转换完成，共 {total_pages} 页")

                self._report_progress(
                    0,
                    total_pages,
                    f"开始并行处理 {total_pages} 页 (并发数: {self.max_concurrent})...",
                )
                time.sleep(0.1)  # 确保进度条显示

                results = {}
                completed = 0

                # 使用线程池并行处理
                with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                    # 提交所有任务
                    future_to_page = {
                        executor.submit(
                            self._process_single_page,
                            idx,
                            img_data,
                            prompt,
                        ): idx
                        for idx, img_data in enumerate(images)
                    }

                    # 处理完成的任务
                    for future in as_completed(future_to_page):
                        page_num, content, error = future.result()
                        results[page_num] = (content, error)
                        completed += 1
                        self._report_progress(
                            completed,
                            total_pages,
                            f"已完成 {completed}/{total_pages} 页",
                        )

                # 检查是否有错误
                for page_num, (_, error) in results.items():
                    if error:
                        return APIResponse(
                            status_code=500,
                            error=f"第 {page_num + 1} 页处理失败: {error}",
                            raw_response=None,
                        )

                # 按顺序合并结果
                all_content = []
                for idx in range(total_pages):
                    content, _ = results[idx]
                    all_content.append(f"\n\n## 第 {idx + 1} 页\n\n{content}")

                self._report_progress(total_pages, total_pages, "处理完成")
                combined_content = "".join(all_content)
                return APIResponse(
                    status_code=200,
                    content=combined_content,
                    raw_response=None,
                )
            data_url = self.build_data_url(file_path, mime_type)
            payload = self.build_payload(data_url, prompt)

            kwargs = {}
            if self.config.timeout is not None:
                kwargs["timeout"] = self.config.timeout
            response = self.session.post(
                self.API_URL,
                json=payload,
                **kwargs,
            )

            if response.status_code == 200:
                data = response.json()
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                return APIResponse(
                    status_code=response.status_code,
                    content=content,
                    raw_response=data,
                )
            return APIResponse(
                status_code=response.status_code,
                error=response.text,
                raw_response=response.json()
                if response.headers.get("content-type") == "application/json"
                else None,
            )

        except requests.exceptions.Timeout:
            return APIResponse(status_code=408, error="请求超时")
        except requests.exceptions.RequestException as e:
            return APIResponse(status_code=500, error=f"请求异常: {e}")
        except Exception as e:
            return APIResponse(status_code=500, error=f"未知错误: {e}")

    def close(self) -> None:
        """Close session."""
        self.session.close()
