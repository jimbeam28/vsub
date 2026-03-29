pub mod cli;
pub mod core;

use std::path::{Path, PathBuf};
use thiserror::Error;

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
    _input: P,
    _config: &core::Config,
) -> Result<PathBuf> {
    // TODO: Phase 2 实现
    Err(VsubError::Video("功能尚未实现".to_string()))
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
