# CRC Visualizer (CRC 循环冗余校验计算与可视化工具)

## 1. 软件概述
`CRC Visualizer` 是一款基于 Python 与 Tkinter 开发的 CRC（循环冗余校验）长除法计算与可视化辅助工具。本程序支持常用的标准生成多项式（如 CRC-4、CRC-8、CRC-16、CRC-32）以及自定义多项式的模二除法演算，并以图形化形式（包含余数长除式及关联圆弧图）展示计算过程，方便学习与协议分析。

系统支持将生成的图表导出为 `PNG`、`JPG`、`SVG`、`PDF` 以及 Windows 原生的 `EMF` 矢量图元格式，便于在文档、报告中进行排版和配图。

为了方便分发与部署，项目提供了基于 **Nuitka** 的打包脚本，支持将 Python 源码编译为无 Python 环境依赖的独立 Windows 可执行程序（`.exe`）。

---

## 2. 系统运行环境与核心依赖

### 2.1 基础环境
- **操作系统**：Windows 10/11 (x64)
- **运行要求**：Python 3.10 或更高版本

### 2.2 依赖包清单
运行及编译本程序需要安装以下第三方依赖项：
- **Pillow** (`>= 10.0.0`)：负责底层的内存图像生成与图解渲染。
- **svglib** (`>= 1.5.0`)：用于将 SVG 格式转换为 ReportLab 绘图对象。
- **reportlab** (`>= 4.0.0`)：用于生成 PDF 文件。
- **nuitka** (`>= 2.0`)：用于将 Python 代码编译并打包为 exe 可执行程序（仅打包需要）。
- **zstandard** (`>= 0.15.0`)：用于压缩打包后的二进制文件（仅打包需要）。

---

## 3. 安装与本地运行

建议在 Python 虚拟环境中进行本地开发与调试运行：

1. **进入项目根目录**：
   ```powershell
   cd e:\My_Project\CRC_visualizer
   ```

2. **创建并激活虚拟环境**：
   ```powershell
   # 创建虚拟环境
   python -m venv .venv

   # 激活虚拟环境
   .venv\Scripts\Activate.ps1
   ```

3. **安装依赖包**（若遇到 Windows 环境下虚拟环境激活失效，建议使用强力命令强制写入）：
   ```powershell
   # 常规安装命令
   pip install nuitka zstandard Pillow svglib reportlab
   
   # 【推荐：防环境变量污染强力命令】
   .\.venv\Scripts\python.exe -m pip install nuitka zstandard Pillow svglib reportlab
   ```

4. **运行主程序**（若遇到运行错乱，建议使用专属解释器启动）：
   ```powershell
   # 常规运行命令
   python main.py
   
   # 【推荐：防环境变量污染强力命令】
   .\.venv\Scripts\python.exe main.py
   ```

---

## 4. 可执行程序打包指南

项目提供了打包脚本 `build_exe.py`。该脚本使用 Nuitka 提取项目依赖，并将图标资源、Windows 元数据（如版本号、版权声明、描述信息等）一同打包。

