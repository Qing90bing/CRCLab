import tkinter as tk
import os
from PIL import Image, ImageTk
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
        """ 弹出优雅的自定义关于本软件对话框，保证字体完全受控统一，并增加视觉美化设计 """
        dlg = tk.Toplevel(self.app.root)
        dlg.title(Config.UI_TEXT['about_title'])
        dlg.transient(self.app.root)
        
        try:
            self.app.root.attributes("-disabled", True)
        except Exception:
            pass
            
        def restore_parent(event):
            if event.widget == dlg:
                try:
                    self.app.root.attributes("-disabled", False)
                except Exception:
                    pass
        dlg.bind("<Destroy>", restore_parent)
        
        dlg.configure(bg=Config.COLORS['main_bg'])
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()
        
        content = tk.Frame(dlg, bg=Config.COLORS['main_bg'], padx=30, pady=25)
        content.pack(fill=tk.BOTH, expand=True)
        
        self._create_about_header(content)
        tk.Frame(content, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=(0, 15))
        self._create_about_tech_info(content)
        tk.Frame(content, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=10)
        self._create_about_libs(content)
        self._create_about_footer(content, dlg)
        
        dlg.update_idletasks()
        rw = max(580, dlg.winfo_reqwidth())
        rh = max(500, dlg.winfo_reqheight())
        dlg.geometry(f"{rw}x{rh}+{(sw-rw)//2}+{(sh-rh)//2}")
        dlg.resizable(False, False)

    def _create_about_header(self, parent):
        """ 创建关于对话框的头部区域 """
        header_frame = tk.Frame(parent, bg=Config.COLORS['main_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "app_icon2.png")
        try:
            img = Image.open(logo_path)
            resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
            img.thumbnail((300, 90), resample_filter)
            photo = ImageTk.PhotoImage(img)
            logo_lbl = tk.Label(header_frame, image=photo, bg=Config.COLORS['main_bg'])
            logo_lbl.image = photo
            logo_lbl.pack(side=tk.LEFT, padx=(0, 20))
        except Exception:
            tk.Label(header_frame, text="CRCLab", font=("Times New Roman", 24, "bold"), 
                     bg=Config.COLORS['main_bg'], fg=Config.COLORS['primary']).pack(side=tk.LEFT, padx=(0, 20))
            
        title_frame = tk.Frame(header_frame, bg=Config.COLORS['main_bg'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        
        tk.Label(title_frame, text="CRCLab", font=("Times New Roman", 22, "bold"), 
                 bg=Config.COLORS['main_bg'], fg=Config.COLORS['primary']).pack(anchor="w", pady=(8, 0))
        tk.Label(title_frame, text="循环冗余校验解析与验证工具", font=Config.FONTS['zh_bold'], 
                 bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_dark']).pack(anchor="w", pady=(4, 0))
        tk.Label(title_frame, text=f"版本: {Config.VERSION}", font=Config.FONTS['en_main'], 
                 bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_muted']).pack(anchor="w", pady=(4, 0))

    def _create_about_tech_info(self, parent):
        """ 创建关于对话框的技术信息与链接区域 """
        info_frame = tk.Frame(parent, bg=Config.COLORS['main_bg'])
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        import tkinter.font as tkfont
        import webbrowser
        
        zh_normal_font = Config.FONTS['zh_normal']
        link_font = tkfont.Font(family=zh_normal_font[0], size=zh_normal_font[1], underline=True)
        
        meta_frame = tk.Frame(info_frame, bg=Config.COLORS['main_bg'])
        meta_frame.pack(fill=tk.X, pady=(0, 10))
        
        author_row = tk.Frame(meta_frame, bg=Config.COLORS['main_bg'])
        author_row.pack(fill=tk.X, pady=2)
        tk.Label(author_row, text="开发作者: ", font=Config.FONTS['zh_normal'], bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_dark']).pack(side=tk.LEFT)
        tk.Label(author_row, text=Config.AUTHOR, font=Config.FONTS['zh_normal'], bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_dark']).pack(side=tk.LEFT)
        
        repo_row = tk.Frame(meta_frame, bg=Config.COLORS['main_bg'])
        repo_row.pack(fill=tk.X, pady=2)
        tk.Label(repo_row, text="开源仓库: ", font=Config.FONTS['zh_normal'], bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_dark']).pack(side=tk.LEFT)
        
        repo_lbl = tk.Label(repo_row, text=Config.REPOSITORY, font=link_font, fg=Config.COLORS['primary'], bg=Config.COLORS['main_bg'], cursor="hand2")
        repo_lbl.pack(side=tk.LEFT)
        repo_lbl.bind("<Button-1>", lambda e: webbrowser.open_new(Config.REPOSITORY))
        
        feedback_row = tk.Frame(meta_frame, bg=Config.COLORS['main_bg'])
        feedback_row.pack(fill=tk.X, pady=2)
        tk.Label(feedback_row, text="问题反馈: ", font=Config.FONTS['zh_normal'], bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_dark']).pack(side=tk.LEFT)
        
        feedback_url = f"{Config.REPOSITORY}/issues"
        feedback_lbl = tk.Label(feedback_row, text=feedback_url, font=link_font, fg=Config.COLORS['primary'], bg=Config.COLORS['main_bg'], cursor="hand2")
        feedback_lbl.pack(side=tk.LEFT)
        feedback_lbl.bind("<Button-1>", lambda e: webbrowser.open_new(feedback_url))
        
        tech_text = (
            f"核心技术特性:\n"
            f"• 支持无损矢量 EMF / SVG 导出，拒绝缩放模糊\n"
            f"• 搭载 GDI 高清渲染核心，实现 Office 排版像素级兼容\n"
            f"• 实时二进制长除运算结果看板与过程特征自动解析"
        )
        tk.Label(info_frame, text=tech_text, font=Config.FONTS['zh_normal'], bg=Config.COLORS['main_bg'], 
                 fg=Config.COLORS['text_dark'], justify=tk.LEFT, anchor="w").pack(fill=tk.X, expand=True, pady=(5, 0))

    def _create_about_libs(self, parent):
        """ 创建关于对话框的第三方库展示区域 """
        import webbrowser
        import tkinter.font as tkfont
        
        zh_normal_font = Config.FONTS['zh_normal']
        link_font = tkfont.Font(family=zh_normal_font[0], size=zh_normal_font[1], underline=True)
        
        libs_section = tk.Frame(parent, bg=Config.COLORS['main_bg'])
        libs_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(libs_section, text="使用的第三方库:", font=Config.FONTS['zh_bold'], bg=Config.COLORS['main_bg'], 
                 fg=Config.COLORS['text_dark'], anchor="w").pack(fill=tk.X, pady=(0, 5))
        
        libs_row = tk.Frame(libs_section, bg=Config.COLORS['main_bg'])
        libs_row.pack(fill=tk.X, pady=2)
        
        libs_row.grid_columnconfigure(0, weight=1)
        libs_row.grid_columnconfigure(1, weight=1)
        libs_row.grid_columnconfigure(2, weight=1)
        
        libs = [
            ("Pillow", "https://github.com/python-pillow/Pillow", 0, tk.W),
            ("svglib", "https://github.com/deeplook/svglib", 1, None),
            ("reportlab", "https://pypi.org/project/reportlab/", 2, tk.E)
        ]
        
        for name, url, col, sticky in libs:
            lbl = tk.Label(libs_row, text=name, font=link_font, fg=Config.COLORS['primary'], bg=Config.COLORS['main_bg'], cursor="hand2")
            if sticky:
                lbl.grid(row=0, column=col, sticky=sticky)
            else:
                lbl.grid(row=0, column=col)
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open_new(u))

    def _create_about_footer(self, parent, dlg):
        """ 创建关于对话框的底部版权与确定按钮区域 """
        bottom_frame = tk.Frame(parent, bg=Config.COLORS['main_bg'])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Label(bottom_frame, text=Config.COPYRIGHT, font=Config.FONTS['en_main'], 
                 bg=Config.COLORS['main_bg'], fg=Config.COLORS['text_muted']).pack(side=tk.LEFT, pady=(15, 0))
        
        btn = ttk.Button(bottom_frame, text="确定", width=8, command=dlg.destroy, style='Action.TButton')
        try:
            btn.pack(side=tk.RIGHT, pady=(15, 0))
        except Exception:
            ttk.Button(bottom_frame, text="确定", width=8, command=dlg.destroy).pack(side=tk.RIGHT, pady=(15, 0))
