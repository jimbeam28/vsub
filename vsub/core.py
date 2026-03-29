"""核心处理模块"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

from tqdm import tqdm

from vsub.asr import AsrWord, create_engine, ENGINE_REGISTRY
from vsub.audio import AudioExtractor, cleanup_audio, temp_audio_path
from vsub.config import Config, OutputFormat
from vsub.device import get_device
from vsub.subtitle import SubtitleGenerator, SubtitleSegment, segments_from_asr_result
from vsub.video import probe_video, validate_video

logger = logging.getLogger(__name__)


def process_video(
    input_path: Path,
    config: Config,
    device: Optional[str] = None,
    show_progress: bool = True,
) -> Path:
    """处理单个视频文件

    Args:
        input_path: 输入视频路径
        config: 配置对象
        device: 计算设备 (cuda/mps/cpu)，None 则自动检测
        show_progress: 是否显示进度条

    Returns:
        输出字幕文件路径
    """
    logger.info(f"开始处理: {input_path}")

    # 1. 验证视频
    logger.debug("验证视频文件...")
    validate_video(input_path)
    video_info = probe_video(input_path)
    logger.info(f"视频信息: {video_info.resolution} @ {video_info.fps:.2f}fps, 时长: {video_info.duration:.2f}s")

    if not video_info.has_audio:
        raise RuntimeError("视频没有音频轨道")

    # 2. 提取音频
    logger.info("提取音频...")
    extractor = AudioExtractor()
    temp_audio = temp_audio_path(input_path)
    try:
        extractor.extract_to_wav(input_path, temp_audio, show_progress=show_progress)
        logger.debug(f"音频已提取到: {temp_audio}")

        # 3. ASR 识别（带真实进度条）
        logger.info("启动 ASR 识别...")

        # 自动检测设备
        if device is None:
            device = get_device(prefer_gpu=True)
        logger.info(f"使用设备: {device}")

        engine = create_engine(
            engine_type=config.engine.value,
            model=config.model.value,
            device=device,
        )
        if not engine.is_available():
            raise RuntimeError("ASR 引擎不可用，请安装 faster-whisper")

        # 使用 tqdm 显示真实进度
        if show_progress:
            with tqdm(total=100, desc="语音识别", unit="%") as pbar:
                def update_progress(progress: float):
                    pbar.n = int(progress * 100)
                    pbar.refresh()

                words = engine.transcribe(
                    temp_audio,
                    language=config.language,
                    progress_callback=update_progress
                )
                pbar.n = 100
                pbar.refresh()
        else:
            words = engine.transcribe(temp_audio, language=config.language)

        logger.info(f"识别完成: {len(words)} 个单词")

        if not words:
            raise RuntimeError("未识别到任何语音")

        # 4. 生成字幕
        logger.debug("生成字幕...")
        segments = segments_from_asr_result(
            words,
            max_duration=5.0,
            max_chars=config.max_line_length * config.max_line_count,
        )
        logger.info(f"生成 {len(segments)} 个字幕片段")

        generator = SubtitleGenerator(
            max_line_length=config.max_line_length,
            max_line_count=config.max_line_count,
        )

        # 5. 确定输出路径
        output_path = determine_output_path(input_path, config)
        logger.debug(f"输出路径: {output_path}")

        # 6. 写入文件
        generator.write_to_file(segments, config.format, output_path, config.overwrite)
        logger.info(f"✓ 字幕已保存: {output_path}")

        return output_path

    finally:
        # 清理临时音频文件
        if not config.keep_audio:
            cleanup_audio(temp_audio)


def process_videos(
    inputs: List[Path],
    config: Config,
    max_workers: Optional[int] = None,
    device: Optional[str] = None,
) -> List[Tuple[Path, Optional[Path]]]:
    """处理多个视频文件

    Args:
        inputs: 输入视频路径列表
        config: 配置对象
        max_workers: 最大并发数，None 则根据 CPU 核心数自动选择
        device: 计算设备，None 则自动检测

    Returns:
        结果列表，每个元素为 (输入路径, 输出路径)，失败时输出路径为 None
    """
    if not inputs:
        return []

    # 检查重复路径
    path_counts = {}
    for p in inputs:
        path_counts[p] = path_counts.get(p, 0) + 1
    duplicates = [p for p, count in path_counts.items() if count > 1]
    if duplicates:
        logger.warning(f"检测到重复输入路径: {duplicates}")

    # 如果只有一个文件，直接处理，不使用并发
    if len(inputs) == 1:
        try:
            output_path = process_video(inputs[0], config, device=device)
            return [(inputs[0], output_path)]
        except Exception as e:
            logger.error(f"✗ 处理失败: {e}")
            return [(inputs[0], None)]

    # 自动检测设备（只检测一次）
    if device is None:
        device = get_device(prefer_gpu=True)
    logger.info(f"批量处理使用设备: {device}")

    # 确定并发数
    if max_workers is None:
        if config.max_workers is not None:
            max_workers = config.max_workers
        else:
            import os
            max_workers = min(os.cpu_count() or 1, 4)  # 默认最多4个并发

    logger.info(f"并发数: {max_workers}")

    # 使用 OrderedDict 保持插入顺序并处理重复
    from collections import OrderedDict
    results_map: OrderedDict[Path, Optional[Path]] = OrderedDict()
    completed = 0
    failed_count = 0

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，保留原始顺序信息
            future_to_index = {
                executor.submit(
                    _process_video_wrapper,
                    input_path,
                    config,
                    device,
                ): (idx, input_path)
                for idx, input_path in enumerate(inputs)
            }

            # 使用进度条显示总体进度
            with tqdm(total=len(inputs), desc="批量处理", unit="文件") as pbar:
                for future in as_completed(future_to_index):
                    idx, input_path = future_to_index[future]
                    try:
                        output_path = future.result()
                        results_map[input_path] = output_path
                        logger.info(f"✓ 完成: {input_path.name}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ 处理失败 {input_path.name}: {e}")
                        results_map[input_path] = None

                    completed += 1
                    pbar.update(1)
                    pbar.set_postfix({
                        "完成": f"{completed}/{len(inputs)}",
                        "成功": completed - failed_count,
                        "失败": failed_count
                    })
    except Exception as e:
        logger.error(f"批量处理异常: {e}")
        raise

    # 按原始输入顺序返回结果（处理重复路径）
    return [(inp, results_map.get(inp)) for inp in inputs]


def _process_video_wrapper(
    input_path: Path,
    config: Config,
    device: str,
) -> Optional[Path]:
    """处理视频的包装器，用于捕获日志"""
    try:
        # 在子线程中禁用进度条，避免显示混乱
        return process_video(input_path, config, device=device, show_progress=False)
    except Exception as e:
        logger.error(f"处理 {input_path.name} 时出错: {e}")
        raise


def determine_output_path(input_path: Path, config: Config) -> Path:
    """确定输出路径"""
    base_name = input_path.stem

    ext = "srt" if config.format == OutputFormat.SRT else "vtt"

    if config.output_dir:
        output_dir = config.output_dir
    else:
        output_dir = input_path.parent

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir / f"{base_name}.{ext}"
