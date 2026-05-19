# -*- coding: utf-8 -*-
"""
CRC Visualizer - Nuitka 自动化一键打包脚本
"""
import os
import sys
import subprocess

def run_build():
    print("====== 🚀 开始执行 Nuitka 编译打包流程 ======")
    
    # 确保在项目根目录运行
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 动态从 config/constants.py 提取版本号以保持项目全局统一
    try:
        sys.path.insert(0, project_dir)
        from config.constants import Config
        raw_version = Config.VERSION
        # 清洗版本号，如 "v1.0.1" -> "1.0.1"
        clean_version = raw_version.lstrip('vV')
        # 补全为 Windows 必须的 4 位版本格式 (如 "1.0.1" -> "1.0.1.0")
        parts = clean_version.split('.')
        while len(parts) < 4:
            parts.append('0')
        version_str = '.'.join(parts[:4])
    except Exception:
        version_str = "1.0.1.0"
    
    # 检查静态资源是否存在
    icon_ico = "app_icon.ico"
    icon_png = "app_icon.png"
    
    extra_args = []
    if os.path.exists(icon_ico):
        extra_args.append(f"--windows-icon-from-ico={icon_ico}")
        extra_args.append(f"--include-data-files={icon_ico}={icon_ico}")
    if os.path.exists(icon_png):
        extra_args.append(f"--include-data-files={icon_png}={icon_png}")
        
    # 定义编译所用的主要参数
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",                      # 独立包模式
        "--onefile",                         # 生成单文件 .exe
        "--enable-plugin=tk-inter",          # 启用 Tkinter 适配插件
        "--include-package=svglib",          # 强制包含 PDF 转换包 svglib
        "--include-package=reportlab",       # 强制包含 PDF 物理渲染包 reportlab
        "--windows-console-mode=disable",    # 关闭 CMD 窗口
        "--show-progress",                   # 显示编译进度
        
        # Windows 版权与元数据注入
        "--company-name=CRC Studio",
        "--product-name=CRC Visualizer",
        f"--file-version={version_str}",
        f"--product-version={version_str}",
        "--file-description=Real-time CRC calculation and division arc visualizer.",
        "--copyright=Copyright © 2026 CRC Studio. All rights reserved.",
        
        # 输出路径设定
        "--output-dir=dist",
        "--output-filename=CRC_Visualizer.exe",
    ]
    
    # 拼接额外资源参数和入口文件
    nuitka_args.extend(extra_args)
    nuitka_args.append("main.py")
    
    print(f"执行编译命令:\n{' '.join(nuitka_args[2:])}\n")
    
    try:
        # 执行 Nuitka 编译命令
        result = subprocess.run(nuitka_args, check=True)
        if result.returncode == 0:
            print("\n====== 🎉 打包成功！产物位于 dist 目录 ======")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败，错误码: {e.returncode}")
    except FileNotFoundError:
        print("\n❌ 错误：未在当前环境中找到 Nuitka，请先激活虚拟环境并安装 Nuitka：\n   pip install nuitka zstandard")

if __name__ == "__main__":
    run_build()
