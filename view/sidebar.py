import tkinter as tk
from tkinter import ttk
from config.constants import Config
from view.widgets import ModernCheckbutton, ModernScale, ColorSwatchRow

class SidebarPanel(tk.Frame):
    """
    侧边控制面板视图组件类。
    
    采用高内聚的组件级封装，负责滚动条侧边栏的外观搭建、
    所有的输入数据框、滑动条调节器、颜色配置项的绑定及状态变更监听。
    使用 view/widgets.py 定义的通用小部件以消除冗余。
    """
    def __init__(self, parent, app, width):
        """
        初始化侧边栏。
        :param parent: 容纳侧边栏的父容器。
        :param app: 主应用程序 CRCVisualizerApp 实例。
        :param width: 侧边栏物理宽度。
        """
        super().__init__(parent, bg=Config.COLORS['sidebar_bg'], width=width)
        self.app = app
        self.pack(side=tk.LEFT, fill=tk.Y)
        self.pack_propagate(False)
        
        # 1. 物理构建带滚动条的主体侧边容器
        self._build_scrollable_container(width)
        
        # 2. 构建各业务区
        self._init_input_section()
        self._init_style_section()
        self._init_color_section()

    def _build_scrollable_container(self, side_w):
        """ 物理构建带滚动条的响应式侧边栏容器框架 """
        self.side_canvas = tk.Canvas(self, bg=Config.COLORS['sidebar_bg'], highlightthickness=0)
        self.side_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.side_canvas.yview)
        
        scroll_w = side_w - Config.LAYOUT['side_scroll_offset']
        self.scrollable_frame = tk.Frame(self.side_canvas, bg=Config.COLORS['sidebar_bg'], width=scroll_w)
        
        self.side_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=scroll_w)
        
        # 绘制功能配置主标题及下方装饰性渐变底纹分割线
        tk.Label(self.scrollable_frame, text=Config.UI_TEXT['sidebar_title'], bg=Config.COLORS['sidebar_bg'], 
                 fg=Config.COLORS['sidebar_title_fg'], font=Config.FONTS['side_title']).pack(pady=(20, 10))
        tk.Frame(self.scrollable_frame, height=2, bg=Config.COLORS['primary'], width=Config.LAYOUT['side_divider_width']).pack(pady=(0, 20))
        
        # 绑定尺寸重构事件，实时同步更新滚动视区大小
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        )
        
        self.side_canvas.configure(yscrollcommand=self.side_scrollbar.set)
        self.side_scrollbar.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)

        # 鼠标移入自动绑定/移出解绑全局滚轮事件，优雅防止与主 Canvas 产生滚动冲突
        def _bind_mousewheel(event):
            self.side_canvas.bind_all("<MouseWheel>", lambda e: self.side_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        def _unbind_mousewheel(event):
            self.side_canvas.unbind_all("<MouseWheel>")
            
        self.bind("<Enter>", _bind_mousewheel)
        self.bind("<Leave>", _unbind_mousewheel)
        
        # 实例化内部配置容器
        self.inner_panel = tk.Frame(self.scrollable_frame, bg=Config.COLORS['sidebar_bg'], 
                                     padx=Config.LAYOUT['input_padx'], 
                                     pady=Config.LAYOUT['input_pady'])
        self.inner_panel.pack(fill=tk.BOTH, expand=True)

    def _init_input_section(self):
        """ 初始化数据位与生成多项式输入控制区 """
        parent = self.inner_panel
        
        # 1. 原始二进制数据位输入
        tk.Label(parent, text=Config.UI_TEXT['data_label'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        self.data_entry = ttk.Entry(parent, textvariable=self.app.data_var, font=Config.FONTS['en_main'])
        self.data_entry.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']), ipady=Config.LAYOUT['entry_ipady'])
        self.data_entry.bind("<Return>", lambda e: self.app.generate(auto_center=True))

        # 2. 生成多项式输入
        tk.Label(parent, text=Config.UI_TEXT['poly_label'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        pf = tk.Frame(parent, bg=Config.COLORS['sidebar_bg'])
        pf.pack(fill=tk.X, pady=(0, 5))
        self.poly_entry = ttk.Entry(pf, textvariable=self.app.divisor_var, font=Config.FONTS['en_main'])
        self.poly_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=Config.LAYOUT['entry_ipady'])
        self.poly_entry.bind("<Return>", lambda e: self.app.generate(auto_center=True))
        
        # 3. 标准预设多项式快速选择
        self.poly_combo = ttk.Combobox(parent, values=list(Config.STD_POLYS.keys()), state="readonly", font=Config.FONTS['btn_small'])
        self.poly_combo.set(list(Config.STD_POLYS.keys())[0])
        self.poly_combo.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']))
        self.poly_combo.bind("<<ComboboxSelected>>", self.app.on_poly_selected)

        # 4. 补零标记开关，使用 ModernCheckbutton 扁平化小部件
        self.show_gray_check = ModernCheckbutton(
            parent, 
            Config.UI_TEXT['gray_toggle'], 
            self.app.show_gray_var, 
            self.app.on_toggle_gray
        )
        self.show_gray_check.pack(anchor=tk.W, pady=(0, Config.LAYOUT['section_pady']))
        
        tk.Frame(parent, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=10)

    def _init_style_section(self):
        """ 初始化排版与长除法物理间距微调滑块区 """
        parent = self.inner_panel
        tk.Label(parent, text=Config.UI_TEXT['style_section'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
        
        # 排版微调控制滑块清单，统一使用 ModernScale 精美小部件构建
        styles = [
            (Config.UI_TEXT['font_size'], 10, 80, self.app.font_size_var, 1),
            (Config.UI_TEXT['h_spacing'], 0.5, 3.0, self.app.spacing_var, 0.1),
            (Config.UI_TEXT['v_spacing'], 0.5, 3.0, self.app.v_spacing_var, 0.1),
            (Config.UI_TEXT['line_width'], 1, 10, self.app.line_width_var, 1),
            (Config.UI_TEXT['padding'], 0, 200, self.app.padding_var, 1),
            (Config.UI_TEXT['ext_left'], -5.0, 0.0, self.app.line_ext_left_var, 0.1),
            (Config.UI_TEXT['ext_right'], 0.0, 5.0, self.app.line_ext_right_var, 0.1),
            (Config.UI_TEXT['span_left'], -2.0, -0.1, self.app.curve_span_left_var, 0.1),
            (Config.UI_TEXT['span_right'], -1.5, 1.5, self.app.curve_span_right_var, 0.1)
        ]
        
        self.scales = []
        for label, f, t, var, r in styles:
            scale = ModernScale(parent, label, f, t, var, resolution=r, command=lambda x: self.app.generate(auto_center=False))
            scale.pack(fill=tk.X, pady=(0, 2))
            self.scales.append(scale)
        
        # 参数一键恢复默认按钮
        ttk.Button(parent, text=Config.UI_TEXT['btn_reset_params'], command=self.app.reset_params).pack(fill=tk.X, pady=(5, Config.LAYOUT['section_pady']))

    def _init_color_section(self):
        """ 初始化多维色彩配置项，并在底部渲染最为尊贵、大气的“导出图表”大按钮 """
        parent = self.inner_panel
        tk.Label(parent, text=Config.UI_TEXT['color_section'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
        
        color_attrs = [
            ('bg_block_color', Config.UI_TEXT['label_bg_block_color']),
            ('bg_digit_color', Config.UI_TEXT['label_bg_digit_color']),
            ('digit_color', Config.UI_TEXT['label_digit_color']),
            ('line_color', Config.UI_TEXT['label_line_color']),
            ('sheet_bg_color', Config.UI_TEXT['label_sheet_bg_color']),
            ('canvas_bg_color', Config.UI_TEXT['label_canvas_bg_color'])
        ]
        
        self.color_rows = {}
        for attr, text in color_attrs:
            row = ColorSwatchRow(
                parent, 
                text, 
                attr, 
                initial_color=getattr(self.app, attr), 
                on_click_callback=self.app.pick_color
            )
            row.pack(fill=tk.X, pady=6)
            self.color_rows[attr] = row
            
        # 恢复默认色彩按钮
        ttk.Button(parent, text=Config.UI_TEXT['btn_reset_color'], command=self.app.reset_colors).pack(fill=tk.X, pady=(15, 20))
                  
        # 分割线及高亮“导出图表”尊贵按钮
        tk.Frame(parent, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=10)
        ttk.Button(parent, text=Config.UI_TEXT['btn_export'], command=self.app.open_export_dialog, 
                   style='Action.TButton').pack(fill=tk.X, pady=(15, 30))

    def update_swatches(self):
        """ 响应色彩重置或重新选取，动态同步色彩块底色 """
        for attr, row in self.color_rows.items():
            row.update_color(getattr(self.app, attr))

    def update_states(self, is_gray_enabled):
        """ 根据“是否显示补零”开关状态，联动设置“背景块”和“块内字”颜色行的置灰状态 """
        for attr in ['bg_block_color', 'bg_digit_color']:
            if attr in self.color_rows:
                self.color_rows[attr].set_state(is_gray_enabled)
