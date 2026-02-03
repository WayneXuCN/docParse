"""
CLI 入口模块
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from docparse.config import ConfigManager
from docparse.models import ProcessStatus
from docparse.ocr_service import OCRService

app = typer.Typer(
    name="docparse",
    help="智能文档解析工具",
    add_completion=False,
)
console = Console()


@app.command()
def file(
    file_path: Annotated[str, typer.Argument(help="要处理的文件路径")],
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            help="服务商 (siliconflow, openai)",
            rich_help_panel="API 设置",
        ),
    ] = "siliconflow",
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            "-k",
            help="API Key (优先使用环境变量)",
            rich_help_panel="API 设置",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="模型名称", rich_help_panel="API 设置"),
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option(
            "--base-url",
            help="API 基础 URL (用于 OpenAI 兼容 API)",
            rich_help_panel="API 设置",
        ),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option(
            "--timeout", "-t", help="请求超时时间（秒）", rich_help_panel="API 设置"
        ),
    ] = None,
    output_dir: Annotated[
        str | None,
        typer.Option("--output", "-o", help="输出目录"),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="自定义提示词"),
    ] = None,
):
    """
    处理单个文件

    支持的格式: PDF, PNG, JPG, JPEG, BMP, TIF, TIFF
    """
    typer.echo(f"正在处理文件: {file_path}")
    typer.echo(f"使用服务商: {provider}")

    try:
        # 使用 rich 进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("正在处理...", total=100)

            def progress_callback(current: int, total: int, message: str = "") -> None:
                if total > 0:
                    percentage = (current / total) * 100
                    if percentage < 100:
                        progress.update(task, completed=percentage, description=message)
                    else:
                        progress.update(task, completed=100, description="处理完成")

            service = OCRService(
                provider=provider,
                api_key=api_key,
                model=model,
                base_url=base_url,
                timeout=timeout if timeout != 0 else None,
                progress_callback=progress_callback,
            )
            result = service.process_file(file_path, output_dir, prompt)

        if result.status == ProcessStatus.SUCCESS:
            console.print("[green]✓[/green] 处理成功!")
            console.print(f"  输出文件: {result.output_path}")
            console.print(f"  处理时间: {result.processing_time:.2f}秒")
        else:
            console.print(f"[red]✗[/red] 处理失败: {result.error_message}")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"发生错误: {str(e)}", err=True)
        raise typer.Exit(1) from None


@app.command()
def batch(
    files: Annotated[
        list[str] | None,
        typer.Option("--file", "-f", help="要处理的文件路径（可多次使用）"),
    ] = None,
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            help="服务商 (siliconflow, openai)",
            rich_help_panel="API 设置",
        ),
    ] = "siliconflow",
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="API Key", rich_help_panel="API 设置"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="模型名称", rich_help_panel="API 设置"),
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", help="API 基础 URL", rich_help_panel="API 设置"),
    ] = None,
    output_dir: Annotated[
        str | None,
        typer.Option("--output", "-o", help="输出目录"),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="自定义提示词"),
    ] = None,
):
    """
    批量处理多个文件

    使用 --file 或 -f 选项指定多个文件
    """
    if files is None:
        files = []
    if not files:
        typer.echo("请至少指定一个文件", err=True)
        typer.echo("示例: docparse batch --file file1.png --file file2.jpg")
        raise typer.Exit(1)

    typer.echo(f"批量处理 {len(files)} 个文件...")
    typer.echo(f"使用服务商: {provider}")

    try:
        service = OCRService(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
        result = service.process_files(files, output_dir, prompt)

        typer.echo("\n处理完成:")
        typer.echo(f"  总文件数: {result.total_files}")
        typer.echo(f"  成功: {result.success_count}")
        typer.echo(f"  失败: {result.failed_count}")
        typer.echo(f"  成功率: {result.success_rate:.1f}%")
        typer.echo(f"  总耗时: {result.total_processing_time:.2f}秒")

        if result.failed_count > 0:
            typer.echo("\n失败的文件:")
            for r in result.results:
                if r.status == ProcessStatus.FAILED:
                    typer.echo(f"  - {r.file_path}: {r.error_message}")

    except Exception as e:
        typer.echo(f"发生错误: {str(e)}", err=True)
        raise typer.Exit(1) from None


@app.command()
def dir(
    directory: Annotated[str, typer.Argument(help="要处理的目录路径")],
    pattern: Annotated[
        str,
        typer.Option("--pattern", help="文件匹配模式（默认: *）"),
    ] = "*",
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            help="服务商 (siliconflow, openai)",
            rich_help_panel="API 设置",
        ),
    ] = "siliconflow",
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="API Key", rich_help_panel="API 设置"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="模型名称", rich_help_panel="API 设置"),
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", help="API 基础 URL", rich_help_panel="API 设置"),
    ] = None,
    output_dir: Annotated[
        str | None,
        typer.Option("--output", "-o", help="输出目录"),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="自定义提示词"),
    ] = None,
):
    """
    处理目录中的所有文件

    默认处理目录中所有支持的文件格式
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        typer.echo(f"目录不存在: {directory}", err=True)
        raise typer.Exit(1)

    if not dir_path.is_dir():
        typer.echo(f"路径不是目录: {directory}", err=True)
        raise typer.Exit(1)

    typer.echo(f"正在处理目录: {directory}")
    typer.echo(f"使用服务商: {provider}")

    try:
        service = OCRService(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
        result = service.process_directory(directory, output_dir, pattern, prompt)

        if result.total_files == 0:
            typer.echo("未找到支持的文件")
            raise typer.Exit(0)

        typer.echo("\n处理完成:")
        typer.echo(f"  总文件数: {result.total_files}")
        typer.echo(f"  成功: {result.success_count}")
        typer.echo(f"  失败: {result.failed_count}")
        typer.echo(f"  成功率: {result.success_rate:.1f}%")
        typer.echo(f"  总耗时: {result.total_processing_time:.2f}秒")

        if result.failed_count > 0:
            typer.echo("\n失败的文件:")
            for r in result.results:
                if r.status == ProcessStatus.FAILED:
                    typer.echo(f"  - {r.file_path}: {r.error_message}")

    except Exception as e:
        typer.echo(f"发生错误: {str(e)}", err=True)
        raise typer.Exit(1) from None


@app.command()
def config(
    provider: Annotated[
        str | None,
        typer.Option("--show-provider", help="显示当前服务商配置"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", "-s", help="显示当前配置"),
    ] = False,
):
    """
    配置管理

    设置或查看配置信息
    """
    if show or provider:
        ConfigManager.load_env()

        app_config = ConfigManager.get_app_config()

        if provider:
            provider_config = ConfigManager.get_provider_config(provider=provider)
            typer.echo(f"{provider.upper()} 服务商配置:")
            typer.echo(f"  Provider: {provider_config.provider}")
            typer.echo(f"  Model: {provider_config.model}")
            typer.echo(f"  Base URL: {provider_config.base_url or 'N/A'}")
            typer.echo(
                f"  API Key: {'已设置' if provider_config.api_key else '未设置'}"
            )
        elif show:
            typer.echo("当前配置:")
            typer.echo(f"  输出目录: {app_config.output_dir}")

            sf_config = ConfigManager.get_provider_config(provider="siliconflow")
            typer.echo("\n  SiliconFlow:")
            typer.echo(f"    Model: {sf_config.model}")
            typer.echo(f"    API Key: {'已设置' if sf_config.api_key else '未设置'}")

            oa_config = ConfigManager.get_provider_config(provider="openai")
            typer.echo("\n  OpenAI:")
            typer.echo(f"    Model: {oa_config.model}")
            typer.echo(f"    Base URL: {oa_config.base_url or 'N/A'}")
            typer.echo(f"    API Key: {'已设置' if oa_config.api_key else '未设置'}")

            typer.echo("\n提示: 请使用 .env 文件设置 API Key")
    else:
        typer.echo("请使用 --show 或 --show-provider 选项")
        typer.echo("示例:")
        typer.echo("  docparse config --show")
        typer.echo("  docparse config --show-provider siliconflow")
        typer.echo("  docparse config --show-provider openai")


if __name__ == "__main__":
    app()
