import os
import ctypes
import tkinter as tk
from tkinter import messagebox, font as tkfont, colorchooser, ttk, filedialog
from PIL import Image, ImageGrab, ImageTk

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.renderer import CanvasRenderer
from view.export_dialog import ExportDialog

class CRCVisualizerApp:
    """
    CRC Visualizer 应用程序主类。
    
    整合 Pillow 高保真内存渲染管道，提供极具沉浸感的交互。
    支持主/次画布 100% 物理重绘、高清多倍数无损导出，以及自适应布局。
    """
    def __init__(self, root):
        self.root = root
        self.root.title(Config.UI_TEXT['title'])
        
        # 初始化核心引擎与变量
        self.engine = CRCEngine()
        self.renderer = None
        self.view_scale = 1.0  # 全局缩放比例
        self.photo_img = None  # 强引用保持
        
        # 1. 基础环境配置
        self._setup_window_geometry()
        self._load_default_colors()
        self._setup_styles()
        
        # 2. 构建 UI 布局
        self.setup_ui()
        
        # 3. 启动初始化与智能居中
        self.root.update_idletasks()
        self.update_ui_states()
        self.generate(auto_center=True)
        self.root.after(100, self.center_view)

    # --- 基础配置方法 ---

    def _setup_window_geometry(self):
        """ 配置窗口初始大小及位置（智能居中，并默认最大化启动） """
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w = min(Config.LAYOUT['window_max_w'], int(sw * Config.LAYOUT['window_w_ratio']))
        h = min(Config.LAYOUT['window_max_h'], int(sh * Config.LAYOUT['window_h_ratio']))
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.minsize(Config.LAYOUT['window_min_w'], Config.LAYOUT['window_min_h'])
        self.root.configure(bg=Config.COLORS['main_bg'])
        
        try:
            # 默认以窗口最大化启动，为高清晰度长除法画布提供极致沉浸空间
            self.root.state('zoomed')
        except Exception:
            pass

    def _load_default_colors(self):
        for attr, color in Config.DEFAULT_COLORS.items():
            setattr(self, attr, color)

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TCombobox', padding=Config.LAYOUT['entry_ipady'])
        self.style.configure('TCombobox', font=Config.FONTS['combo'])

    # --- UI 构建逻辑 ---

    def setup_ui(self):
        """ 构建整体 UI 框架：左侧控制面板 + 右侧画布区域 """
        self._setup_sidebar_base()
        
        panel = self.scrollable_frame
        panel.inner_panel = tk.Frame(panel, bg=Config.COLORS['sidebar_bg'], 
                                     padx=Config.LAYOUT['input_padx'], 
                                     pady=Config.LAYOUT['input_pady'])
        panel.inner_panel.pack(fill=tk.BOTH, expand=True)
        
        self._init_input_section(panel.inner_panel)
        self._init_style_section(panel.inner_panel)
        self._init_color_section(panel.inner_panel)
        
        # 右侧核心画布区域
        self._setup_canvas_area()

    def _setup_sidebar_base(self):
        """ 构建带滚动条的响应式侧边栏 """
        win_w = self.root.winfo_width()
        if win_w <= 1: win_w = min(1600, int(self.root.winfo_screenwidth() * 0.9))
        side_w = max(Config.LAYOUT['min_side_width'], int(win_w * Config.LAYOUT['side_ratio']))
        
        self.side_container = tk.Frame(self.root, bg=Config.COLORS['sidebar_bg'], width=side_w)
        self.side_container.pack(side=tk.LEFT, fill=tk.Y)
        self.side_container.pack_propagate(False)

        self.side_canvas = tk.Canvas(self.side_container, bg=Config.COLORS['sidebar_bg'], highlightthickness=0)
        self.side_scrollbar = tk.Scrollbar(self.side_container, orient="vertical", command=self.side_canvas.yview)
        self.scrollable_frame = tk.Frame(self.side_canvas, bg=Config.COLORS['sidebar_bg'], width=side_w-Config.LAYOUT['side_scroll_offset'])
        
        self.side_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=side_w-Config.LAYOUT['side_scroll_offset'])
        
        tk.Label(self.scrollable_frame, text=Config.UI_TEXT['sidebar_title'], bg=Config.COLORS['sidebar_bg'], 
                 fg=Config.COLORS['sidebar_title_fg'], font=Config.FONTS['side_title']).pack(pady=(20, 10))
        tk.Frame(self.scrollable_frame, height=2, bg=Config.COLORS['primary'], width=Config.LAYOUT['side_divider_width']).pack(pady=(0, 20))
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        )
        
        self.side_canvas.configure(yscrollcommand=self.side_scrollbar.set)
        self.side_scrollbar.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)

        def _bind_mousewheel(event):
            self.side_canvas.bind_all("<MouseWheel>", lambda e: self.side_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        def _unbind_mousewheel(event):
            self.side_canvas.unbind_all("<MouseWheel>")
            
        self.side_container.bind("<Enter>", _bind_mousewheel)
        self.side_container.bind("<Leave>", _unbind_mousewheel)

    def _init_input_section(self, parent):
        """ 初始化输入区域 """
        tk.Label(parent, text=Config.UI_TEXT['data_label'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        self.data_var = tk.StringVar(value=Config.DEFAULT_VALUES['data'])
        self.data_entry = tk.Entry(parent, textvariable=self.data_var, font=Config.FONTS['en_main'])
        self.data_entry.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']), ipady=Config.LAYOUT['entry_ipady'])
        self.data_entry.bind("<Return>", lambda e: self.generate(auto_center=True))

        tk.Label(parent, text=Config.UI_TEXT['poly_label'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        pf = tk.Frame(parent, bg=Config.COLORS['sidebar_bg'])
        pf.pack(fill=tk.X, pady=(0, 5))
        self.divisor_var = tk.StringVar(value=Config.DEFAULT_VALUES['divisor'])
        self.poly_entry = tk.Entry(pf, textvariable=self.divisor_var, font=Config.FONTS['en_main'])
        self.poly_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=Config.LAYOUT['entry_ipady'])
        self.poly_entry.bind("<Return>", lambda e: self.generate(auto_center=True))
        
        self.poly_combo = ttk.Combobox(parent, values=list(Config.STD_POLYS.keys()), state="readonly", font=Config.FONTS['btn_small'])
        self.poly_combo.set(list(Config.STD_POLYS.keys())[0])
        self.poly_combo.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']))
        self.poly_combo.bind("<<ComboboxSelected>>", self.on_poly_selected)

        # 补零标记开关
        self.show_gray_var = tk.BooleanVar(value=Config.DEFAULT_VALUES['show_gray'])
        self._add_custom_check(parent, Config.UI_TEXT['gray_toggle'], self.show_gray_var, self.on_toggle_gray)
        
        tk.Frame(parent, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=10)

    def _init_style_section(self, parent):
        """ 初始化排版布局参数区 """
        tk.Label(parent, text=Config.UI_TEXT['style_section'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
        dv = Config.DEFAULT_VALUES
        styles = [
            (Config.UI_TEXT['font_size'], 10, 80, "font_size_var", dv['font_size'], 1),
            (Config.UI_TEXT['h_spacing'], 0.5, 3.0, "spacing_var", dv['h_spacing'], 0.1),
            (Config.UI_TEXT['v_spacing'], 0.5, 3.0, "v_spacing_var", dv['v_spacing'], 0.1),
            (Config.UI_TEXT['line_width'], 1, 10, "line_width_var", dv['line_width'], 1),
            (Config.UI_TEXT['padding'], 0, 200, "padding_var", dv['padding'], 1),
            (Config.UI_TEXT['ext_left'], -5.0, 0.0, "line_ext_left_var", dv['ext_left'], 0.1),
            (Config.UI_TEXT['ext_right'], 0.0, 5.0, "line_ext_right_var", dv['ext_right'], 0.1),
            (Config.UI_TEXT['span_left'], -2.0, -0.1, "curve_span_left_var", dv['span_left'], 0.1),
            (Config.UI_TEXT['span_right'], -1.5, 1.5, "curve_span_right_var", dv['span_right'], 0.1)
        ]
        for label, f, t, var, d, r in styles:
            self._add_scale(parent, label, f, t, var, d, res=r)
        
        tk.Button(parent, text=Config.UI_TEXT['btn_reset_params'], command=self.reset_params, 
                  font=Config.FONTS['btn_small'], bg=Config.COLORS['btn_default_bg'], pady=Config.LAYOUT['btn_ipady']).pack(fill=tk.X, pady=(5, Config.LAYOUT['section_pady']))

    def _init_color_section(self, parent):
        """ 初始化颜色选择区，并在底部加入高贵大气的“导出图表”按钮 """
        tk.Label(parent, text=Config.UI_TEXT['color_section'], bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
        
        # 逐行构建精美颜色配置项，左侧为中文标签，右侧为可点击色块
        self._add_color_row(parent, Config.UI_TEXT['label_bg_block_color'], 'bg_block_color')
        self._add_color_row(parent, Config.UI_TEXT['label_bg_digit_color'], 'bg_digit_color')
        self._add_color_row(parent, Config.UI_TEXT['label_digit_color'], 'digit_color')
        self._add_color_row(parent, Config.UI_TEXT['label_line_color'], 'line_color')
        self._add_color_row(parent, Config.UI_TEXT['label_sheet_bg_color'], 'sheet_bg_color')
        self._add_color_row(parent, Config.UI_TEXT['label_canvas_bg_color'], 'canvas_bg_color')
        
        tk.Button(parent, text=Config.UI_TEXT['btn_reset_color'], command=self.reset_colors, 
                  font=Config.FONTS['btn_small'], bg=Config.COLORS['btn_default_bg'], pady=Config.LAYOUT['btn_ipady']).pack(fill=tk.X, pady=(15, 20))
                  
        # 尊贵大气的深蓝色“导出图表”大按钮
        tk.Frame(parent, height=1, bg=Config.COLORS['divider']).pack(fill=tk.X, pady=10)
        tk.Button(parent, text=Config.UI_TEXT['btn_export'], command=self.open_export_dialog, 
                  font=Config.FONTS['btn_large_bold'], fg="white", bg=Config.COLORS['primary'], activebackground=Config.COLORS['primary_active'],
                  activeforeground="white", pady=10).pack(fill=tk.X, pady=(15, 30))

    def _setup_canvas_area(self):
        """ 构建右侧核心绘图区域 """
        cont = tk.Frame(self.root, bg=Config.LAYOUT['canvas_bg'], bd=2)
        cont.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.canvas = tk.Canvas(cont, bg=Config.COLORS['canvas_default_bg'], highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self._setup_canvas_toolbar(cont)
        
        self.renderer = CanvasRenderer(self.canvas)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def _setup_canvas_toolbar(self, parent):
        tb = tk.Frame(parent, bg=Config.COLORS['toolbar_bg'], bd=1, relief=tk.RAISED, padx=10, pady=5)
        tb.place(relx=0.5, y=30, anchor="n")
        
        tk.Button(tb, text=" - ", command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_out_factor']), font=Config.FONTS['zoom_btn'], 
                  bg=Config.COLORS['zoom_btn_bg'], relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        self.zoom_lbl = tk.Label(tb, text="100%", font=Config.FONTS['zoom_lbl'], 
                                 bg=Config.COLORS['toolbar_bg'], width=6)
        self.zoom_lbl.pack(side=tk.LEFT, padx=5)
        tk.Button(tb, text=" + ", command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_in_factor']), font=Config.FONTS['zoom_btn'], 
                  bg=Config.COLORS['zoom_btn_bg'], relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        tk.Frame(tb, width=1, bg=Config.COLORS['toolbar_divider'], height=20).pack(side=tk.LEFT, padx=10)
        
        tk.Button(tb, text=Config.UI_TEXT['btn_fit'], command=self.center_view, 
                  font=Config.FONTS['btn_small'], bg=Config.COLORS['toolbar_bg'], relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tb, text=Config.UI_TEXT['btn_reset_view'], command=self.reset_view, 
                  font=Config.FONTS['btn_small'], bg=Config.COLORS['toolbar_bg'], relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

    # --- 核心业务与渲染逻辑 ---

    def generate(self, auto_center=False, force_rebuild=True):
        """ 核心生成入口：采用双通道缓存加速，15ms 智能防抖合并滑块拖拽，视角放缩 0 延迟极速响应 """
        # 如果仅仅是视角的放大或缩小，直接调用极速位图插值 resize 并在 1ms 内展示，完全绕过防抖，实现 0 延迟顺滑响应！
        if not force_rebuild:
            self._actual_generate(auto_center, force_rebuild=False)
            return

        if getattr(self, '_render_pending', False):
            self._next_auto_center = auto_center
            return
            
        self._render_pending = True
        self._next_auto_center = auto_center
        
        def run_generation():
            try:
                self._actual_generate(self._next_auto_center, force_rebuild=True)
            finally:
                self._render_pending = False
                
        # 拖动滑块时调用，延迟 15 毫秒合并高频请求，保障拖拽无粘滞
        self.root.after(15, run_generation)

    def _actual_generate(self, auto_center=False, force_rebuild=True):
        """ 实际的渲染物理管线：利用基准大图缓存，将缩放视角与排版重绘深度解耦，响应速度提升百倍！ """
        data = self.data_var.get().strip()
        divisor = self.divisor_var.get().strip()
        
        if not data or not divisor:
            messagebox.showwarning(Config.MESSAGES['warning_title_invalid'], Config.MESSAGES['warning_empty'])
            return
        if not all(c in '01' for c in data) or not all(c in '01' for c in divisor):
            messagebox.showwarning(Config.MESSAGES['warning_title_format'], Config.MESSAGES['warning_invalid_binary'])
            return
        if divisor[0] == '0':
            messagebox.showwarning(Config.MESSAGES['warning_title_algo'], Config.MESSAGES['warning_poly_first_bit_1'])
            return
        if len(divisor) < 2:
            messagebox.showwarning(Config.MESSAGES['warning_title_algo'], Config.MESSAGES['warning_poly_len_min_2'])
            return

        # 1. 仅在参数/数据实际变化，或缓存未初始化时，才重新进行昂贵的 SSAA 内存排版绘制
        if force_rebuild or not getattr(self, 'base_image', None):
            q, rows, dividend = self.engine.calculate(data, divisor)
            ctx = self._get_render_context()
            # 基础缓存大图的渲染比例强制恒等于 1.0 物理原比例
            ctx['view_scale'] = 1.0
            self.base_image = self.renderer.render(data, dividend, divisor, q, rows, ctx)

        # 2. 从极其轻量级的内存缓存中直接根据当前 view_scale 极速缩放视角
        vs = getattr(self, 'view_scale', 1.0)
        if abs(vs - 1.0) > 1e-4:
            tw = max(1, int(self.base_image.width * vs))
            th = max(1, int(self.base_image.height * vs))
            # 极其高效的 C 语言位图插值缩放，耗时低于 1 毫秒！
            img = self.base_image.resize((tw, th), Image.Resampling.BILINEAR)
        else:
            img = self.base_image
        
        # 3. 转为 ImageTk 并贴在 Canvas 中央 (0, 0)
        self.photo_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(bg=self.canvas_bg_color)
        self.canvas.create_image(0, 0, image=self.photo_img, anchor="center")
        self.canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
        
        if auto_center: self.center_view()

    def _get_render_context(self):
        ctx = {
            'view_scale': getattr(self, 'view_scale', 1.0),
            'font_size': self.font_size_var.get(),
            'grid_base': Config.GRID_BASE,
            'h_spacing': self.spacing_var.get(),
            'v_spacing': self.v_spacing_var.get(),
            'line_width': self.line_width_var.get(),
            'padding': self.padding_var.get(),
            'show_gray': self.show_gray_var.get(),
            'show_border': True,  # 主界面始终显示精美边框
            'ext_left': self.line_ext_left_var.get(),
            'ext_right': self.line_ext_right_var.get(),
            'curve_span_left': self.curve_span_left_var.get(),
            'curve_span_right': self.curve_span_right_var.get(),
            **{k: getattr(self, k) for k in Config.DEFAULT_COLORS}
        }
        return ctx

    # --- 交互控制方法 ---

    def _adjust_zoom(self, factor):
        new_scale = self.view_scale * factor
        if Config.LAYOUT['zoom_min'] <= new_scale <= Config.LAYOUT['zoom_max']:
            self.view_scale = new_scale
            self.update_zoom_display()
            self.generate(auto_center=False, force_rebuild=False)

    def on_mousewheel(self, event):
        self.view_scale = max(Config.LAYOUT['zoom_min'], min(5.0, getattr(self, 'view_scale', 1.0) * (Config.LAYOUT['zoom_in_factor'] if event.delta > 0 else Config.LAYOUT['zoom_out_factor'])))
        self.update_zoom_display()
        self.generate(auto_center=False, force_rebuild=False)

    def update_zoom_display(self):
        if hasattr(self, 'zoom_lbl'):
            self.zoom_lbl.config(text=f"{int(self.view_scale * 100)}%")

    def center_view(self):
        bbox = self.canvas.bbox("all")
        if not bbox: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.xview_moveto(((bbox[0]+bbox[2])/2 - cw/2 + 3000) / 6000)
        self.canvas.yview_moveto(((bbox[1]+bbox[3])/2 - ch/2 + 3000) / 6000)

    def reset_view(self):
        """ 重置缩放比例与居中视角 """
        self.view_scale = 1.0
        self.update_zoom_display()
        self.generate(True, force_rebuild=False)

    def start_pan(self, event): self.canvas.scan_mark(event.x, event.y)
    def do_pan(self, event): self.canvas.scan_dragto(event.x, event.y, gain=1)

    def pick_color(self, attr):
        color = colorchooser.askcolor(initialcolor=getattr(self, attr))[1]
        if color:
            setattr(self, attr, color)
            self.update_color_swatches()
            self.generate()

    def reset_colors(self):
        self._load_default_colors()
        self.update_color_swatches()
        self.generate()

    def reset_params(self):
        mapping = {
            'font_size': 'font_size_var', 'h_spacing': 'spacing_var', 'v_spacing': 'v_spacing_var',
            'line_width': 'line_width_var', 'padding': 'padding_var', 'ext_left': 'line_ext_left_var',
            'ext_right': 'line_ext_right_var', 'span_left': 'curve_span_left_var', 'span_right': 'curve_span_right_var'
        }
        for key, var_name in mapping.items():
            if hasattr(self, var_name):
                getattr(self, var_name).set(Config.DEFAULT_VALUES[key])
        self.generate()

    def on_poly_selected(self, event):
        poly = Config.STD_POLYS.get(self.poly_combo.get())
        if poly: self.divisor_var.set(poly); self.generate(True)

    def on_toggle_gray(self):
        self.update_ui_states(); self.generate(False)

    def update_ui_states(self):
        is_gray_enabled = self.show_gray_var.get()
        
        # 针对 "背景块" 和 "块内字" 颜色行的控件状态刷新
        for attr in ['bg_block_color', 'bg_digit_color']:
            if hasattr(self, 'color_swatches') and attr in self.color_swatches:
                canvas = self.color_swatches[attr]
                lbl = self.color_labels[attr]
                if is_gray_enabled:
                    canvas.config(cursor="hand2", highlightbackground=Config.COLORS['border_enabled'])
                    lbl.config(fg=Config.COLORS['fg_enabled'])
                else:
                    canvas.config(cursor="", highlightbackground=Config.COLORS['border_disabled'])
                    lbl.config(fg=Config.COLORS['fg_disabled'])

    # --- 弹出式导出与实时高保真重绘预览 ---

    def open_export_dialog(self):
        """ 打开导出对话框以进行高保真多倍率大图和矢量图保存 """
        ExportDialog(self)

    # --- UI 辅助绘图组件 ---

    def _add_custom_check(self, parent, text, var, command):
        """ 绘制一个现代化、大尺寸的自定义复选框 """
        f = tk.Frame(parent, bg=Config.COLORS['sidebar_bg'])
        f.pack(anchor=tk.W, pady=(0, Config.LAYOUT['section_pady']))
        sz = Config.LAYOUT['check_size']
        canvas = tk.Canvas(f, width=sz+4, height=sz+4, bg=Config.COLORS['sidebar_bg'], highlightthickness=0, cursor="hand2")
        canvas.pack(side=tk.LEFT)
        lbl = tk.Label(f, text=text, bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_normal'], cursor="hand2")
        lbl.pack(side=tk.LEFT, padx=5)
        
        def refresh():
            canvas.delete("all")
            color = Config.LAYOUT['check_color'] if var.get() else Config.COLORS['border_enabled']
            canvas.create_rectangle(2, 2, sz+1, sz+1, outline=color, width=2)
            if var.get():
                canvas.create_line(sz*0.2, sz*0.5, sz*0.45, sz*0.8, fill=color, width=3)
                canvas.create_line(sz*0.45, sz*0.8, sz*0.85, sz*0.25, fill=color, width=3)
        def toggle(e=None):
            var.set(not var.get())
            refresh()
            if command: command()
        canvas.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        refresh()

    def _add_scale(self, parent, label, f, t, var_name, default, res=1):
        """ 通用滑块组件封装 """
        tk.Label(parent, text=label, bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_normal']).pack(anchor=tk.W, pady=(5, 0))
        var = tk.DoubleVar(value=default) if isinstance(res, float) else tk.IntVar(value=default)
        setattr(self, var_name, var)
        tk.Scale(parent, from_=f, to_=t, resolution=res, orient=tk.HORIZONTAL, variable=var, 
                 sliderlength=Config.LAYOUT['slider_len'], width=Config.LAYOUT['slider_thick'],
                 font=("Times New Roman", 10), bg=Config.COLORS['sidebar_bg'], highlightthickness=0, 
                 command=lambda x: self.generate(auto_center=False)).pack(fill=tk.X, pady=(0, 10))

    def _add_color_row(self, parent, text, attr):
        """ 新增现代化高品质色彩配置行：左侧显示名称，右侧显示精美物理色彩框，支持实时点击重置色值 """
        row_frame = tk.Frame(parent, bg=Config.COLORS['sidebar_bg'])
        row_frame.pack(fill=tk.X, pady=6)
        
        lbl = tk.Label(row_frame, text=text, bg=Config.COLORS['sidebar_bg'], font=Config.FONTS['zh_normal'])
        lbl.pack(side=tk.LEFT)
        
        sz = Config.LAYOUT['check_size']
        canvas = tk.Canvas(
            row_frame, 
            width=sz * 2.5, 
            height=sz, 
            bg=getattr(self, attr), 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['border_enabled'],
            cursor="hand2"
        )
        canvas.pack(side=tk.RIGHT)
        
        def on_click(e):
            if canvas.cget("cursor") == "hand2":
                self.pick_color(attr)
                
        canvas.bind("<Button-1>", on_click)
        
        # 缓存引用
        if not hasattr(self, 'color_swatches'):
            self.color_swatches = {}
        if not hasattr(self, 'color_labels'):
            self.color_labels = {}
            
        self.color_swatches[attr] = canvas
        self.color_labels[attr] = lbl
        
        return row_frame

    def update_color_swatches(self):
        """ 刷新所有颜色块的物理背景，响应重置或挑选更新 """
        if hasattr(self, 'color_swatches'):
            for attr, canvas in self.color_swatches.items():
                canvas.config(bg=getattr(self, attr))

if __name__ == "__main__":
    # 提升高DPI清晰度（针对 Windows 系统）
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = CRCVisualizerApp(root)
    root.mainloop()