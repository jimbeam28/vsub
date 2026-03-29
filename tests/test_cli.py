"""CLI 模块测试"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from vsub.cli import cli, init_config, main
from vsub.config import Config


class TestCli:
    """CLI 测试"""

    def test_cli_help(self):
        """测试帮助信息"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "视频字幕生成工具" in result.output
        assert "-o, --output" in result.output
        assert "-l, --language" in result.output

    def test_cli_version(self):
        """测试版本信息"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "vsub" in result.output
        assert "0.2.0" in result.output

    def test_cli_no_input(self):
        """测试无输入文件"""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 1
        assert "请提供输入视频文件" in result.output

    def test_cli_nonexistent_file(self):
        """测试不存在的文件"""
        runner = CliRunner()
        result = runner.invoke(cli, ["/nonexistent/video.mp4"])
        assert result.exit_code == 2  # Click 的路径验证错误

    def test_cli_init(self, tmp_path):
        """测试 --init 命令"""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["--init"])
            assert result.exit_code == 0
            assert "配置文件已生成" in result.output
            assert Path("vsub.yaml").exists()

    def test_cli_init_exists(self, tmp_path):
        """测试配置文件已存在"""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # 先创建配置文件
            Path("vsub.yaml").write_text("format: srt\n")
            # 模拟用户输入 "n"（不覆盖）
            result = runner.invoke(cli, ["--init"], input="n\n")
            assert result.exit_code == 0
            assert "已取消" in result.output

    @patch("vsub.cli.process_video")
    def test_cli_single_file(self, mock_process, tmp_path):
        """测试单文件处理"""
        # 创建模拟视频文件
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file)])

        assert result.exit_code == 0
        mock_process.assert_called_once()

    @patch("vsub.cli.process_videos")
    def test_cli_batch_files(self, mock_process, tmp_path):
        """测试批量处理"""
        # 创建多个模拟视频文件
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        video1.write_text("dummy")
        video2.write_text("dummy")

        mock_process.return_value = [
            (video1, tmp_path / "video1.srt"),
            (video2, tmp_path / "video2.srt"),
        ]

        runner = CliRunner()
        result = runner.invoke(cli, [str(video1), str(video2)])

        assert result.exit_code == 0
        mock_process.assert_called_once()
        assert "完成: 2/2" in result.output

    @patch("vsub.cli.process_video")
    def test_cli_batch_with_single_output(self, mock_process, tmp_path):
        """测试批量处理时指定单一输出"""
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        video1.write_text("dummy")
        video2.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video1), str(video2), "-o", "output.srt"])

        assert result.exit_code == 1
        assert "批量处理时不能指定单一输出文件" in result.output

    @patch("vsub.cli.process_video")
    def test_cli_with_format(self, mock_process, tmp_path):
        """测试指定格式"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "-f", "vtt"])

        assert result.exit_code == 0
        # 检查传入的参数
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.format.value == "vtt"

    @patch("vsub.cli.process_video")
    def test_cli_with_model(self, mock_process, tmp_path):
        """测试指定模型"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "-m", "medium"])

        assert result.exit_code == 0
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.model.value == "medium"

    @patch("vsub.cli.process_video")
    def test_cli_with_language(self, mock_process, tmp_path):
        """测试指定语言"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "-l", "zh"])

        assert result.exit_code == 0
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.language == "zh"

    @patch("vsub.cli.process_video")
    def test_cli_keep_audio(self, mock_process, tmp_path):
        """测试 --keep-audio"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "--keep-audio"])

        assert result.exit_code == 0
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.keep_audio is True

    @patch("vsub.cli.process_video")
    def test_cli_overwrite(self, mock_process, tmp_path):
        """测试 --overwrite"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "--overwrite"])

        assert result.exit_code == 0
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.overwrite is True

    @patch("vsub.cli.process_video")
    def test_cli_output_path(self, mock_process, tmp_path):
        """测试指定输出路径"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")
        output_path = tmp_path / "output" / "subtitle.srt"

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "-o", str(output_path)])

        assert result.exit_code == 0
        call_args = mock_process.call_args
        config = call_args[0][1]
        assert config.output_dir == output_path.parent

    @patch("vsub.cli.process_video")
    def test_cli_verbose(self, mock_process, tmp_path):
        """测试 --verbose"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file), "-v"])

        assert result.exit_code == 0

    @patch("vsub.cli.process_video")
    def test_cli_error_handling(self, mock_process, tmp_path):
        """测试错误处理"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy")

        mock_process.side_effect = RuntimeError("处理失败")

        runner = CliRunner()
        result = runner.invoke(cli, [str(video_file)])

        assert result.exit_code == 1
        assert "错误: 处理失败" in result.output


class TestInitConfig:
    """配置初始化测试"""

    def test_init_config_creates_file(self, tmp_path, monkeypatch):
        """测试生成配置文件"""
        monkeypatch.chdir(tmp_path)

        init_config()

        config_file = tmp_path / "vsub.yaml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "format: srt" in content
        assert "model: base" in content

    def test_main_entry(self):
        """测试主入口"""
        with patch("vsub.cli.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()
