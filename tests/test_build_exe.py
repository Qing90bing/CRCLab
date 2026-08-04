import subprocess
from pathlib import Path

import pytest

import build_exe


def test_normalize_windows_version():
    assert build_exe.normalize_windows_version("v1.2.3") == "1.2.3.0"
    assert build_exe.normalize_windows_version("2") == "2.0.0.0"


@pytest.mark.parametrize("version", ["", "v1.a.0", "1.2.3.4.5"])
def test_normalize_windows_version_rejects_invalid_versions(version):
    with pytest.raises(ValueError):
        build_exe.normalize_windows_version(version)


def test_build_command_uses_project_relative_inputs():
    command = build_exe.build_command(build_exe.PROJECT_ROOT, "1.2.3.0", python_executable="python")

    assert command[0:3] == ["python", "-m", "nuitka"]
    assert command[-1] == str(build_exe.PROJECT_ROOT / "main.py")
    assert f"--output-dir={build_exe.PROJECT_ROOT / 'dist'}" in command
    assert f"--include-data-dir={build_exe.PROJECT_ROOT / 'resources'}=resources" in command
    assert f"--windows-icon-from-ico={build_exe.PROJECT_ROOT / 'resources' / 'app_icon.ico'}" in command


def test_resolve_build_python_prefers_project_virtualenv(tmp_path):
    executable = tmp_path / ".venv" / "Scripts" / "python.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()

    assert build_exe.resolve_build_python(tmp_path) == str(executable)


def test_resolve_build_python_rejects_missing_project_virtualenv(tmp_path):
    with pytest.raises(FileNotFoundError, match="项目虚拟环境"):
        build_exe.resolve_build_python(tmp_path)


def test_run_build_returns_nuitka_exit_code_and_preserves_cwd(monkeypatch):
    original_cwd = Path.cwd()
    monkeypatch.setattr(build_exe, "REMOVE_TEMP_FILES", False)

    def fail_build(command, **kwargs):
        assert kwargs["cwd"] == build_exe.PROJECT_ROOT
        raise subprocess.CalledProcessError(returncode=23, cmd=command)

    monkeypatch.setattr(build_exe.subprocess, "run", fail_build)

    assert build_exe.run_build() == 23
    assert Path.cwd() == original_cwd


def test_run_build_returns_one_when_process_cannot_start(monkeypatch):
    monkeypatch.setattr(build_exe, "REMOVE_TEMP_FILES", False)

    def fail_to_start(*args, **kwargs):
        raise OSError("not found")

    monkeypatch.setattr(build_exe.subprocess, "run", fail_to_start)

    assert build_exe.run_build() == 1


def test_cleanup_removes_only_known_temporary_directories(tmp_path):
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    for name in build_exe.TEMP_BUILD_DIR_NAMES:
        (output_dir / name).mkdir()
    unrelated = output_dir / "keep.txt"
    unrelated.touch()

    build_exe.cleanup_temp_build_dirs(output_dir)

    assert unrelated.exists()
    assert all(not (output_dir / name).exists() for name in build_exe.TEMP_BUILD_DIR_NAMES)
