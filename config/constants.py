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
        'hint_scroll': "*实时拖动滑块调整视图"
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

    # 字体配置：定义不同用途的字体族
    FONTS = {
        'zh_bold': ("SimSun", 11, "bold"),   # 中文标题加粗
        'zh_normal': ("SimSun", 11),         # 中文正文
        'en_main': ("Times New Roman", 12)    # 核心数据（建议使用衬线体模拟数学公式感）
    }
