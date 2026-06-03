class Config:
    """
    静态配置与样式常量中心。
    
    集中管理应用程序的所有静态数据，包括配色方案、界面文本、布局比例、
    默认业务参数以及字体配置。通过修改此类，可以快速调整 UI 风格和默认行为。
    """
    
    # 软件版本定义
    VERSION = "v1.0.1"
    AUTHOR = "Qing90bing"
    COPYRIGHT = "© 2026 Qing90bing. All Rights Reserved."
    REPOSITORY = "https://github.com/Qing90bing/CRCLab"
    
    # 默认配色方案：采用现代化的柔和色调
    DEFAULT_COLORS = {
        'divisor_color': "#000000",    # 左侧除数数字颜色
        'quotient_color': "#000000",   # 顶部商数字颜色
        'dividend_color': "#000000",   # 其他主体部分（被除数、计算过程、余数）颜色
        'bg_block_color': "#f3f4f6",   # 补零区域的背景块颜色（淡灰色）
        'bg_digit_color': "#000000",   # 补零区域内的数字颜色
        'line_color': "#000000",       # 除法横线、弧线及边框颜色
        'sheet_bg_color': "#ffffff"    # 模拟纸张的背景底色
    }

    COLORS = {
        'main_bg': "#f3f4f6",           # 主窗口底色
        'sidebar_bg': "SystemButtonFace",        # 侧边栏容器背景
        'sidebar_title_fg': "#1e293b",  # 侧边栏主标题颜色
        'primary': "#3b82f6",           # brand主色调（高亮勾选框、主按钮）
        'divider': "#e5e7eb",           # 分割线颜色
        'border_enabled': "#cbd5e1",    # 色块启用状态边框色
        'border_disabled': "#f3f4f6",   # 色块禁用状态边框色
        'fg_enabled': "#000000",        # 启用态文字前景色
        'fg_disabled': "#cbd5e1",       # 禁用态文字置灰前景色
        'canvas_default_bg': "#d1d5db", # 主画布默认背景色
        'toolbar_bg': "#ffffff",        # 画布工具栏背景
        'toolbar_divider': "#e2e8f0",   # 工具栏垂直分割线背景
        'preview_canvas_bg': "#ffffff",  # 导出预览画布背景色
        'preview_canvas_border': "#cbd5e1", # 导出预览画布边框高亮色
        'dir_lbl_fg': "#64748b",        # 导出目录路径文字灰色
        'dashboard_bg': "#ffffff",      # 解析看板背景色
        'dashboard_card_bg': "#ffffff", # 解析看板卡片背景色
        'dashboard_card_border': "#e2e8f0", # 看板卡片边框色
        'text_muted': "#64748b",        # 置灰/次要文字颜色
        'text_dark': "#1e293b",         # 加黑/主要文字颜色
        'frame_highlight': "#ef4444",   # 最终发送帧校验码高亮色 (红色)
    }

    MESSAGES = {
        'warning_title_invalid': "输入无效",
        'warning_empty': "数据位和多项式不能为空！",
        'warning_title_format': "格式错误",
        'warning_invalid_binary': "请输入有效的二进制字符串 (仅限 0 和 1)！",
        'warning_title_algo': "算法限制",
        'warning_poly_first_bit_1': "多项式首位必须为 1 才能进行有效的 CRC 除法计算。",
        'warning_poly_len_min_2': "多项式长度至少需为 2 位。",
        'warning_custom_dir_empty': "已选择“自定义目录”，但尚未通过“浏览目录”按钮指定具体导出路径。",
        'warning_invalid_filename': "导出文件名不合格！\n文件名不能为空，且不能包含以下字符：\\ / : * ? \" < > |",
        'export_fail_title': "导出失败",
        'export_fail_body': "导出过程中发生错误，请按以下信息排查：\n\n1) 错误类型: {error_type}\n2) 错误详情: {error_msg}\n3) 建议排查: 请确认目录写入权限或导出参数是否有效。",
    }

    # 标准多项式库：预设常用的 CRC 标准以便用户快速选择
    STD_POLYS = {
        "自定义": "",
        "CRC-4 (10011)": "10011",
        "CRC-8 (100000111)": "100000111",
        "CRC-16-CCITT (10001000000100001)": "10001000000100001",
        "CRC-32 (100000100110000010001110110110111)": "100000100110000010001110110110111"
    }

    # 布局基准：定义单个字符单元格的基础像素大小
    GRID_BASE = 35
    DEFAULT_FONT_SIZE = 22
    
    UI_TEXT = {
        'title': f"CRCLab 循环冗余校验解析与验证工具 {VERSION}",
        'data_label': "数据位:",
        'poly_label': "多项式:",
        'font_size': "文字大小:",
        'h_spacing': "字符间距:",
        'v_spacing': "行间距:",
        'line_width': "线条粗细:",
        'padding': "边距留白:",
        'ext_left': "主横线左延伸:",
        'ext_right': "主横线右延伸:",
        'span_left': "弧线左跨度:",
        'span_right': "弧线右偏移:",
        'color_section': "配色方案:",
        'btn_reset_color': "恢复默认配色",
        'btn_zoom_in': "＋ 放大",
        'btn_zoom_out': "－ 缩小",
        'btn_drag': "✋ 拖动",
        'btn_reset_view': "⛶ 100%",
        'btn_fit': "▢ 适应窗口",
        'btn_reset_params': "恢复默认参数",
        'sidebar_title': "功能配置",
        'input_section': "基础数据配置:",
        'style_section': "排版布局参数:",
        
        # 主界面配色标签说明文字
        'btn_export': "导出图表",
        'label_bg_block_color': "补零区域背景块:",
        'label_bg_digit_color': "补零标记文字色:",
        'label_divisor_color': "左侧除数颜色:",
        'label_quotient_color': "顶部商颜色:",
        'label_dividend_color': "主体数字颜色:",
        'label_line_color': "长除除线及弧线:",
        'label_sheet_bg_color': "图表纸张底版色:",
        
        # 导出对话框文字
        'export_title': "导出图表",
        'export_preview': "图表预览",
        'export_params': "导出参数",
        'export_spec_group': "导出规格",
        'export_output_group': "输出选项",
        'export_format': "格式",
        'export_quality': "像素倍率",
        'export_dpi': "DPI",
        'export_jpg_quality': "质量",
        'export_color': "颜色",
        'export_show_border': "导出带黑色边框",
        'export_filename': "导出文件名",
        'export_dir': "导出目录",
        'export_btn_browse': "浏览目录",
        'export_info_group': "预估信息",
        'export_width_placeholder': "导出宽度： -- 像素",
        'export_height_placeholder': "导出高度： -- 像素",
        'export_size_placeholder': "预估大小： -- KB",
        'btn_cancel': "取消",
        'btn_start_export': "开始导出",
        'dialog_pick_dir_title': "选择导出目录",

        # 解析看板文字
        'dashboard_title': "实时运算结果解析看板",
        'card_input_title': "输入特征分析",
        'card_stats_title': "运算步骤统计",
        'card_checksum_title': "校验输出结果",
        'card_frame_title': "发送数据帧",
        
        # 关于软件相关文本
        'btn_about': "关于软件",
        'about_title': "关于 CRCLab",
    }

    # 界面组件布局参数：精确控制侧边栏和控件的样式
    LAYOUT = {
        'side_ratio': 0.32,      # 侧边栏占据窗口宽度的比例 (30%)
        'min_side_width': 400,   # 侧边栏最小宽度保证
        'input_padx': 20,        # 输入区域水平内边距
        'input_pady': 20,        # 输入区域垂直内边距
        'check_size': 20,        # 自定义复选框的尺寸
        'check_color': "#3b82f6",# 复选框激活时的蓝色调
        'canvas_bg': "#1e293b",  # 画布容器的背景（暗色调）
        'export_dialog_w_ratio': 0.75,   # 导出对话框对物理屏幕宽度的占比
        'export_dialog_h_ratio': 0.75,   # 导出对话框对物理屏幕高度的占比
        'export_side_width': 540,        # 导出侧边控制栏宽度
        
        # 物理主窗口几何比例常数
        'window_w_ratio': 0.95,          # 启动窗口对屏幕宽度的占比
        'window_h_ratio': 0.95,          # 启动窗口对屏幕高度的占比
        'window_max_w': 1920,            # 启动窗口最大物理宽度
        'window_max_h': 1080,            # 启动窗口最大物理高度
        'window_min_w': 1200,            # 最小宽度限制
        'window_min_h': 800,             # 最小高度限制
        'side_scroll_offset': 25,        # 侧边栏滚动条补偿宽度偏移
        'side_divider_width': 200,       # 侧边栏分割线几何宽度
        'zoom_in_factor': 1.1,           # 物理放大步长因子
        'zoom_out_factor': 0.9,          # 物理缩小步长因子
        'zoom_min': 0.1,                 # 视角缩放最小值
        'zoom_max': 10.0,                # 视角缩放最大值
        
        # 导出弹窗及物理像素边界
        'export_min_w': 900,             # 导出对话框最小物理宽度
        'export_min_h': 600,             # 导出对话框最小物理高度
        
        # SSAA 抗锯齿物理渲染控制参数
        # SSAA 抗锯齿物理渲染控制参数
        'ssaa_factor': 2,                # SSAA 抗锯齿超采样因子
        'curve_segments': 200,            # 贝塞尔曲线分段数（提高采样数以减少矢量曲线导出时的锯齿感）
        
        # 自定义色彩块拾色按钮物理尺寸，调大以方便用户点击
        'color_swatch_w': 80,           # 色彩拾色块物理宽度
        'color_swatch_h': 30,            # 色彩拾色块物理高度
        
        # 导出成功提示弹窗的尺寸与边距参数
        'success_dialog_min_w': 640,     # 导出成功弹窗最小宽度
        'success_dialog_h_offset': 15,   # 导出成功弹窗高度底部偏置
        'success_dialog_pad': 30,        # 弹窗内边距 (Padding)
        'success_icon_size': 64,         # 成功圆勾徽章的物理大小
        
        # 关于软件对话框参数
        'about_dialog_w': 580,           # 关于软件弹窗最小宽度
        'about_dialog_h': 500,           # 关于软件弹窗最小高度
        'about_logo_w': 300,             # 关于软件弹窗 Logo 宽度
        'about_logo_h': 90,              # 关于软件弹窗 Logo 高度
        
        # 主窗口浮动工具栏及画布交互控制参数
        'toolbar_y_offset': 35,          # 浮动工具栏的 y 轴偏移量
        'toolbar_padding_x': 16,         # 工具栏内部水平 Padding
        'toolbar_padding_y': 8,          # 工具栏内部垂直 Padding
        'toolbar_divider_padx': 14,      # 分割线水平间距
        'toolbar_divider_height': 24,    # 分割线高度
        'render_debounce_ms': 15,        # 图像生成主防抖延迟时间 (毫秒)
        'canvas_scroll_bound': 2000,     # 画布无限滚动范围的物理边界半宽
        'zoom_mousewheel_max': 5.0,      # 鼠标滚轮缩放的最大上限
        'default_screen_width_fallback': 1600, # 屏幕尺寸获取失败时的宽度默认备用值
        
        # 解析看板布局参数
        'dashboard_height': 220,         # 看板整体高度
        'card_gap': 12,                  # 卡片之间的间隔
    }

    # 默认业务参数配置表：程序启动时的初始状态
    DEFAULT_VALUES = {
        'data': "110101",        # 默认数据位
        'divisor': "1011",       # 默认多项式
        'font_size': 38,         # 默认字体大小
        'h_spacing': 1.2,        # 默认水平间距倍数
        'v_spacing': 1.4,        # 默认垂直间距倍数
        'line_width': 2,         # 默认线宽
        'padding': 30,           # 默认外边距
        'ext_left': 0,           # 线条左端延伸
        'ext_right': 0,          # 线条右端延伸
        'span_left': -0.5,       # 弧线跨度调整
        'span_right': 0.0,       # 弧线位置偏移
        'bold_zeros': False,     # 补零标记加粗
        'bold_divisor': False,   # 左侧除数加粗
        'bold_quotient': False,  # 顶部商加粗
        'bold_dividend': False   # 主体数字加粗
    }

    # 默认导出配置参数表：统一控制初始业务值
    EXPORT_VALUES = {
        'filename': "crc_export",                 # 默认导出文件名
        'format': "png",                          # 默认物理导出格式
        'quality': "默认尺寸",                # 默认物理画面缩放倍数
        'jpg_quality': 80,                         # 默认 JPG 压缩质量
        'dpi': 300,                                # 默认物理 DPI 密度
        'color': "彩色",                          # 默认物理导出色彩模式
        'show_border': False,                      # 默认是否绘制纸张框线
        'dir_mode': "当前目录（导出结果）",       # 默认存储目标目录类型
        'custom_dir': ""                          # 默认自定义目录初始值
    }

    # 导出下拉菜单的可选参数元数据集合
    EXPORT_OPTIONS = {
        'formats': ["png", "jpg", "svg", "pdf", "emf"],
        'qualities': [
            "默认尺寸", "默认尺寸2倍",
            "默认尺寸3倍", "默认尺寸4倍"
        ],
        'dpis': [72, 96, 150, 200, 300, 600, 1200],
        'colors': ["彩色", "灰度", "黑白"],
        'dir_modes': ["当前目录（导出结果）", "自定义目录"]
    }

    FONTS = {
        'zh_bold': ("SimSun", 10, "bold"),   # 中文标题加粗
        'zh_normal': ("SimSun", 10),         # 中文正文
        'en_main': ("Times New Roman", 10),   # 核心数据字体，采用衬线体以模拟公式样式
        
        # 扩展 UI 通用组件字体
        'side_title': ("SimSun", 12, "bold"),    # 侧边栏主标题字体
        'combo': ("SimSun", 10),                 # 下拉选择框字体
        'btn_small': ("SimSun", 10),              # 侧边栏常规小按钮字体
        'zoom_btn': ("Times New Roman", 12, "bold"),       # 缩放控制按钮字体
        'zoom_lbl': ("Times New Roman", 10, "bold"),       # 顶部比例显示字体
        'fallback_families': ["times.ttf", "times", "simsun.ttc", "simsun"], # 字体回退列表
        'gdi_family': "Times New Roman",         # Windows GDI 矢量导出默认字体
    }

    # GDI 矢量绘制配置参数
    GDI = {
        'bk_transparent': 1,           # GDI SetBkMode 背景透明 (TRANSPARENT)
        'ta_center_baseline': 30,      # GDI 文本水平及基线对齐标志
        'null_brush': 5,               # GDI NULL_BRUSH 空画刷
        'null_pen': 8,                 # GDI NULL_PEN 空画笔
        'ps_solid': 0,                 # GDI PS_SOLID 实线画笔样式
        'fw_normal': 400,              # GDI FW_NORMAL 普通字宽
        'default_charset': 1,          # GDI DEFAULT_CHARSET 默认字符集
        'antialiased_quality': 4,      # GDI ANTIALIASED_QUALITY 高级抗锯齿字体品质
        'baseline_offset_ratio': 0.33, # GDI 文本垂直基线对齐微调比率
    }
