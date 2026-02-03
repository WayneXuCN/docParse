"""
配置管理模块
"""

import contextlib
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def get_config_dir() -> Path:
    """
    获取配置目录路径

    Returns
    -------
    Path
        配置目录路径
        - macOS/Linux: ~/.config/docparse/
        - Windows: %APPDATA%\\docparse\\
    """
    if os.name == "nt":
        config_dir = (
            Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            / "docparse"
        )
    else:
        config_dir = Path.home() / ".config" / "docparse"

    config_dir.mkdir(parents=True, exist_ok=True)

    # 自动创建 .env.example 示例文件
    env_example = config_dir / ".env.example"
    if not env_example.exists():
        env_example.write_text(
            "# SiliconFlow API 配置\n"
            "SILICONFLOW_API_KEY=your_siliconflow_api_key_here\n"
            "SILICONFLOW_MODEL=PaddlePaddle/PaddleOCR-VL-1.5\n"
            "# RPM: 每分钟最大请求数 (Requests Per Minute)\n"
            "# SILICONFLOW_RPM=1000\n"
            "# TPM: 每分钟最大 token 数 (Tokens Per Minute)\n"
            "# SILICONFLOW_TPM=80000\n"
            "# 最大并发数，留空或注释掉表示自动根据 RPM 计算\n"
            "# SILICONFLOW_MAX_CONCURRENT=10\n"
            "\n"
            "# OpenAI API 配置\n"
            "OPENAI_API_KEY=your_openai_api_key_here\n"
            "OPENAI_MODEL=gpt-4o\n"
            "OPENAI_BASE_URL=https://api.openai.com/v1\n"
            "# OPENAI_RPM=1000\n"
            "# OPENAI_TPM=80000\n"
            "# OPENAI_MAX_CONCURRENT=10\n"
            "\n"
            "# 应用配置（可选）\n"
            "OUTPUT_DIR=output\n"
            "# 请求超时时间（秒），留空或注释掉表示无限制\n"
            "# REQUEST_TIMEOUT=120\n"
        )

    return config_dir


def get_config_file() -> Path:
    """
    获取配置文件路径

    Returns
    -------
    Path
        配置文件路径
    """
    return get_config_dir() / "config"


@dataclass
class AppConfig:
    """
    应用程序配置

    Parameters
    ----------
    output_dir : str, optional
        输出目录，默认为 "output"
    supported_extensions : list, optional
        支持的文件扩展名列表
    default_prompt : str, optional
        默认提示词
    """

    output_dir: str = "output"
    supported_extensions: list[str] | None = None
    default_prompt: str = (
        "请提取这个文档中的所有文本内容，包括表格、标题、正文等，"
        "并以 Markdown 格式输出保持原文档的结构和格式"
    )

    def __post_init__(self):
        """初始化后处理"""
        if self.supported_extensions is None:
            self.supported_extensions = [
                ".pdf",
                ".png",
                ".jpg",
                ".jpeg",
                ".bmp",
                ".tif",
                ".tiff",
            ]

    @property
    def output_path(self) -> Path:
        """
        获取输出目录的 Path 对象

        Returns
        -------
        Path
            输出目录路径
        """
        return Path(self.output_dir)

    def ensure_output_dir(self) -> Path:
        """
        确保输出目录存在

        Returns
        -------
        Path
            输出目录路径
        """
        self.output_path.mkdir(parents=True, exist_ok=True)
        return self.output_path


