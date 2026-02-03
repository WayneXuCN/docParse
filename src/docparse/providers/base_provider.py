"""
服务商抽象层
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from docparse.models import APIResponse, FileType


@dataclass
class ProviderConfig:
    """
    服务商配置

    Parameters
    ----------
    api_key : str
        API 密钥
    model : str
        模型名称
    temperature : float, optional
        采样温度，默认为 0.1
    max_tokens : int, optional
        最大生成 token 数，默认为 4000
    timeout : int, optional
        请求超时时间（秒），默认为 30
    rpm : int, optional
        每分钟最大请求数 (Requests Per Minute)，默认为 1000
    tpm : int, optional
        每分钟最大 token 数 (Tokens Per Minute)，默认为 80000
    max_concurrent : int, optional
        最大并发数，None 表示自动计算
    """

    api_key: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 30
    rpm: int = 1000
    tpm: int = 80000
    max_concurrent: int | None = None


class BaseProvider(ABC):
    """
    OCR 服务商抽象基类

    所有服务商实现需要继承此类并实现抽象方法
    """

    def __init__(self, config: ProviderConfig, progress_callback=None):
        """
        初始化服务商

        Parameters
        ----------
        config : ProviderConfig
            服务商配置对象
        progress_callback : callable, optional
            进度回调函数，接收 (current, total, message) 参数
        """
        self.config = config
        self.progress_callback = progress_callback

    def _report_progress(self, current: int, total: int, message: str = "") -> None:
        """
        报告进度

        Parameters
        ----------
        current : int
            当前进度
        total : int
            总数
        message : str, optional
            进度消息
        """
        if self.progress_callback:
            self.progress_callback(current, total, message)

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def close(self) -> None:
        """关闭资源"""

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
