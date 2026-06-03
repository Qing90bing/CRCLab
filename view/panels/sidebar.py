import tkinter as tk
import os
from PIL import Image, ImageTk
from tkinter import ttk
from config.constants import Config
from view.components.widgets import ModernCheckbutton, ModernScale, ColorSwatchRow

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
        :param app: 主应用程序 CRCLabApp 实例。
        :param width: 侧边栏宽度。
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
        """ 构建带滚动条的侧边栏容器框架 """
        self.side_canvas = tk.Canvas(self, bg=Config.COLORS['sidebar_bg'], highlightthickness=0)
        self.side_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.side_canvas.yview)
        
        scroll_w = side_w - Config.LAYOUT['side_scroll_offset']
        self.scrollable_frame = tk.Frame(self.side_canvas, bg=Config.COLORS['sidebar_bg'], width=scroll_w)
        
        self.side_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=scroll_w)
        
        # 绘制功能配置主标题，并在同一行右侧放置原生信息按钮
        title_row = tk.Frame(self.scrollable_frame, bg=Config.COLORS['sidebar_bg'])
        title_row.pack(fill=tk.X, padx=20, pady=(20, 10))
        title_row.grid_columnconfigure(0, weight=1, uniform="sidebar_title")
        title_row.grid_columnconfigure(2, weight=1, uniform="sidebar_title")
        
        tk.Label(title_row, text=Config.UI_TEXT['sidebar_title'], bg=Config.COLORS['sidebar_bg'], 
                 fg=Config.COLORS['sidebar_title_fg'], font=Config.FONTS['side_title']).grid(row=0, column=1)
        ttk.Button(title_row, text="ⓘ", width=3, command=self.show_about_dialog).grid(row=0, column=2, sticky=tk.E)
        tk.Frame(self.scrollable_frame, height=2, bg=Config.COLORS['primary'], width=Config.LAYOUT['side_divider_width']).pack(pady=(0, 20))
        
        # 绑定尺寸重构事件，实时同步更新滚动视区大小
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        )
        
        self.side_canvas.configure(yscrollcommand=self.side_scrollbar.set)
        self.side_scrollbar.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)

        # 鼠标移入自动绑定/移出解绑全局滚轮事件，防止与主 Canvas 产生滚动冲突
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
        parent = tk.LabelFrame(
            self.inner_panel, 
            text=Config.UI_TEXT.get('input_section', '基础数据配置:'), 
            bg=Config.COLORS['sidebar_bg'],
            fg=Config.COLORS['sidebar_title_fg'],
            font=Config.FONTS['zh_bold'],
            padx=12, pady=10
        )
        parent.pack(fill=tk.X, pady=(0, 15))
        
        # 1. 原始二进制数据位输入
        tk.Label(parent, text=Config.UI_TEXT['data_label'], bg=Config.COLORS['sidebar_bg']).pack(anchor=tk.W, pady=(0, 5))
        self.data_entry = ttk.Entry(parent, textvariable=self.app.data_var, font=Config.FONTS['en_main'])
        self.data_entry.pack(fill=tk.X, pady=(0, 5))
        self.data_entry.bind("<Return>", lambda e: self.app.generate(auto_center=True))

        # 2. 生成多项式输入
        tk.Label(parent, text=Config.UI_TEXT['poly_label'], bg=Config.COLORS['sidebar_bg']).pack(anchor=tk.W, pady=(5, 5))
        pf = tk.Frame(parent, bg=Config.COLORS['sidebar_bg'])
        pf.pack(fill=tk.X, pady=(0, 5))
        self.poly_entry = ttk.Entry(pf, textvariable=self.app.divisor_var, font=Config.FONTS['en_main'])
        self.poly_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.poly_entry.bind("<Return>", lambda e: self.app.generate(auto_center=True))
        
        # 3. 标准预设多项式快速选择
        self.poly_combo = ttk.Combobox(parent, values=list(Config.STD_POLYS.keys()), state="readonly", font=Config.FONTS['btn_small'])
        self.poly_combo.set(list(Config.STD_POLYS.keys())[0])
        self.poly_combo.pack(fill=tk.X, pady=(0, 5))
        self.poly_combo.bind("<<ComboboxSelected>>", self.app.on_poly_selected)

    def _init_style_section(self):
        """ 初始化排版与长除法间距滑块区 """
        parent = tk.LabelFrame(
            self.inner_panel, 
            text=Config.UI_TEXT['style_section'], 
            bg=Config.COLORS['sidebar_bg'],
            fg=Config.COLORS['sidebar_title_fg'],
            font=Config.FONTS['zh_bold'],
            padx=12, pady=10
        )
        parent.pack(fill=tk.X, pady=(0, 15))
        
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
        ttk.Button(parent, text=Config.UI_TEXT['btn_reset_params'], command=self.app.reset_params).pack(fill=tk.X, pady=(10, 5))

    def _init_color_section(self):
        """ 初始化色彩配置项，并在底部渲染“导出图表”按钮 """
        parent = tk.LabelFrame(
            self.inner_panel, 
            text=Config.UI_TEXT['color_section'], 
            bg=Config.COLORS['sidebar_bg'],
            fg=Config.COLORS['sidebar_title_fg'],
            font=Config.FONTS['zh_bold'],
            padx=12, pady=10
        )
        parent.pack(fill=tk.X, pady=(0, 15))
        
        color_attrs = [
            ('bg_block_color', Config.UI_TEXT['label_bg_block_color'], True, None),
            ('bg_digit_color', Config.UI_TEXT['label_bg_digit_color'], False, self.app.bold_zeros_var),
            ('divisor_color', Config.UI_TEXT['label_divisor_color'], False, self.app.bold_divisor_var),
            ('quotient_color', Config.UI_TEXT['label_quotient_color'], False, self.app.bold_quotient_var),
            ('dividend_color', Config.UI_TEXT['label_dividend_color'], False, self.app.bold_dividend_var),
            ('line_color', Config.UI_TEXT['label_line_color'], False, None),
            ('sheet_bg_color', Config.UI_TEXT['label_sheet_bg_color'], True, None)
        ]
        
        self.color_rows = {}
        for attr, text, allow_trans, bold_var in color_attrs:
            row = ColorSwatchRow(
                parent, 
                text, 
                attr, 
                initial_color=getattr(self.app, attr), 
                on_click_callback=self.app.pick_color,
                on_transparent_toggle=self.app.on_transparent_toggle,
                allow_transparent=allow_trans,
                bold_var=bold_var,
                on_bold_toggle=lambda: self.app.generate(auto_center=False)
            )
            row.pack(fill=tk.X, pady=6)
            self.color_rows[attr] = row
            
        # 恢复默认色彩按钮
        ttk.Button(parent, text=Config.UI_TEXT['btn_reset_color'], command=self.app.reset_colors).pack(fill=tk.X, pady=(10, 5))
                  
        # 导出图表按钮（放在主 panel 中）
        ttk.Button(self.inner_panel, text=Config.UI_TEXT['btn_export'], command=self.app.open_export_dialog, 
                   style='Action.TButton').pack(fill=tk.X, pady=(15, 20))

    def update_swatches(self):
        """ 响应色彩重置或重新选取，动态同步色彩块底色 """
        for attr, row in self.color_rows.items():
            row.update_color(getattr(self.app, attr))

    def show_about_dialog(self):
        """ 弹出关于本软件对话框 """
        from view.dialogs.about_dialog import AboutDialog
        AboutDialog(self.app)

    def show_input_error(self, entry_widget, msg):
        """ 显示基础数据输入错误的悬浮 tooltip 并聚焦选中 """
        entry_widget.focus_set()
        entry_widget.selection_range(0, tk.END)
        
        if hasattr(self, '_error_tooltip') and self._error_tooltip:
            try:
                self._error_tooltip.destroy()
            except Exception:
                pass
            
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 2
        
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.geometry(f"+{x}+{y}")
        tip.configure(bg="#fef2f2", highlightbackground="#f87171", highlightthickness=1)
        
        lbl = tk.Label(
            tip, 
            text="⚠️ " + msg,
            bg="#fef2f2",
            fg="#b91c1c",
            font=Config.FONTS['zh_normal'],
            justify=tk.LEFT,
            padx=8,
            pady=4
        )
        lbl.pack()
        
        self._error_tooltip = tip
        
        def _close_tip(*args):
            if hasattr(self, '_error_tooltip') and self._error_tooltip == tip:
                try:
                    tip.destroy()
                except Exception:
                    pass
                self._error_tooltip = None
                
        tip.after(3000, _close_tip)
        
        # 绑定点击或按键时立刻消失
        entry_widget.bind("<Key>", _close_tip, add="+")
        entry_widget.bind("<Button-1>", _close_tip, add="+")

