class Config:
    """
    静态配置与样式常量中心。
    
    集中管理应用程序的所有静态数据，包括配色方案、界面文本、布局比例、
    默认业务参数以及字体配置。通过修改此类，可以快速调整 UI 风格和默认行为。
    """
    
    # 默认配色方案：采用现代化的柔和色调
    DEFAULT_COLORS = {
        'digit_color': "#000000",      # 标准数字颜色（主要用于被除数和商）
        'bg_block_color': "#f3f4f6",   # 补零区域的背景块颜色（淡灰色）
        'bg_digit_color': "#000000",   # 补零区域内的数字颜色
        'line_color': "#374151",       # 除法横线、弧线及边框颜色
        'sheet_bg_color': "#ffffff",   # 模拟纸张的背景底色
        'canvas_bg_color': "#d1d5db"   # 绘图区域最底层的背景色
    }

    # 系统界面配色：定义窗口底色、组件背景与状态高亮联动
    COLORS = {
        'main_bg': "#f3f4f6",           # 主窗口底色
        'sidebar_bg': "#ffffff",        # 侧边栏容器背景
        'sidebar_title_fg': "#1e293b",  # 侧边栏主标题颜色
        'primary': "#3b82f6",           # 品牌主色调（高亮勾选框、主按钮）
        'primary_active': "#2563eb",    # 主色调激活/悬停态
        'divider': "#e5e7eb",           # 分割线颜色
        'btn_default_bg': "#f8fafc",    # 常规小按钮背景色
        'border_enabled': "#cbd5e1",    # 色块启用状态边框色
        'border_disabled': "#f3f4f6",   # 色块禁用状态边框色
        'fg_enabled': "#000000",        # 启用态文字前景色
        'fg_disabled': "#cbd5e1",       # 禁用态文字置灰前景色
        'canvas_default_bg': "#d1d5db", # 主画布默认背景色
        'toolbar_bg': "#ffffff",        # 画布工具栏背景
        'zoom_btn_bg': "#f8fafc",       # 缩放按钮背景色
        'toolbar_divider': "#e2e8f0",   # 工具栏垂直分割线背景
        'preview_canvas_bg': "#ffffff",  # 导出预览画布背景色
        'preview_canvas_border': "#cbd5e1", # 导出预览画布边框高亮色
        'dir_lbl_fg': "#64748b",        # 导出目录路径文字灰色
        'cancel_bg': "#ef4444",         # 取消按钮高雅红
        'export_btn_bg': "#10b981",     # 开始导出翡翠绿
    }

    # 静态提示信息与弹窗文案集合
    MESSAGES = {
        'warning_title_invalid': "输入无效",
        'warning_empty': "数据位和多项式不能为空！",
        'warning_title_format': "格式错误",
        'warning_invalid_binary': "请输入有效的二进制字符串 (仅限 0 和 1)！",
        'warning_title_algo': "算法限制",
        'warning_poly_first_bit_1': "多项式首位必须为 1 才能进行有效的 CRC 除法计算。",
        'warning_poly_len_min_2': "多项式长度至少需为 2 位。",
        'error_title_custom_dir': "选择路径错误",
        'warning_custom_dir_empty': "已选择“自定义目录”，但尚未通过“浏览目录”按钮指定具体导出路径。",
        'export_success_title': "导出成功",
        'export_success_body': "图表已成功导出至：\n",
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
    
    # 界面文本配置：集中管理所有 UI 标签，方便国际化或快速文案调整
    UI_TEXT = {
        'title': "CRC 长除法解析与验证工具",
        'data_label': "数据位:",
        'poly_label': "多项式:",
        'gray_toggle': "显示补零标记",
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
        'btn_generate': "生成解析图",
        'btn_reset_color': "恢复默认配色",
        'btn_fit': "适应屏幕",
        'btn_reset_view': "重置比例",
        'btn_reset_params': "恢复默认参数",
        'canvas_ctrl': "画布控制:",
        'sidebar_title': "功能配置",
        'style_section': "排版布局参数:",
        'hint_scroll': "*实时拖动滑块调整视图",
        
        # 主界面配色标签说明文字
        'btn_export': "导出图表",
        'label_bg_block_color': "补零区域背景块:",
        'label_bg_digit_color': "补零标记文字色:",
        'label_digit_color': "除数被除数数字:",
        'label_line_color': "长除除线及弧线:",
        'label_sheet_bg_color': "图表纸张底版色:",
        'label_canvas_bg_color': "主窗口画布底层:",
        
        # 导出对话框文字
        'export_title': "导出图表",
        'export_preview': "导出预览",
        'export_params': "导出参数",
        'export_format': "格式",
        'export_quality': "画质",
        'export_dpi': "DPI",
        'export_color': "颜色",
        'export_show_border': "显示纸张边框",
        'export_dir': "导出目录",
        'export_btn_browse': "浏览目录",
        'export_info_group': "导出估算信息",
        'export_width_placeholder': "导出宽度: -- 像素",
        'export_height_placeholder': "导出高度: -- 像素",
        'export_size_placeholder': "预估大小: -- KB",
        'btn_cancel': "取消",
        'btn_start_export': "开始导出",
        'dialog_pick_dir_title': "选择导出目录",
    }

    # 界面组件布局参数：精确控制侧边栏和控件的样式
    LAYOUT = {
        'side_ratio': 0.28,      # 侧边栏占据窗口宽度的比例 (28%)
        'min_side_width': 400,   # 侧边栏最小宽度保证
        'input_padx': 20,        # 输入区域水平内边距
        'input_pady': 20,        # 输入区域垂直内边距
        'slider_len': 22,        # 滑块自身的物理长度
        'slider_thick': 22,      # 滑块轨道的垂直厚度
        'check_size': 20,        # 自定义复选框的尺寸
        'check_color': "#3b82f6",# 复选框激活时的蓝色调
        'entry_pady': 15,        # 输入框组件之间的外部间距
        'entry_ipady': 8,        # 输入框内部垂直厚度 (Internal Padding)
        'btn_pady': 8,           # 按钮组件之间的外部间距
        'btn_ipady': 8,          # 按钮内部垂直厚度
        'section_pady': 25,      # 各个逻辑功能区之间的垂直间距
        'canvas_bg': "#1e293b",  # 画布容器的背景（暗色调）
        'toolbar_bg': "#ffffff", # 工具栏背景
        'toolbar_opacity': 0.9,  # 工具栏透明度
        'export_dialog_w_ratio': 0.88,  # 导出对话框对物理屏幕宽度的占比
        'export_dialog_h_ratio': 0.88,  # 导出对话框对物理屏幕高度的占比
        'export_side_width': 450,        # 导出侧边控制栏宽度
        'export_preview_bg': "#f8fafc",  # 导出预览区背景底色
        'export_ctrl_bg': "#ffffff",     # 导出参数控制区背景底色
        
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
        'export_max_w': 1560,            # 导出对话框物理宽度上限
        'export_max_h': 980,             # 导出对话框物理高度上限
        'export_min_w': 1200,            # 导出对话框最小物理宽度
        'export_min_h': 750,             # 导出对话框最小物理高度
        
        # SSAA 抗锯齿物理渲染控制参数
        'temp_canvas_base': 2500,        # SSAA 公式临时高分画布基准大小
        'draw_origin_offset': 600.0,     # SSAA 渲染的原点安全偏置
        'ssaa_factor': 2,                # SSAA 抗锯齿超采样因子
        'curve_segments': 40,            # 除法左侧贝塞尔曲线分段数
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
        'show_gray': True        # 默认开启补零标记
    }

    # 默认导出配置参数表：统一控制初始业务值
    EXPORT_VALUES = {
        'format': "png",                          # 默认物理导出格式
        'quality': "标清默认尺寸1倍",             # 默认物理画面缩放倍数
        'dpi': 96,                                # 默认物理 DPI 密度
        'color': "彩色",                          # 默认物理导出色彩模式
        'show_border': False,                      # 默认是否绘制纸张框线
        'dir_mode': "当前目录（导出结果）",       # 默认存储目标目录类型
        'custom_dir': ""                          # 默认自定义目录初始值
    }

    # 导出下拉菜单的可选参数元数据集合
    EXPORT_OPTIONS = {
        'formats': ["png", "jpg", "svg"],
        'qualities': [
            "标清默认尺寸", "标清默认尺寸1倍", "标清默认尺寸2倍",
            "标清默认尺寸3倍", "高清默认尺寸1倍", "高清默认尺寸2倍"
        ],
        'dpis': [72, 96, 150, 200, 300, 600],
        'colors': ["彩色", "灰度", "黑白"],
        'dir_modes': ["当前目录（导出结果）", "自定义目录"]
    }

    # 字体配置：定义不同用途的字体族
    FONTS = {
        'zh_bold': ("SimSun", 11, "bold"),   # 中文标题加粗
        'zh_normal': ("SimSun", 11),         # 中文正文
        'en_main': ("Times New Roman", 12),   # 核心数据（建议使用衬线体模拟数学公式感）
        
        # 扩展 UI 通用组件字体
        'combo': ("SimSun", 10),                 # 下拉选择框字体
        'side_title': ("SimSun", 16, "bold"),    # 侧边栏主标题字体
        'btn_small': ("SimSun", 9),              # 侧边栏常规小按钮字体
        'btn_large_bold': ("SimSun", 11, "bold"),# 侧边栏深蓝大按钮/动作大按钮字体
        'zoom_btn': ("Arial", 12, "bold"),       # 顶部放大/缩小物理图标字体
        'zoom_lbl': ("Times New Roman", 11, "bold"), # 顶部比例显示字体
        'fallback_families': ["times.ttf", "times", "arial.ttf", "arial", "simsun.ttc", "simsun"], # 渲染器安全回退字体族列表
    }
