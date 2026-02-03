"""
数据模型模块
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class FileType(str, Enum):
    """文件类型枚举"""

    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"
    BMP = "image/bmp"
    TIFF = "image/tiff"
    UNKNOWN = "application/octet-stream"


class ProcessStatus(str, Enum):
    """处理状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class APIResponse:
    """
    API 响应数据类

    Parameters
    ----------
    status_code : int
        HTTP 状态码
    content : str, optional
        响应内容
    error : str, optional
        错误信息
    raw_response : dict, optional
        原始响应数据
    """

    status_code: int
    content: str | None = None
    error: str | None = None
    raw_response: dict | None = None

    @property
    def is_success(self) -> bool:
        """
        检查响应是否成功

        Returns
        -------
        bool
            成功返回 True，否则返回 False
        """
        return self.status_code == 200 and self.error is None


@dataclass
class OCRResult:
    """
    OCR 处理结果数据类

    Parameters
    ----------
    file_path : str
        文件路径
    output_path : str
        输出文件路径
    content : str
        处理后的文本内容
    status : ProcessStatus
        处理状态
    error_message : str, optional
        错误信息
    processing_time : float, optional
        处理时间（秒）
    created_at : datetime, optional
        创建时间
    """

    file_path: str
    output_path: str
    content: str
    status: ProcessStatus
    error_message: str | None = None
    processing_time: float | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns
        -------
        dict
            字典形式的处理结果
        """
        return {
            "file_path": self.file_path,
            "output_path": self.output_path,
            "status": self.status.value,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BatchResult:
    """
    批量处理结果数据类

    Parameters
    ----------
    total_files : int
        总文件数
    success_count : int
        成功数量
    failed_count : int
        失败数量
    results : list, optional
        单个处理结果列表
    total_processing_time : float, optional
        总处理时间（秒）
    """

    total_files: int
    success_count: int
    failed_count: int
    results: list[OCRResult] = field(default_factory=list)
    total_processing_time: float | None = None

    @property
    def success_rate(self) -> float:
        """
        计算成功率

        Returns
        -------
        float
            成功率（百分比）
        """
        if self.total_files == 0:
            return 0.0
        return (self.success_count / self.total_files) * 100

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns
        -------
        dict
            字典形式的批量处理结果
        """
        return {
            "total_files": self.total_files,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": round(self.success_rate, 2),
            "total_processing_time": self.total_processing_time,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class FileInfo:
    """
    文件信息数据类

    Parameters
    ----------
    path : Path
        文件路径
    size : int
        文件大小（字节）
    mime_type : FileType
        MIME 类型
    is_valid : bool, optional
        是否有效，默认为 True
    error_message : str, optional
        错误信息
    """

    path: Path
    size: int
    mime_type: FileType
    is_valid: bool = True
    error_message: str | None = None

    @classmethod
    def from_path(cls, path: Path, supported_extensions: list[str]) -> "FileInfo":
        """
        从路径创建文件信息

        Parameters
        ----------
        path : Path
            文件路径
        supported_extensions : list
            支持的文件扩展名列表

        Returns
        -------
        FileInfo
            文件信息对象
        """
        if not path.exists():
            return cls(
                path=path,
                size=0,
                mime_type=FileType.UNKNOWN,
                is_valid=False,
                error_message=f"文件不存在: {path}",
            )

        if not path.is_file():
            return cls(
                path=path,
                size=0,
                mime_type=FileType.UNKNOWN,
                is_valid=False,
                error_message=f"路径不是文件: {path}",
            )

        ext = path.suffix.lower()
        if ext not in supported_extensions:
            return cls(
                path=path,
                size=0,
                mime_type=FileType.UNKNOWN,
                is_valid=False,
                error_message=f"不支持的文件类型: {ext}",
            )

        size = path.stat().st_size
        mime_type = cls._get_mime_type(ext)

        return cls(path=path, size=size, mime_type=mime_type)

    @staticmethod
    def _get_mime_type(ext: str) -> FileType:
        """
        根据扩展名获取 MIME 类型

        Parameters
        ----------
        ext : str
            文件扩展名

        Returns
        -------
        FileType
            MIME 类型
        """
        mime_map = {
            ".pdf": FileType.PDF,
            ".png": FileType.PNG,
            ".jpg": FileType.JPEG,
            ".jpeg": FileType.JPEG,
            ".bmp": FileType.BMP,
            ".tif": FileType.TIFF,
            ".tiff": FileType.TIFF,
        }
        return mime_map.get(ext.lower(), FileType.UNKNOWN)