### 4.1 编译环境配置
Nuitka 在进行底层编译时需要调用 C++ 编译器。请在执行打包前确保系统已安装相应工具链：
- **推荐方案（MSVC 编译器）**：
  安装 [Visual Studio 2022 社区版](https://visualstudio.microsoft.com/zh-hans/downloads/)，并在安装引导中勾选 **“使用 C++ 的桌面开发”**。VS 安装引导将自动配置编译器环境。

### 4.2 执行打包构建
激活虚拟环境后，直接运行打包脚本：
```powershell
# 常规打包命令
python build_exe.py

# 【推荐：防环境变量污染强力命令】
.\.venv\Scripts\python.exe build_exe.py
```

### 4.3 构建结果说明
- **构建时长**：由于 Nuitka 需要将代码编译为 C++ 并进行编译优化，通常需要 2 至 5 分钟。
- **发布产物**：构建完成后，会在根目录下生成 `dist` 文件夹，其中的 `CRC_Visualizer.exe` 即可作为无 Python 环境依赖的独立程序分发。程序内已包含了运行时所需的静态资源及 PDF、EMF 导出库。

---

## 5. 项目目录结构

```text
CRC_visualizer/
├── core/                # 算法运算核心模块
│   └── engine.py        # 二进制模二除法核心计算引擎
├── view/                # 界面展现与绘制控制层
│   ├── renderer.py      # Pillow 内存矢量化图解高清重绘器
│   ├── sidebar.py       # GUI 参数控制及排版布局侧边栏面板
│   ├── dashboard.py     # 实时运算分析及校验解析看板
│   ├── widgets.py       # 通用高阶定制 GUI 交互组件库 (包含滑块、拾色器等)
│   ├── export_dialog.py # 高精度导出参数配置与交互对话框 (弹窗外壳)
│   ├── export_form.py   # 导出参数控制及表单交互面板 (弹窗左侧栏)
│   ├── export_preview.py# 导出纸张效果动态实时预览画布 (弹窗右侧栏)
│   ├── exporter.py      # 高阶导出外观协调外观类 (Facade) 与分发管理中心
│   ├── success_dialog.py# 导出成功路径回显与气泡式交互弹窗
│   └── exporters/       # 插件化多格式导出底层适配扩展包
│       ├── __init__.py  # 导出器注册与模块暴露接口
│       ├── base.py      # 物理导出插件基础抽象类
│       ├── bitmap.py    # 位图格式 (PNG, JPG) 高分辨率渲染与大小评估插件
│       ├── svg.py       # SVG 高清晰矢量标记渲染网关插件
│       ├── pdf.py       # SVG-to-ReportLab PDF 物理写盘与矢量粗估插件
│       └── emf.py       # 基于 Windows GDI32 底层原生的 EMF 矢量图元插件
├── config/              # 常量与全局静态设置中心
│   └── constants.py     # 静态色彩、预设多项式、字体降级回退及布局参数定义
├── app_icon.ico         # 应用程序系统图标
├── app_icon.png         # 高清晰图片资源
├── build_exe.py         # Nuitka 自动化一键打包编译脚本
└── README.md            # 项目使用与部署说明文档 (本文档)
```

---

## 6. 技术架构说明与常见问题排查

### 6.1 静态资源路径解析机制（CWD 漂移防范）
- **技术问题**：在单文件 `.exe` 执行或从其他路径启动程序时，常规相对路径 `"app_icon.png"` 会因为当前工作目录（Current Working Directory）改变而无法被程序读取，导致图标回退为 Tkinter 默认的“羽毛”组件。
- **架构设计**：本程序在 `main.py` 的初始化逻辑中，采用基于 `__file__` 动态计算模块物理目录的绝对定位技术：
  ```python
  base_dir = os.path.dirname(os.path.abspath(__file__))
  icon_png = os.path.join(base_dir, "app_icon.png")
  ```
  该机制确保了程序在不同启动目录下运行时，均能正常加载图片资源。

### 6.2 导出 PDF 时提示 “PDF 依赖未就绪”
- **排查建议**：请确保虚拟环境中已成功执行 `pip install svglib reportlab`。打包时请使用项目自带的 `build_exe.py` 打包脚本，该脚本已配置包含声明，确保动态加载的依赖包被正常打入二进制文件中。

### 6.3 导出 EMF 提示 “估算失败” 或 导出的矢量文件报错
- **机制说明**：EMF 格式采用 Windows GDI32 底层增强图元拦截机制，目前仅支持在 Windows 系统下进行实时文件尺寸评估与无损写盘导出。
- **故障排除**：若估算发生异常，请检查并确认 `view/renderer.py` 中用于绘图渲染优化的圆角盖修补判定已收紧为同时校验 `hasattr(actual_draw, 'ellipse')`，以此避免在不支持 ellipse 接口的 EMF 拦截器上调用该方法导致报错。

### 6.4 运行打包时提示 “No module named nuitka” 但 pip 提示已安装
- **现象原因**：此现象属于 Windows 终端下常见的**虚拟环境激活半失效（环境变量污染）**故障。虽然终端左侧显示了 `(.venv)` 前缀，但执行 `pip install` 时却被系统定向到了全局 Python 路径（导致包被装在了全局），而运行打包脚本时使用了虚拟环境内部的解释器，从而因找不到模块报错。
- **解决方案**：无需重新配置终端，直接调用虚拟环境内特定路径的解释器进行显式包安装及打包编译即可解决：
  ```powershell
  # 强制安装依赖至虚拟环境中
  .\.venv\Scripts\python.exe -m pip install nuitka zstandard Pillow svglib reportlab
  
  # 强制使用虚拟环境下的解释器执行编译
  .\.venv\Scripts\python.exe build_exe.py
  ```

---

## 7. 技术支持与开发声明
本软件在编写、架构重构、性能调优以及打包故障诊断与修复的过程中，引入了 Google Gemini 智能 AI 编程辅助系统进行多轮协作编码、技术验证与缺陷排查。

