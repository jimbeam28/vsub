use clap::{Parser, ValueEnum, ValueHint};
use std::path::PathBuf;

use crate::core::{OutputFormat, WhisperModel};

/// Vsub - 视频字幕生成工具
///
/// 使用语音识别技术自动生成视频字幕
#[derive(Parser, Debug)]
#[command(
    name = "vsub",
    version,
    about = "视频字幕生成工具",
    long_about = "Vsub 使用语音识别技术自动生成视频字幕。\n\n示例:\n  vsub input.mp4                    # 生成 input.srt\n  vsub input.mp4 -o output.srt      # 指定输出文件\n  vsub *.mp4                        # 批量处理",
    after_help = "更多信息请访问: https://github.com/yourusername/vsub"
)]
pub struct Cli {
    /// 输入视频文件路径
    #[arg(
        value_hint = ValueHint::FilePath,
        help = "输入视频文件路径，支持通配符批量处理"
    )]
    pub input: Vec<PathBuf>,

    /// 输出文件路径
    #[arg(
        short,
        long,
        value_hint = ValueHint::FilePath,
        help = "输出字幕文件路径（默认: 与输入文件同名）"
    )]
    pub output: Option<PathBuf>,

    /// 输出格式
    #[arg(
        short,
        long,
        value_enum,
        help = "输出字幕格式"
    )]
    pub format: Option<OutputFormatArg>,

    /// 模型大小
    #[arg(
        short,
        long,
        value_enum,
        help = "Whisper 模型大小"
    )]
    pub model: Option<ModelArg>,

    /// 语言代码
    #[arg(
        short,
        long,
        help = "语言代码 (如: en, zh, ja, 留空为自动检测)"
    )]
    pub language: Option<String>,

    /// 保留临时音频文件
    #[arg(
        long,
        help = "保留临时提取的音频文件"
    )]
    pub keep_audio: bool,

    /// 强制覆盖输出文件
    #[arg(
        long,
        help = "强制覆盖已存在的输出文件"
    )]
    pub overwrite: bool,

    /// 生成配置文件
    #[arg(
        long,
        help = "生成默认配置文件到当前目录",
        conflicts_with = "input"
    )]
    pub init: bool,

    /// 详细输出
    #[arg(
        short,
        long,
        help = "显示详细处理信息"
    )]
    pub verbose: bool,
}

/// 输出格式参数
#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum OutputFormatArg {
    Srt,
    Vtt,
}

impl OutputFormatArg {
    pub fn to_format(self) -> OutputFormat {
        match self {
            OutputFormatArg::Srt => OutputFormat::Srt,
            OutputFormatArg::Vtt => OutputFormat::Vtt,
        }
    }
}

/// 模型参数
#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum ModelArg {
    Tiny,
    Base,
    Small,
    Medium,
    Large,
    #[value(name = "large-v2")]
    LargeV2,
    #[value(name = "large-v3")]
    LargeV3,
}

impl ModelArg {
    pub fn to_model(self) -> WhisperModel {
        match self {
            ModelArg::Tiny => WhisperModel::Tiny,
            ModelArg::Base => WhisperModel::Base,
            ModelArg::Small => WhisperModel::Small,
            ModelArg::Medium => WhisperModel::Medium,
            ModelArg::Large => WhisperModel::Large,
            ModelArg::LargeV2 => WhisperModel::LargeV2,
            ModelArg::LargeV3 => WhisperModel::LargeV3,
        }
    }
}

impl Cli {
    /// 验证参数
    pub fn validate(&self) -> Result<(), String> {
        // 如果是 --init 模式，不需要验证输入
        if self.init {
            return Ok(());
        }

        // 检查是否有输入文件
        if self.input.is_empty() {
            return Err("请提供输入视频文件".to_string());
        }

        // 验证输入文件是否存在
        for path in &self.input {
            if !path.exists() {
                return Err(format!("输入文件不存在: {}", path.display()));
            }
            // 检查是否是文件
            if !path.is_file() {
                return Err(format!("路径不是文件: {}", path.display()));
            }
        }

        // 如果指定了输出路径，检查输入是否只有一个文件
        if self.output.is_some() && self.input.len() > 1 {
            return Err("批量处理时不能指定单一输出文件".to_string());
        }

        Ok(())
    }

    /// 获取所有输入文件（支持通配符展开）
    pub fn get_input_files(&self) -> Vec<PathBuf> {
        self.input.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cli_parse() {
        let cli = Cli::parse_from(["vsub", "input.mp4"]);
        assert_eq!(cli.input.len(), 1);
        assert_eq!(cli.input[0], PathBuf::from("input.mp4"));
    }

    #[test]
    fn test_format_conversion() {
        assert_eq!(
            OutputFormatArg::Srt.to_format(),
            OutputFormat::Srt
        );
        assert_eq!(
            OutputFormatArg::Vtt.to_format(),
            OutputFormat::Vtt
        );
    }

    #[test]
    fn test_model_conversion() {
        assert_eq!(ModelArg::Tiny.to_model(), WhisperModel::Tiny);
        assert_eq!(ModelArg::Base.to_model(), WhisperModel::Base);
        assert_eq!(ModelArg::Medium.to_model(), WhisperModel::Medium);
    }
}
