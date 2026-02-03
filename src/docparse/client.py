"""
API 客户端模块
"""

from docparse.config import ConfigManager
from docparse.models import APIResponse, FileType
from docparse.providers import OpenAIProvider, SiliconFlowProvider
from docparse.providers.base_provider import ProviderConfig as BaseProviderConfig


class OCRClient:
    """
    OCR 客户端

    提供统一的接口调用不同的 OCR 服务商
    """

    def __init__(
        self,
        provider: str = "siliconflow",
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        progress_callback=None,
    ):
        """
        初始化客户端

        Parameters
        ----------
        provider : str, optional
            服务商名称，可选 "siliconflow" 或 "openai"，默认为 "siliconflow"
        api_key : str, optional
            API 密钥
        model : str, optional
            模型名称
        base_url : str, optional
            API 基础 URL（主要用于 OpenAI 兼容的 API）
        timeout : int, optional
            请求超时时间（秒）
        progress_callback : callable, optional
            进度回调函数，接收 (current, total, message) 参数

        Raises
        ------
        ValueError
            当服务商不被支持时抛出
        """
        provider_config = ConfigManager.get_provider_config(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=timeout,
        )

        # Convert config.ProviderConfig to base_provider.ProviderConfig
        base_provider_config = BaseProviderConfig(
            api_key=provider_config.api_key,
            model=provider_config.model,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
            timeout=provider_config.timeout if provider_config.timeout is not None else 30,
            rpm=provider_config.rpm,
            tpm=provider_config.tpm,
            max_concurrent=provider_config.max_concurrent,
        )

        if provider == "siliconflow":
            self.provider = SiliconFlowProvider(base_provider_config, progress_callback)
        elif provider == "openai":
            self.provider = OpenAIProvider(
                base_provider_config, base_url=base_url, progress_callback=progress_callback
            )
        else:
            raise ValueError(
                f"不支持的服务商: {provider}支持的服务商: siliconflow, openai"
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
        return self.provider.encode_file_to_base64(file_path)

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
        return self.provider.build_data_url(file_path, mime_type)

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
        return self.provider.build_payload(data_url, prompt)

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
        return self.provider.process_image(file_path, mime_type, prompt)

    def close(self) -> None:
        """关闭资源"""
        self.provider.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
