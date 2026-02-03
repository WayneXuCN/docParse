"""
OpenAI 服务商实现
"""

import base64

import requests

from docparse.models import APIResponse, FileType
from docparse.providers.base_provider import BaseProvider, ProviderConfig


class OpenAIProvider(BaseProvider):
    """
    OpenAI API 服务商
    """

    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        config: ProviderConfig,
        base_url: str | None = None,
        progress_callback=None,
    ):
        """
        初始化 OpenAI 服务商

        Parameters
        ----------
        config : ProviderConfig
            服务商配置对象
        base_url : str, optional
            自定义 API 基础 URL（用于 OpenAI 兼容的 API）
        progress_callback : callable, optional
            进度回调函数，接收 (current, total, message) 参数
        """
        super().__init__(config, progress_callback)
        self.base_url = base_url or self.API_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
        )

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

    def process_image(
        self,
        file_path: str,
        mime_type: FileType,
        prompt: str | None = None,
    ) -> APIResponse:
        """
        处理图片文件

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
            data_url = self.build_data_url(file_path, mime_type)
            payload = self.build_payload(data_url, prompt)

            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.config.timeout,
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
            else:
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
            return APIResponse(status_code=500, error=f"请求异常: {str(e)}")
        except Exception as e:
            return APIResponse(status_code=500, error=f"未知错误: {str(e)}")

    def close(self) -> None:
        """关闭会话"""
        self.session.close()
