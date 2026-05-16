import tkinter as tk
from tkinter import messagebox, font as tkfont, colorchooser, ttk
import ctypes

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.renderer import CanvasRenderer

# 提升高DPI清晰度
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class CRCVisualizerApp:
    """
    CRC Visualizer 应用程序主类。
    
    负责集成算法引擎、渲染引擎和配置常量，构建基于 Tkinter 的图形界面。
    实现了响应式侧边栏、画布拖拽平移、实时缩放、以及动态样式参数调整等功能。
    """
    def __init__(self, root):
        """
        初始化应用程序。
        :param root: Tkinter 根窗口实例。
        """
        self.root = root
        self.root.title(Config.UI_TEXT['title'])
        
        # 初始化核心组件
        self.engine = CRCEngine()
        self.renderer = None
        self.view_scale = 1.0  # 全局缩放比例
        
        # 1. 基础环境配置
        self._setup_window_geometry()
        self._load_default_colors()
        self._setup_styles()
        
        # 2. 构建 UI 布局
        self.setup_ui()
        
        # 3. 启动初始化
        self.root.update_idletasks()
        self.update_ui_states()
        self.generate(auto_center=True)
        # 延迟执行视角居中，确保 Canvas 尺寸已完全计算
        self.root.after(100, self.center_view)

    # --- 基础配置方法 ---

    def _setup_window_geometry(self):
        """ 配置窗口初始大小及位置（智能居中） """
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # 窗口大小取屏幕的 90%，但不超过 1600x1000
        w, h = min(1600, int(sw * 0.9)), min(1000, int(sh * 0.9))
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#f3f4f6")

    def _load_default_colors(self):
        """ 从 Config 动态加载初始颜色到 App 实例属性 """
        for attr, color in Config.DEFAULT_COLORS.items():
            setattr(self, attr, color)

    def _setup_styles(self):
        """ 针对 ttk 组件（如下拉框）进行深度样式定制 """
        self.style = ttk.Style()
        # 关键：通过 padding 控制 Combobox 的内部厚度，使其与普通 Entry 保持视觉一致
        self.style.configure('TCombobox', padding=Config.LAYOUT['entry_ipady'])
        self.style.configure('TCombobox', font=("SimSun", 10))

    # --- UI 构建逻辑 ---

    def setup_ui(self):
        """ 构建整体 UI 框架：左侧控制面板 + 右侧画布区域 """
        # 1. 侧边栏基础结构（含滚动支持）
        self._setup_sidebar_base()
        
        # 2. 控制面板内容填充
        panel = self.scrollable_frame
        panel.inner_panel = tk.Frame(panel, bg="#ffffff", 
                                     padx=Config.LAYOUT['input_padx'], 
                                     pady=Config.LAYOUT['input_pady'])
        panel.inner_panel.pack(fill=tk.BOTH, expand=True)
        
        self._init_input_section(panel.inner_panel)
        self._init_style_section(panel.inner_panel)
        self._init_color_section(panel.inner_panel)
        
        # 3. 右侧画布区域
        self._setup_canvas_area()

    def _setup_sidebar_base(self):
        """ 构建带滚动条的响应式侧边栏 """
        # 响应式宽度计算：基于窗口宽度的百分比
        win_w = self.root.winfo_width()
        if win_w <= 1: win_w = min(1600, int(self.root.winfo_screenwidth() * 0.9))
        side_w = max(Config.LAYOUT['min_side_width'], int(win_w * Config.LAYOUT['side_ratio']))
        
        self.side_container = tk.Frame(self.root, bg="#ffffff", width=side_w)
        self.side_container.pack(side=tk.LEFT, fill=tk.Y)
        self.side_container.pack_propagate(False)

        # 使用 Canvas 实现侧边栏内部滚动
        self.side_canvas = tk.Canvas(self.side_container, bg="#ffffff", highlightthickness=0)
        self.side_scrollbar = tk.Scrollbar(self.side_container, orient="vertical", command=self.side_canvas.yview)
        self.scrollable_frame = tk.Frame(self.side_canvas, bg="#ffffff", width=side_w-25)
        
        self.side_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=side_w-25)
        
        # 侧边栏标题
        tk.Label(self.scrollable_frame, text=Config.UI_TEXT['sidebar_title'], bg="#ffffff", 
                 fg="#1e293b", font=("SimSun", 16, "bold")).pack(pady=(20, 10))
        tk.Frame(self.scrollable_frame, height=2, bg="#3b82f6", width=200).pack(pady=(0, 20))
        
        # 监听内容变化并动态更新滚动区域
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        )
        
        self.side_canvas.configure(yscrollcommand=self.side_scrollbar.set)
        self.side_scrollbar.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)

        # 智能滚轮绑定：仅当鼠标在侧边栏上方时才启用滚动
        def _bind_mousewheel(event):
            self.side_canvas.bind_all("<MouseWheel>", lambda e: self.side_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        def _unbind_mousewheel(event):
            self.side_canvas.unbind_all("<MouseWheel>")
            
        self.side_container.bind("<Enter>", _bind_mousewheel)
        self.side_container.bind("<Leave>", _unbind_mousewheel)

    def _init_input_section(self, parent):
        """ 初始化数据位与多项式输入区 """
        tk.Label(parent, text=Config.UI_TEXT['data_label'], bg="#ffffff", font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        self.data_var = tk.StringVar(value=Config.DEFAULT_VALUES['data'])
        self.data_entry = tk.Entry(parent, textvariable=self.data_var, font=Config.FONTS['en_main'])
        self.data_entry.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']), ipady=Config.LAYOUT['entry_ipady'])
        self.data_entry.bind("<Return>", lambda e: self.generate(auto_center=True))

        tk.Label(parent, text=Config.UI_TEXT['poly_label'], bg="#ffffff", font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(5, 5))
        pf = tk.Frame(parent, bg="#ffffff")
        pf.pack(fill=tk.X, pady=(0, 5))
        self.divisor_var = tk.StringVar(value=Config.DEFAULT_VALUES['divisor'])
        self.poly_entry = tk.Entry(pf, textvariable=self.divisor_var, font=Config.FONTS['en_main'])
        self.poly_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=Config.LAYOUT['entry_ipady'])
        self.poly_entry.bind("<Return>", lambda e: self.generate(auto_center=True))
        
        # 标准多项式下拉选择
        self.poly_combo = ttk.Combobox(parent, values=list(Config.STD_POLYS.keys()), state="readonly", font=("SimSun", 9))
        self.poly_combo.set("自定义")
        self.poly_combo.pack(fill=tk.X, pady=(0, Config.LAYOUT['entry_pady']))
        self.poly_combo.bind("<<ComboboxSelected>>", self.on_poly_selected)

        # 补零标记开关
        self.show_gray_var = tk.BooleanVar(value=Config.DEFAULT_VALUES['show_gray'])
        self._add_custom_check(parent, Config.UI_TEXT['gray_toggle'], self.show_gray_var, self.on_toggle_gray)
        
        tk.Frame(parent, height=1, bg="#e5e7eb").pack(fill=tk.X, pady=10)

    def _init_style_section(self, parent):
        """ 初始化排版布局参数滑块区 """
        tk.Label(parent, text=Config.UI_TEXT['style_section'], bg="#ffffff", font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
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
                  font=("SimSun", 9), bg="#f8fafc", pady=Config.LAYOUT['btn_ipady']).pack(fill=tk.X, pady=(5, Config.LAYOUT['section_pady']))

    def _init_color_section(self, parent):
        """ 初始化颜色配置区 """
        tk.Label(parent, text=Config.UI_TEXT['color_section'], bg="#ffffff", font=Config.FONTS['zh_bold']).pack(anchor=tk.W, pady=(15, 5))
        grid = tk.Frame(parent, bg="#ffffff")
        grid.pack(fill=tk.X)
        self.btn_bg_block = self._add_color_btn(grid, "背景块", 'bg_block_color', 0, 0)
        self.btn_bg_digit = self._add_color_btn(grid, "块内字", 'bg_digit_color', 0, 1)
        self._add_color_btn(grid, "数字", 'digit_color', 0, 2)
        self._add_color_btn(grid, "线条", 'line_color', 1, 0)
        self._add_color_btn(grid, "纸张", 'sheet_bg_color', 1, 1)
        self._add_color_btn(grid, "画布", 'canvas_bg_color', 1, 2)
        tk.Button(parent, text=Config.UI_TEXT['btn_reset_color'], command=self.reset_colors, 
                  font=("SimSun", 9), bg="#f8fafc", pady=Config.LAYOUT['btn_ipady']).pack(fill=tk.X, pady=(10, 20))

    def _setup_canvas_area(self):
        """ 构建右侧核心绘图区域 """
        cont = tk.Frame(self.root, bg=Config.LAYOUT['canvas_bg'], bd=2)
        cont.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.canvas = tk.Canvas(cont, bg="#d1d5db", highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 创建悬浮工具栏
        self._setup_canvas_toolbar(cont)
        
        # 初始化渲染引擎
        self.renderer = CanvasRenderer(self.canvas)
        # 绑定画布交互事件
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def _setup_canvas_toolbar(self, parent):
        """ 在画布上方创建一个现代化的浮动工具栏 """
        tb = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.RAISED, padx=10, pady=5)
        # 悬浮在画布顶部中央
        tb.place(relx=0.5, y=30, anchor="n")
        
        # 1. 缩放控制组
        tk.Button(tb, text=" - ", command=lambda: self._adjust_zoom(0.9), font=("Arial", 12, "bold"), 
                  bg="#f8fafc", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        self.zoom_lbl = tk.Label(tb, text="100%", font=("Times New Roman", 11, "bold"), 
                                 bg="#ffffff", width=6)
        self.zoom_lbl.pack(side=tk.LEFT, padx=5)
        tk.Button(tb, text=" + ", command=lambda: self._adjust_zoom(1.1), font=("Arial", 12, "bold"), 
                  bg="#f8fafc", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        tk.Frame(tb, width=1, bg="#e2e8f0", height=20).pack(side=tk.LEFT, padx=10)
        
        # 2. 视角控制组
        tk.Button(tb, text=Config.UI_TEXT['btn_fit'], command=self.center_view, 
                  font=("SimSun", 9), bg="#ffffff", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tb, text=Config.UI_TEXT['btn_reset_view'], command=self.reset_view, 
                  font=("SimSun", 9), bg="#ffffff", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

    # --- 核心业务逻辑 ---

    def generate(self, auto_center=False):
        """ 核心生成逻辑：验证输入 -> 调用算法引擎 -> 调用渲染引擎 """
        data = self.data_var.get().strip()
        divisor = self.divisor_var.get().strip()
        
        # 1. 增强参数验证
        if not data or not divisor:
            messagebox.showwarning("输入无效", "数据位和多项式不能为空！")
            return
        if not all(c in '01' for c in data) or not all(c in '01' for c in divisor):
            messagebox.showwarning("格式错误", "请输入有效的二进制字符串 (仅限 0 和 1)！")
            return
        if divisor[0] == '0':
            messagebox.showwarning("算法限制", "多项式首位必须为 1 才能进行有效的 CRC 除法计算。")
            return
        if len(divisor) < 2:
            messagebox.showwarning("算法限制", "多项式长度至少需为 2 位。")
            return

        # 2. 计算 CRC 过程
        q, rows, dividend = self.engine.calculate(data, divisor)
        
        # 3. 渲染
        ctx = self._get_render_context()
        self.renderer.render(data, dividend, divisor, q, rows, ctx)
        
        if auto_center: self.center_view()

    def _get_render_context(self):
        """ 统一收集当前 UI 状态作为渲染上下文 """
        ctx = {
            'view_scale': getattr(self, 'view_scale', 1.0),
            'font_size': self.font_size_var.get(),
            'grid_base': Config.GRID_BASE,
            'h_spacing': self.spacing_var.get(),
            'v_spacing': self.v_spacing_var.get(),
            'line_width': self.line_width_var.get(),
            'padding': self.padding_var.get(),
            'show_gray': self.show_gray_var.get(),
            'ext_left': self.line_ext_left_var.get(),
            'ext_right': self.line_ext_right_var.get(),
            'curve_span_left': self.curve_span_left_var.get(),
            'curve_span_right': self.curve_span_right_var.get(),
            **{k: getattr(self, k) for k in Config.DEFAULT_COLORS}
        }
        return ctx

    # --- 交互控制方法 ---

    def _adjust_zoom(self, factor):
        """ 通过按钮调整缩放比例 """
        new_scale = self.view_scale * factor
        if 0.1 <= new_scale <= 10.0:
            self.view_scale = new_scale
            self.update_zoom_display()
            self.generate(auto_center=False)

    def on_mousewheel(self, event):
        """ 滚轮触发缩放 """
        self.view_scale = max(0.2, min(5.0, getattr(self, 'view_scale', 1.0) * (1.1 if event.delta > 0 else 0.9)))
        self.update_zoom_display()
        self.generate(auto_center=False)

    def update_zoom_display(self):
        """ 更新工具栏上的百分比显示 """
        if hasattr(self, 'zoom_lbl'):
            self.zoom_lbl.config(text=f"{int(self.view_scale * 100)}%")

    def center_view(self):
        """ 将绘图内容自动居中于画布 """
        bbox = self.canvas.bbox("all")
        if not bbox: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        # 3000 是因为我们在 finalize_canvas 中设置了庞大的滚动域基准
        self.canvas.xview_moveto(( (bbox[0]+bbox[2])/2 - cw/2 + 3000 ) / 6000)
        self.canvas.yview_moveto(( (bbox[1]+bbox[3])/2 - ch/2 + 3000 ) / 6000)

    def reset_view(self):
        """ 重置缩放比例与居中视角 """
        self.font_size_var.set(Config.DEFAULT_VALUES['font_size'])
        self.view_scale = 1.0
        self.update_zoom_display()
        self.generate(True)

    def start_pan(self, event): self.canvas.scan_mark(event.x, event.y)
    def do_pan(self, event): self.canvas.scan_dragto(event.x, event.y, gain=1)

    def pick_color(self, attr):
        """ 弹出调色盘修改颜色并重绘 """
        color = colorchooser.askcolor(initialcolor=getattr(self, attr))[1]
        if color:
            setattr(self, attr, color)
            self.generate()

    def reset_colors(self):
        self._load_default_colors()
        self.generate()

    def reset_params(self):
        """ 恢复所有滑块参数到默认值 """
        dv = Config.DEFAULT_VALUES
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
        """ 处理下拉框选择标准多项式的事件 """
        poly = Config.STD_POLYS.get(self.poly_combo.get())
        if poly: self.divisor_var.set(poly); self.generate(True)

    def on_toggle_gray(self):
        """ 处理补零标记开关切换 """
        self.update_ui_states(); self.generate(False)

    def update_ui_states(self):
        """ 根据复选框状态动态启用/禁用相关的颜色按钮 """
        state = tk.NORMAL if self.show_gray_var.get() else tk.DISABLED
        self.btn_bg_block.config(state=state)
        self.btn_bg_digit.config(state=state)

    # --- UI 辅助绘图组件 ---

    def _add_custom_check(self, parent, text, var, command):
        """ 绘制一个现代化、大尺寸的自定义复选框 """
        f = tk.Frame(parent, bg="#ffffff")
        f.pack(anchor=tk.W, pady=(0, Config.LAYOUT['section_pady']))
        sz = Config.LAYOUT['check_size']
        canvas = tk.Canvas(f, width=sz+4, height=sz+4, bg="#ffffff", highlightthickness=0, cursor="hand2")
        canvas.pack(side=tk.LEFT)
        lbl = tk.Label(f, text=text, bg="#ffffff", font=Config.FONTS['zh_normal'], cursor="hand2")
        lbl.pack(side=tk.LEFT, padx=5)
        
        def refresh():
            canvas.delete("all")
            color = Config.LAYOUT['check_color'] if var.get() else "#cbd5e1"
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
        tk.Label(parent, text=label, bg="#ffffff", font=Config.FONTS['zh_normal']).pack(anchor=tk.W, pady=(5, 0))
        var = tk.DoubleVar(value=default) if isinstance(res, float) else tk.IntVar(value=default)
        setattr(self, var_name, var)
        tk.Scale(parent, from_=f, to_=t, resolution=res, orient=tk.HORIZONTAL, variable=var, 
                 sliderlength=Config.LAYOUT['slider_len'], width=Config.LAYOUT['slider_thick'],
                 font=("Times New Roman", 10), bg="#ffffff", highlightthickness=0, 
                 command=lambda x: self.generate(auto_center=False)).pack(fill=tk.X, pady=(0, 10))

    def _add_color_btn(self, parent, text, attr, row, col):
        """ 通用颜色选择按钮封装 """
        btn = tk.Button(parent, text=text, command=lambda: self.pick_color(attr), font=("SimSun", 9), bg="#ffffff")
        btn.grid(row=row, column=col, sticky="ew", padx=1, pady=1)
        parent.grid_columnconfigure(col, weight=1)
        return btn

if __name__ == "__main__":
    # 提升高DPI清晰度（针对 Windows 系统）
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = CRCVisualizerApp(root)
    root.mainloop()