"""CLI 模块"""

import logging
import sys
from pathlib import Path

import click

from vsub import __version__
from vsub.config import Config, OutputFormat, WhisperModel, AsrEngineType
from vsub.core import process_video, process_videos

# 模块级变量，确保日志只配置一次
_logger_configured = False


def _configure_logging(verbose: bool) -> None:
    """配置日志（线程安全，只执行一次）"""
    global _logger_configured
    if not _logger_configured:
        level = logging.DEBUG if verbose else logging.INFO
        format_str = "%(levelname)s: %(message)s" if verbose else "%(message)s"
        logging.basicConfig(level=level, format=format_str)
        _logger_configured = True


@click.command()
@click.argument("input", nargs=-1, required=False, type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="输出字幕文件路径")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["srt", "vtt"], case_sensitive=False),
    help="输出字幕格式",
)
@click.option(
    "-e",
    "--engine",
    type=click.Choice(["whisper", "openai", "azure", "funasr"], case_sensitive=False),
    help="ASR 引擎类型",
)
@click.option(
    "-m",
    "--model",
    type=click.Choice(
        ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        case_sensitive=False,
    ),
    help="Whisper 模型大小",
)
@click.option("-l", "--language", help="语言代码 (如: en, zh, ja，留空为自动检测)")
@click.option(
    "-d",
    "--device",
    type=click.Choice(["cpu", "cuda", "mps"], case_sensitive=False),
    help="计算设备 (cpu/cuda/mps)，默认自动检测",
)
@click.option(
    "-j",
    "--max-workers",
    type=int,
    help="批量处理并发数，默认自动",
)
@click.option("--keep-audio", is_flag=True, help="保留临时提取的音频文件")
@click.option("--overwrite", is_flag=True, help="强制覆盖已存在的输出文件")
@click.option(
    "--init",
    is_flag=True,
    help="生成默认配置文件到当前目录",
)
@click.option("-v", "--verbose", is_flag=True, help="显示详细处理信息")
@click.version_option(version=__version__, prog_name="vsub")
def cli(
    input: tuple,
    output: Path,
    format: str,
    engine: str,
    model: str,
    language: str,
    device: str,
    max_workers: int,
    keep_audio: bool,
    overwrite: bool,
    init: bool,
    verbose: bool,
):
    """视频字幕生成工具

    示例:
        vsub input.mp4                    # 生成 input.srt
        vsub input.mp4 -o output.srt      # 指定输出文件
        vsub *.mp4                        # 批量处理
    """
    # 设置日志级别（只配置一次）
    _configure_logging(verbose)

    # 处理 --init 命令
    if init:
        return init_config()

    # 检查输入
    if not input:
        click.echo("错误: 请提供输入视频文件", err=True)
        sys.exit(1)

    input_paths = list(input)

    # 如果指定了输出路径，检查输入是否只有一个文件
    if output and len(input_paths) > 1:
        click.echo("错误: 批量处理时不能指定单一输出文件", err=True)
        sys.exit(1)

    # 加载配置
    config = Config.load()

    # 应用命令行参数覆盖
    if format:
        config.format = OutputFormat(format.lower())
    if engine:
        config.engine = AsrEngineType(engine.lower())
    if model:
        config.model = WhisperModel(model.lower())
    if language:
        config.language = language
    if device:
        # 注意：device 不存储在 config 中，直接传递给 process_video
        pass
    if max_workers is not None:
        config.max_workers = max_workers
    if keep_audio:
        config.keep_audio = True
    if overwrite:
        config.overwrite = True
    if output:
        config.output_dir = output.parent

    # 处理单个或多个文件
    if len(input_paths) == 1:
        try:
            result_path = process_video(input_paths[0], config, device=device)
            click.echo(f"✓ 字幕已生成: {result_path}")
            sys.exit(0)
        except Exception as e:
            click.echo(f"错误: {e}", err=True)
            sys.exit(1)
    else:
        results = process_videos(input_paths, config, max_workers=max_workers, device=device)
        success = sum(1 for _, out in results if out is not None)
        failed = len(results) - success
        click.echo(f"\n完成: {success}/{len(input_paths)} 个文件成功")
        if failed > 0:
            click.echo(f"失败: {failed} 个文件", err=True)
            sys.exit(1)
        sys.exit(0)


def init_config():
    """生成默认配置文件"""
    try:
        config_path = Path("vsub.yaml")

        if config_path.exists():
            if not click.confirm("配置文件 vsub.yaml 已存在，是否覆盖?"):
                click.echo("已取消")
                return

        content = Config.default_config_yaml()
        config_path.write_text(content, encoding="utf-8")
        click.echo(f"✓ 配置文件已生成: {config_path}")
        click.echo("您可以使用以下命令编辑配置文件:")
        click.echo("  vim vsub.yaml")
    except OSError as e:
        click.echo(f"错误: 无法写入配置文件: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"错误: 生成配置文件失败: {e}", err=True)
        sys.exit(1)


def main():
    """入口点"""
    cli()


if __name__ == "__main__":
    main()
