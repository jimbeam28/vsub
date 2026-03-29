pub mod asr;
pub mod cli;
pub mod core;

use std::path::{Path, PathBuf};
use thiserror::Error;
use tracing::{info, debug};

/// 应用程序错误类型
#[derive(Error, Debug)]
pub enum VsubError {
    #[error("IO 错误: {0}")]
    Io(#[from] std::io::Error),

    #[error("配置文件错误: {0}")]
    Config(String),

    #[error("视频处理错误: {0}")]
    Video(String),

    #[error("音频提取错误: {0}")]
    Audio(String),

    #[error("ASR 引擎错误: {0}")]
    Asr(String),

    #[error("字幕生成错误: {0}")]
    Subtitle(String),

    #[error("参数错误: {0}")]
    Argument(String),

    #[error("未找到 FFmpeg，请确保 FFmpeg 已安装并在 PATH 中")]
    FFmpegNotFound,

    #[error("未找到 Python ASR 引擎")]
    PythonEngineNotFound,

    #[error("处理被取消")]
    Cancelled,

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}

pub type Result<T> = std::result::Result<T, VsubError>;

/// 处理单个视频文件
pub async fn process_video<P: AsRef<Path>>(
    input: P,
    config: &core::Config,
) -> Result<PathBuf> {
    let input = input.as_ref();

    info!("开始处理: {}", input.display());

    // 1. 检查 FFmpeg
    debug!("检查 FFmpeg...");
    let _ffmpeg = core::check_ffmpeg()?;

    // 2. 验证视频
    debug!("验证视频文件...");
    core::validate_video(input)?;
    let video_info = core::probe_video(input)?;
    info!(
        "视频信息: {}x{} @ {:.2}fps, 时长: {:.2}s",
        video_info.width, video_info.height, video_info.fps, video_info.duration
    );

    if !video_info.has_audio {
        return Err(VsubError::Video("视频没有音频轨道".to_string()));
    }

    // 3. 提取音频
    debug!("提取音频...");
    let extractor = core::AudioExtractor::new()?;
    let temp_audio = core::temp_audio_path(input);
    extractor.extract_to_wav(input, &temp_audio)?;
    info!("音频已提取到: {}", temp_audio.display());

    // 确保在结束时清理临时文件
    let temp_audio_clone = temp_audio.clone();
    let _cleanup = scopeguard::guard(temp_audio_clone, |path| {
        if !config.keep_audio {
            core::cleanup_audio(&path);
        }
    });

    // 4. ASR 识别
    debug!("启动 ASR 识别...");
    let engine = asr::create_engine(config.engine);
    if !engine.is_available() {
        return Err(VsubError::PythonEngineNotFound);
    }

    let words = engine.transcribe(&temp_audio, config.language.as_deref()).await?;
    info!("识别完成: {} 个单词", words.len());

    if words.is_empty() {
        return Err(VsubError::Asr("未识别到任何语音".to_string()));
    }

    // 5. 生成字幕
    debug!("生成字幕...");
    let segments = core::segments_from_asr_result(
        &words,
        5.0,  // 最大片段时长 5 秒
        config.max_line_length * config.max_line_count,
    );
    info!("生成 {} 个字幕片段", segments.len());

    let generator = core::SubtitleGenerator::new(
        config.max_line_length,
        config.max_line_count,
    );

    // 6. 确定输出路径
    let output_path = determine_output_path(input, config)?;
    debug!("输出路径: {}", output_path.display());

    // 7. 写入文件
    generator.write_to_file(&segments, config.format, &output_path, config.overwrite)?;
    info!("字幕已保存: {}", output_path.display());

    Ok(output_path)
}

/// 确定输出路径
fn determine_output_path(
    input: &Path,
    config: &core::Config,
) -> Result<PathBuf> {
    let base_name = input
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("output");

    let ext = match config.format {
        core::OutputFormat::Srt => "srt",
        core::OutputFormat::Vtt => "vtt",
    };

    let output_dir = config
        .output_dir
        .clone()
        .unwrap_or_else(|| input.parent().unwrap_or(Path::new(".")).to_path_buf());

    // 确保输出目录存在
    std::fs::create_dir_all(&output_dir)
        .map_err(|e| VsubError::Io(e))?;

    Ok(output_dir.join(format!("{}.{}", base_name, ext)))
}

/// 处理多个视频文件
pub async fn process_videos<P: AsRef<Path>>(
    inputs: &[P],
    config: &core::Config,
) -> Vec<(PathBuf, Result<PathBuf>)> {
    let mut results = Vec::with_capacity(inputs.len());

    for input in inputs {
        let path = input.as_ref().to_path_buf();
        let result = process_video(input, config).await;
        results.push((path, result));
    }

    results
}
