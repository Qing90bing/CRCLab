"""集中管理 CRCLab 的资源、运行目录和导出路径。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
RESOURCE_DIR_NAME: Final[str] = "resources"
EXPORT_DIR_NAME: Final[str] = "导出结果"

_INVALID_FILENAME_CHARS: Final[frozenset[str]] = frozenset('\\/:*?"<>|')
_RESERVED_WINDOWS_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


def resource_dir() -> Path:
    """返回随应用分发的静态资源目录。"""
    return PACKAGE_ROOT / RESOURCE_DIR_NAME


def resource_path(name: str) -> Path:
    """返回资源文件路径，并拒绝越过资源目录的相对路径。"""
    relative_path = Path(name)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"资源路径必须位于 {RESOURCE_DIR_NAME} 目录内：{name}")
    return resource_dir() / relative_path


def _compiled_containing_dir() -> Path | None:
    """读取 Nuitka 编译产物所在目录，普通 Python 运行时返回 None。"""
    compiled = globals().get("__compiled__")
    containing_dir = getattr(compiled, "containing_dir", None)
    if containing_dir:
        return Path(containing_dir).resolve()
    return None


def application_dir() -> Path:
    """返回应用外部文件所在目录，不依赖进程启动时的当前目录。"""
    compiled_dir = _compiled_containing_dir()
    if compiled_dir is not None:
        return compiled_dir

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return PACKAGE_ROOT


def default_export_dir() -> Path:
    """返回默认导出目录，开发运行和打包运行均相对应用目录确定。"""
    return application_dir() / EXPORT_DIR_NAME


def resolve_custom_dir(value: str | Path) -> Path:
    """解析用户指定的目录，相对路径以应用目录为基准。"""
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = application_dir() / candidate
    return candidate.resolve()


def is_safe_filename(value: str) -> bool:
    """判断文件名是否可以安全地作为导出文件的基础名称。"""
    name = value.strip()
    if not name or name in {".", ".."}:
        return False
    if name != Path(name).name or any(char in _INVALID_FILENAME_CHARS for char in name):
        return False
    if name.rstrip(" .") != name or any(ord(char) < 32 for char in name):
        return False

    windows_stem = name.split(".", 1)[0].upper()
    return windows_stem not in _RESERVED_WINDOWS_NAMES


def validate_filename(value: str) -> str:
    """校验并返回去除首尾空白的导出文件基础名称。"""
    name = value.strip()
    if not is_safe_filename(name):
        raise ValueError('文件名不能为空，且不能包含 \\ / : * ? " < > |')
    return name


def unique_export_path(export_dir: Path, filename: str, fmt: str) -> Path:
    """生成不覆盖已有文件的导出路径。"""
    base_name = validate_filename(filename)
    extension = fmt.strip().lstrip(".").lower()
    if not extension or not extension.isalnum():
        raise ValueError(f"导出格式无效：{fmt}")

    output_path = export_dir / f"{base_name}.{extension}"
    counter = 1
    while output_path.exists():
        output_path = export_dir / f"{base_name}_{counter}.{extension}"
        counter += 1
    return output_path
