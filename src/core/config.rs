use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// 字幕输出格式
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OutputFormat {
    Srt,
    Vtt,
}

impl Default for OutputFormat {
    fn default() -> Self {
        Self::Srt
    }
}

impl std::fmt::Display for OutputFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            OutputFormat::Srt => write!(f, "srt"),
            OutputFormat::Vtt => write!(f, "vtt"),
        }
    }
}

/// ASR 引擎类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AsrEngine {
    Whisper,
}

impl Default for AsrEngine {
    fn default() -> Self {
        Self::Whisper
    }
}

/// Whisper 模型大小
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum WhisperModel {
    Tiny,
    Base,
    Small,
    Medium,
    Large,
    LargeV2,
    LargeV3,
}

impl Default for WhisperModel {
    fn default() -> Self {
        Self::Base
    }
}

impl std::fmt::Display for WhisperModel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            WhisperModel::Tiny => write!(f, "tiny"),
            WhisperModel::Base => write!(f, "base"),
            WhisperModel::Small => write!(f, "small"),
            WhisperModel::Medium => write!(f, "medium"),
            WhisperModel::Large => write!(f, "large"),
            WhisperModel::LargeV2 => write!(f, "large-v2"),
            WhisperModel::LargeV3 => write!(f, "large-v3"),
        }
    }
}

/// 应用程序配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// 输出格式
    #[serde(default)]
    pub format: OutputFormat,

    /// ASR 引擎
    #[serde(default)]
    pub engine: AsrEngine,

    /// Whisper 模型
    #[serde(default = "default_model")]
    pub model: WhisperModel,

    /// 语言代码（如 "en", "zh"）
    pub language: Option<String>,

    /// 保留临时音频文件
    #[serde(default)]
    pub keep_audio: bool,

    /// 强制覆盖输出文件
    #[serde(default)]
    pub overwrite: bool,

    /// 输出目录
    pub output_dir: Option<PathBuf>,

    /// 最大行长度
    #[serde(default = "default_max_line_length")]
    pub max_line_length: usize,

    /// 每行最大单词数
    #[serde(default = "default_max_line_count")]
    pub max_line_count: usize,
}

fn default_model() -> WhisperModel {
    WhisperModel::Base
}

fn default_max_line_length() -> usize {
    80
}

fn default_max_line_count() -> usize {
    2
}

impl Default for Config {
    fn default() -> Self {
        Self {
            format: OutputFormat::default(),
            engine: AsrEngine::default(),
            model: default_model(),
            language: None,
            keep_audio: false,
            overwrite: false,
            output_dir: None,
            max_line_length: default_max_line_length(),
            max_line_count: default_max_line_count(),
        }
    }
}

impl Config {
    /// 从配置文件加载配置
    pub fn from_file(path: &std::path::Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }

    /// 加载默认配置，尝试从多个位置读取配置文件
    pub fn load() -> Self {
        let mut config = Config::default();

        // 尝试从默认位置加载配置文件
        if let Some(config_path) = Self::find_config_file() {
            if let Ok(file_config) = Self::from_file(&config_path) {
                config = config.merge(file_config);
            }
        }

        config
    }

    /// 合并另一个配置，其他配置的值覆盖当前配置
    pub fn merge(mut self, other: Config) -> Self {
        // 只有非默认值才合并
        if other.format != OutputFormat::default() {
            self.format = other.format;
        }
        if other.model != default_model() {
            self.model = other.model;
        }
        if other.language.is_some() {
            self.language = other.language;
        }
        if other.keep_audio {
            self.keep_audio = other.keep_audio;
        }
        if other.overwrite {
            self.overwrite = other.overwrite;
        }
        if other.output_dir.is_some() {
            self.output_dir = other.output_dir;
        }
        if other.max_line_length != default_max_line_length() {
            self.max_line_length = other.max_line_length;
        }
        if other.max_line_count != default_max_line_count() {
            self.max_line_count = other.max_line_count;
        }
        self
    }

    /// 查找配置文件
    fn find_config_file() -> Option<PathBuf> {
        // 优先级：当前目录 > 用户配置目录 > 系统配置目录
        let candidates = [
            PathBuf::from("vsub.toml"),
            dirs::config_dir()
                .map(|d| d.join("vsub").join("config.toml"))
                .unwrap_or_default(),
            PathBuf::from("/etc/vsub/config.toml"),
        ];

        for path in &candidates {
            if path.exists() {
                return Some(path.clone());
            }
        }

        None
    }

    /// 生成默认配置文件内容
    pub fn default_config_toml() -> String {
        r#"# Vsub 配置文件
# 放置于当前目录作为 vsub.toml，或 ~/.config/vsub/config.toml

# 输出格式: srt 或 vtt
format = "srt"

# ASR 引擎: whisper
engine = "whisper"

# Whisper 模型: tiny, base, small, medium, large, large-v2, large-v3
model = "base"

# 语言代码 (如 "en", "zh", 留空为自动检测)
# language = "zh"

# 保留临时音频文件
keep_audio = false

# 强制覆盖输出文件
overwrite = false

# 输出目录 (留空为与输入文件相同目录)
# output_dir = "./output"

# 字幕最大行长度
max_line_length = 80

# 字幕每行最大单词数
max_line_count = 2
"#
        .to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.format, OutputFormat::Srt);
        assert_eq!(config.model, WhisperModel::Base);
        assert!(!config.keep_audio);
        assert!(!config.overwrite);
    }

    #[test]
    fn test_config_merge() {
        let mut base = Config::default();
        base.format = OutputFormat::Vtt;
        base.model = WhisperModel::Medium;

        let other = Config {
            language: Some("zh".to_string()),
            keep_audio: true,
            ..Default::default()
        };

        let merged = base.merge(other);
        assert_eq!(merged.format, OutputFormat::Vtt);
        assert_eq!(merged.model, WhisperModel::Medium);
        assert_eq!(merged.language, Some("zh".to_string()));
        assert!(merged.keep_audio);
    }
}
