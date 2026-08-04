"""CRCLab 的 Nuitka 打包入口。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

from config.constants import Config
from config.paths import PACKAGE_ROOT

REMOVE_TEMP_FILES: bool = True
PROJECT_ROOT: Final[Path] = PACKAGE_ROOT
PROJECT_VENV_DIR_NAME: Final[str] = ".venv"
ICON_FILE_NAME: Final[str] = "app_icon.ico"
TEMP_BUILD_DIR_NAMES: Final[tuple[str, ...]] = ("main.build", "main.dist", "main.onefile-build")


def normalize_windows_version(raw_version: str) -> str:
    """将项目版本号规范化为 Windows 所需的四段纯数字格式。"""
    clean_version = raw_version.strip().lstrip("vV")
    parts = clean_version.split(".")
    if not clean_version or not 1 <= len(parts) <= 4 or any(not part.isdigit() for part in parts):
        raise ValueError(f"版本号必须是 1 至 4 段数字：{raw_version!r}")
    return ".".join([*parts, *("0" for _ in range(4 - len(parts)))])


def validate_project_layout(project_root: Path) -> None:
    """检查打包所需的入口文件和资源目录是否存在。"""
    entry_point = project_root / "main.py"
    resource_dir = project_root / "resources"
    icon_path = resource_dir / ICON_FILE_NAME
    if not entry_point.is_file():
        raise FileNotFoundError(f"找不到程序入口：{entry_point}")
    if not resource_dir.is_dir():
        raise FileNotFoundError(f"找不到资源目录：{resource_dir}")
    if not icon_path.is_file():
        raise FileNotFoundError(f"找不到 Windows 应用图标：{icon_path}")


def resolve_build_python(project_root: Path = PROJECT_ROOT) -> str:
    """解析项目虚拟环境解释器，禁止回退到全局 Python。"""
    project_root = project_root.resolve()
    if sys.platform == "win32":
        executable_path = project_root / PROJECT_VENV_DIR_NAME / "Scripts" / "python.exe"
    else:
        executable_path = project_root / PROJECT_VENV_DIR_NAME / "bin" / "python"
    if not executable_path.is_file():
        raise FileNotFoundError(f"打包必须使用项目虚拟环境，请先创建并安装构建依赖：{executable_path}")
    return str(executable_path)


def build_command(project_root: Path, version: str, python_executable: str | None = None) -> list[str]:
    """构造完整的 Nuitka 命令，不改变调用进程的当前目录。"""
    project_root = project_root.resolve()
    validate_project_layout(project_root)

    executable = python_executable or resolve_build_python(project_root)
    entry_point = project_root / "main.py"
    resource_dir = project_root / "resources"
    icon_path = resource_dir / ICON_FILE_NAME
    output_dir = project_root / "dist"

    return [
        executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        "--include-package=svglib",
        "--include-package=reportlab",
        f"--windows-icon-from-ico={icon_path}",
        "--windows-console-mode=disable",
        "--show-progress",
        "--company-name=CRCLab Studio",
        "--product-name=CRCLab",
        f"--file-version={version}",
        f"--product-version={version}",
        "--file-description=Real-time CRC calculation and division arc visualizer (CRCLab).",
        "--copyright=Copyright (C) 2026 CRCLab. All rights reserved.",
        f"--include-data-dir={resource_dir}=resources",
        f"--report={output_dir / 'nuitka-compilation-report.xml'}",
        f"--output-dir={output_dir}",
        "--output-filename=CRCLab.exe",
        str(entry_point),
    ]


def cleanup_temp_build_dirs(output_dir: Path) -> None:
    """只清理打包脚本明确创建的临时目录，并拒绝跟随目录外的链接。"""
    output_dir = output_dir.resolve()
    for name in TEMP_BUILD_DIR_NAMES:
        temp_dir = output_dir / name
        if not temp_dir.exists():
            continue

        resolved_temp_dir = temp_dir.resolve()
        if resolved_temp_dir.parent != output_dir:
            raise RuntimeError(f"拒绝清理输出目录之外的路径：{resolved_temp_dir}")
        shutil.rmtree(resolved_temp_dir)


def cleanup_failed_build(output_dir: Path) -> None:
    """清理失败构建留下的临时目录，保留编译报告供排错。"""
    if not REMOVE_TEMP_FILES:
        return
    try:
        cleanup_temp_build_dirs(output_dir)
    except (OSError, RuntimeError) as cleanup_error:
        print(f"  [WARNING] 清理失败构建目录时发生错误：{cleanup_error}")


def run_build() -> int:
    """执行打包流程，并返回可供 CI 使用的进程退出码。"""
    print("====== 开始执行 Nuitka 编译打包流程 ======")

    output_dir = PROJECT_ROOT / "dist"
    try:
        version = normalize_windows_version(Config.VERSION)
        command = build_command(PROJECT_ROOT, version)
        print(f"打包解释器：{command[0]}")
        print(f"执行编译命令:\n{subprocess.list2cmdline(command[2:])}\n")
        subprocess.run(command, check=True, cwd=PROJECT_ROOT)
    except ValueError as error:
        print(f"\n[ERROR] 打包配置无效：{error}")
        cleanup_failed_build(output_dir)
        return 1
    except FileNotFoundError as error:
        print(f"\n[ERROR] 打包输入缺失：{error}")
        cleanup_failed_build(output_dir)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"\n[ERROR] 打包失败，错误码：{error.returncode}")
        cleanup_failed_build(output_dir)
        return error.returncode or 1
    except OSError as error:
        print(f"\n[ERROR] 无法启动或执行打包流程：{error}")
        cleanup_failed_build(output_dir)
        return 1

    print("\n====== 打包成功！产物位于 dist 目录 ======")

    if REMOVE_TEMP_FILES:
        print("\n====== 开始清理临时构建目录 ======")
        try:
            cleanup_temp_build_dirs(output_dir)
        except (OSError, RuntimeError) as error:
            print(f"  [ERROR] 清理临时目录失败：{error}")
            return 1
        print("====== 清理完成 ======")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_build())
