use std::path::Path;
use std::process::Command;
use tracing::{debug, trace};

use crate::VsubError;

/// 视频信息
#[derive(Debug, Clone)]
pub struct VideoInfo {
    pub path: std::path::PathBuf,
    pub duration: f64,
    pub width: u32,
    pub height: u32,
    pub has_audio: bool,
    pub audio_codec: Option<String>,
    pub video_codec: Option<String>,
    pub fps: f64,
}

impl VideoInfo {
    pub fn duration_seconds(&self) -> f64 {
        self.duration
    }

    pub fn resolution(&self) -> String {
        format!("{}x{}", self.width, self.height)
    }
}

/// 检查 FFmpeg 是否可用
pub fn check_ffmpeg() -> Result<std::path::PathBuf, VsubError> {
    let output = Command::new("which")
        .arg("ffmpeg")
        .output()
        .map_err(|e| VsubError::Io(e))?;

    if !output.status.success() {
        return Err(VsubError::FFmpegNotFound);
    }

    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok(std::path::PathBuf::from(path))
}

/// 使用 ffprobe 探测视频信息
pub fn probe_video<P: AsRef<Path>>(path: P) -> Result<VideoInfo, VsubError> {
    let path = path.as_ref();

    trace!("Probing video: {}", path.display());

    let output = Command::new("ffprobe")
        .args(&[
            "-v", "error",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            path.to_str().unwrap(),
        ])
        .output()
        .map_err(|e| {
            if e.kind() == std::io::ErrorKind::NotFound {
                VsubError::FFmpegNotFound
            } else {
                VsubError::Io(e)
            }
        })?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(VsubError::Video(format!("ffprobe 失败: {}", stderr)));
    }

    let json: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| VsubError::Video(format!("解析 ffprobe 输出失败: {}", e)))?;

    parse_video_info(path, &json)
}

fn parse_video_info(path: &Path, json: &serde_json::Value) -> Result<VideoInfo, VsubError> {
    let streams = json.get("streams")
        .and_then(|s| s.as_array())
        .ok_or_else(|| VsubError::Video("无法获取视频流信息".to_string()))?;

    let format = json.get("format")
        .ok_or_else(|| VsubError::Video("无法获取格式信息".to_string()))?;

    // 查找视频流
    let video_stream = streams.iter()
        .find(|s| s.get("codec_type").and_then(|c| c.as_str()) == Some("video"));

    // 查找音频流
    let audio_stream = streams.iter()
        .find(|s| s.get("codec_type").and_then(|c| c.as_str()) == Some("audio"));

    let duration = format.get("duration")
        .and_then(|d| d.as_str())
        .and_then(|s| s.parse::<f64>().ok())
        .or_else(|| video_stream.and_then(|s| s.get("duration").and_then(|d| d.as_str()).and_then(|s| s.parse::<f64>().ok())))
        .unwrap_or(0.0);

    let (width, height) = video_stream
        .map(|s| {
            let width = s.get("width").and_then(|w| w.as_u64()).unwrap_or(0) as u32;
            let height = s.get("height").and_then(|h| h.as_u64()).unwrap_or(0) as u32;
            (width, height)
        })
        .unwrap_or((0, 0));

    let fps = video_stream
        .and_then(|s| s.get("r_frame_rate").and_then(|r| r.as_str()))
        .and_then(|r| {
            let parts: Vec<&str> = r.split('/').collect();
            if parts.len() == 2 {
                let num = parts[0].parse::<f64>().ok()?;
                let den = parts[1].parse::<f64>().ok()?;
                Some(if den > 0.0 { num / den } else { 0.0 })
            } else {
                None
            }
        })
        .unwrap_or(0.0);

    let video_codec = video_stream
        .and_then(|s| s.get("codec_name").and_then(|c| c.as_str()).map(|s| s.to_string()));

    let audio_codec = audio_stream
        .and_then(|s| s.get("codec_name").and_then(|c| c.as_str()).map(|s| s.to_string()));

    debug!(
        "Video info: {}x{} @ {:.2}fps, duration: {:.2}s, audio: {}",
        width, height, fps, duration, audio_stream.is_some()
    );

    Ok(VideoInfo {
        path: path.to_path_buf(),
        duration,
        width,
        height,
        has_audio: audio_stream.is_some(),
        audio_codec,
        video_codec,
        fps,
    })
}

/// 验证视频文件
pub fn validate_video<P: AsRef<Path>>(path: P) -> Result<(), VsubError> {
    let path = path.as_ref();

    if !path.exists() {
        return Err(VsubError::Video(format!(
            "文件不存在: {}",
            path.display()
        )));
    }

    if !path.is_file() {
        return Err(VsubError::Video(format!(
            "不是文件: {}",
            path.display()
        )));
    }

    // 检查扩展名
    let ext = path.extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_lowercase())
        .unwrap_or_default();

    let supported = ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "ts", "m2ts"];
    if !supported.contains(&ext.as_str()) {
        debug!("Unknown video extension: {}", ext);
    }

    // 使用 ffprobe 验证
    probe_video(path)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_ffmpeg() {
        // 在 CI 环境中可能失败
        let _ = check_ffmpeg();
    }
}