@dataclass
class ProviderConfig:
    """
    服务商配置

    Parameters
    ----------
    provider : str, optional
        服务商名称，可选 "siliconflow" 或 "openai"，默认为 "siliconflow"
    api_key : str, optional
        API 密钥
    model : str, optional
        模型名称
    base_url : str, optional
        API 基础 URL（用于 OpenAI 兼容的 API）
    temperature : float, optional
        采样温度，默认为 0.1
    max_tokens : int, optional
        最大生成 token 数，默认为 4000
    timeout : int, optional
        请求超时时间（秒），默认为 None（无限制）
    """

    provider: str = "siliconflow"
    api_key: str = ""
    model: str = ""
    base_url: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int | None = None
    rpm: int = 1000  # 每分钟最大请求数 (Requests Per Minute)
    tpm: int = 80000  # 每分钟最大 token 数 (Tokens Per Minute)
    max_concurrent: int | None = None  # 最大并发数，None 表示自动计算

    def __post_init__(self):
        """初始化后处理，从配置文件和环境变量读取配置

        优先级：
        1. 命令行参数（通过 __init__ 传入）
        2. ~/.config/docparse/config
        3. 项目根目录 .env
        4. 系统环境变量
        5. 默认值
        """
        # 加载配置文件（优先级：~/.config/docparse/config > 项目根目录 .env）
        config_file = get_config_file()
        env_files = []

        if config_file.exists():
            env_files.append(str(config_file))

        # 检查项目根目录的 .env 文件
        project_root = Path.cwd()
        project_env = project_root / ".env"
        if project_env.exists():
            # 如果 config_file 也存在，先加载 config（优先级更高）
            # load_dotenv 会覆盖已存在的环境变量，所以需要按优先级反向加载
            pass

        # 按优先级加载：先加载低优先级的，后加载高优先级的
        # 项目根目录 .env 优先级低于 ~/.config/docparse/config
        if project_env.exists():
            env_files.insert(0, str(project_env))

        # 从低优先级到高优先级依次加载，后面的会覆盖前面的
        for env_file in reversed(env_files):
            load_dotenv(env_file, override=True)

        # 读取配置（如果没有通过命令行参数传入）
        if not self.model:
            if self.provider == "siliconflow":
                self.model = os.getenv(
                    "SILICONFLOW_MODEL", "PaddlePaddle/PaddleOCR-VL-1.5"
                )
            elif self.provider == "openai":
                self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

        if not self.api_key:
            if self.provider == "siliconflow":
                self.api_key = os.getenv("SILICONFLOW_API_KEY", "")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY", "")

        if not self.base_url and self.provider == "openai":
            self.base_url = os.getenv("OPENAI_BASE_URL")

        # 读取 timeout 配置（只有当 timeout 是默认值 None 时才从环境变量读取）
        if self.timeout is None:
            timeout_env = os.getenv("REQUEST_TIMEOUT")
            if timeout_env:
                with contextlib.suppress(ValueError):
                    self.timeout = int(timeout_env)

        # 读取 RPM 配置（只有当 rpm 是默认值时才从环境变量读取）
        if self.rpm == 1000:
            rpm_env = os.getenv(f"{self.provider.upper()}_RPM")
            if rpm_env:
                with contextlib.suppress(ValueError):
                    self.rpm = int(rpm_env)

        # 读取 TPM 配置（只有当 tpm 是默认值时才从环境变量读取）
        if self.tpm == 80000:
            tpm_env = os.getenv(f"{self.provider.upper()}_TPM")
            if tpm_env:
                with contextlib.suppress(ValueError):
                    self.tpm = int(tpm_env)

        # 读取 max_concurrent 配置
        if self.max_concurrent is None:
            concurrent_env = os.getenv(f"{self.provider.upper()}_MAX_CONCURRENT")
            if concurrent_env:
                with contextlib.suppress(ValueError):
                    self.max_concurrent = int(concurrent_env)


class ConfigManager:
    """
    配置管理器

    提供全局配置访问和修改接口
    """

    _provider_config: ProviderConfig | None = None
    _app_config: AppConfig | None = None

    @classmethod
    def load_config_file(cls, config_file: str | None = None) -> None:
        """
        加载配置文件

        Parameters
        ----------
        config_file : str, optional
            配置文件路径若不指定则使用默认路径
        """
        if config_file:
            load_dotenv(config_file)
        else:
            config_path = get_config_file()
            if config_path.exists():
                load_dotenv(config_path)

    @classmethod
    def load_env(cls, env_file: str | None = None) -> None:
        """
        加载环境变量

        Parameters
        ----------
        env_file : str, optional
            .env 文件路径若不指定则自动查找
        """
        load_dotenv(env_file)

    @classmethod
    def get_provider_config(
        cls,
        provider: str = "siliconflow",
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> ProviderConfig:
        """
        获取服务商配置

        Parameters
        ----------
        provider : str, optional
            服务商名称，默认为 "siliconflow"
        api_key : str, optional
            API Key
        model : str, optional
            模型名称
        base_url : str, optional
            API 基础 URL
        timeout : int, optional
            请求超时时间（秒），None 表示无限制

        Returns
        -------
        ProviderConfig
            服务商配置对象
        """
        if (
            api_key
            or model
            or base_url
            or timeout is not None
            or cls._provider_config is None
            or cls._provider_config.provider != provider
        ):
            cls._provider_config = ProviderConfig(
                provider=provider,
                api_key=api_key or "",
                model=model or "",
                base_url=base_url,
                timeout=timeout,
            )

        return cls._provider_config

    @classmethod
    def get_app_config(cls) -> AppConfig:
        """
        获取应用配置

        Returns
        -------
        AppConfig
            应用配置对象（单例）
        """
        if cls._app_config is None:
            cls._app_config = AppConfig()
        return cls._app_config

    @classmethod
    def set_provider(cls, provider: str) -> None:
        """
        设置服务商

        Parameters
        ----------
        provider : str
            服务商名称
        """
        if cls._provider_config:
            cls._provider_config.provider = provider

    @classmethod
    def set_output_dir(cls, output_dir: str) -> None:
        """
        设置输出目录

        Parameters
        ----------
        output_dir : str
            输出目录路径
        """
        config = cls.get_app_config()
        config.output_dir = output_dir

    @classmethod
    def reset(cls) -> None:
        """重置所有配置"""
        cls._provider_config = None
        cls._app_config = None
