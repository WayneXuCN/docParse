"""
OCR 服务模块
"""

import time
from pathlib import Path

from docparse.client import OCRClient
from docparse.config import ConfigManager
from docparse.models import BatchResult, FileInfo, OCRResult, ProcessStatus


class OCRService:
    """
    OCR 服务类

    提供单文件、批量文件和目录处理的接口
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
        初始化服务

        Parameters
        ----------
        provider : str, optional
            服务商名称，默认为 "siliconflow"
        api_key : str, optional
            API 密钥
        model : str, optional
            模型名称
        base_url : str, optional
            API 基础 URL
        timeout : int, optional
            请求超时时间（秒）
        progress_callback : callable, optional
            进度回调函数，接收 (current, total, message) 参数
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.progress_callback = progress_callback
        self.app_config = ConfigManager.get_app_config()

    def process_file(
        self,
        file_path: str,
        output_dir: str | None = None,
        prompt: str | None = None,
    ) -> OCRResult:
        """
        处理单个文件

        Parameters
        ----------
        file_path : str
            文件路径
        output_dir : str, optional
            输出目录
        prompt : str, optional
            自定义提示词

        Returns
        -------
        OCRResult
            OCR 处理结果
        """
        start_time = time.time()

        try:
            file_info = FileInfo.from_path(
                Path(file_path),
                self.app_config.supported_extensions or [],
            )

            if not file_info.is_valid:
                return OCRResult(
                    file_path=file_path,
                    output_path="",
                    content="",
                    status=ProcessStatus.FAILED,
                    error_message=file_info.error_message,
                    processing_time=time.time() - start_time,
                )

            with OCRClient(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model,
                base_url=self.base_url,
                timeout=self.timeout,
                progress_callback=self.progress_callback,
            ) as client:
                api_response = client.process_image(
                    file_path=file_path,
                    mime_type=file_info.mime_type,
                    prompt=prompt,
                )

            if not api_response.is_success:
                return OCRResult(
                    file_path=file_path,
                    output_path="",
                    content="",
                    status=ProcessStatus.FAILED,
                    error_message=api_response.error,
                    processing_time=time.time() - start_time,
                )

            output_path = self._save_result(
                file_path=file_path,
                content=api_response.content,
                output_dir=output_dir,
            )

            return OCRResult(
                file_path=file_path,
                output_path=output_path,
                content=api_response.content,
                status=ProcessStatus.SUCCESS,
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return OCRResult(
                file_path=file_path,
                output_path="",
                content="",
                status=ProcessStatus.FAILED,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def process_files(
        self,
        file_paths: list[str],
        output_dir: str | None = None,
        prompt: str | None = None,
    ) -> BatchResult:
        """
        批量处理多个文件

        Parameters
        ----------
        file_paths : list
            文件路径列表
        output_dir : str, optional
            输出目录
        prompt : str, optional
            自定义提示词

        Returns
        -------
        BatchResult
            批量处理结果
        """
        start_time = time.time()
        results = []

        for file_path in file_paths:
            result = self.process_file(file_path, output_dir, prompt)
            results.append(result)

        success_count = sum(1 for r in results if r.status == ProcessStatus.SUCCESS)
        failed_count = len(results) - success_count

        return BatchResult(
            total_files=len(file_paths),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            total_processing_time=time.time() - start_time,
        )

    def process_directory(
        self,
        directory: str,
        output_dir: str | None = None,
        pattern: str = "*",
        prompt: str | None = None,
    ) -> BatchResult:
        """
        处理目录中的所有文件

        Parameters
        ----------
        directory : str
            目录路径
        output_dir : str, optional
            输出目录
        pattern : str, optional
            文件匹配模式，默认为 "*"
        prompt : str, optional
            自定义提示词

        Returns
        -------
        BatchResult
            批量处理结果
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return BatchResult(
                total_files=0,
                success_count=0,
                failed_count=0,
            )

        file_paths = []
        for ext in self.app_config.supported_extensions or []:
            file_paths.extend(dir_path.glob(f"{pattern}{ext}"))

        if not file_paths:
            return BatchResult(
                total_files=0,
                success_count=0,
                failed_count=0,
            )

        file_path_strings = [str(p) for p in file_paths]

        return self.process_files(file_path_strings, output_dir, prompt)

    def _save_result(
        self,
        file_path: str,
        content: str,
        output_dir: str | None = None,
    ) -> str:
        """
        保存处理结果

        Parameters
        ----------
        file_path : str
            原始文件路径
        content : str
            处理后的内容
        output_dir : str, optional
            输出目录

        Returns
        -------
        str
            保存后的文件路径
        """
        if output_dir:
            ConfigManager.set_output_dir(output_dir)

        output_path = ConfigManager.get_app_config().ensure_output_dir()

        base_name = Path(file_path).stem
        md_filename = output_path / f"{base_name}.md"

        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(content)

        return str(md_filename)
