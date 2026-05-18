import os
import ctypes
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.renderer import CanvasRenderer
from view.sidebar import SidebarPanel
from view.export_dialog import ExportDialog

class CRCVisualizerApp:
    """
    CRC Visualizer 应用程序主类。
    
    采用简洁优雅的 MVP/MVC 架构控制层，将臃肿的侧边栏 UI 布局彻底外包给 view/sidebar.py，
    统一、显式地管理全部排版及数据控制变量，提供极快、极清的高保真渲染交互体验。
    """
    def __init__(self, root):
        self.root = root
        self.root.title(Config.UI_TEXT['title'])
        
        # 1. 初始化核心计算引擎
        self.engine = CRCEngine()
        self.renderer = None
        self.view_scale = 1.0  # 全局缩放比例
        self.photo_img = None  # 强引用保持，防止 Tkinter 图像垃圾回收
        
        # 2. 基础数据状态与配色加载
        self._init_variables()
        self._load_default_colors()
        
        # 3. 基础环境及窗口自适应配置
        self._setup_window_geometry()
        self._setup_styles()
        
        # 4. 构建解耦后的 GUI 界面
        self.setup_ui()
        
        # 5. 启动自验证生成与首帧居中
        self.root.update_idletasks()
        self.update_ui_states()
        self.generate(auto_center=True)
        self.root.after(100, self.center_view)

    # --- 状态与变量初始化 ---

    def _init_variables(self):
        """ 统一、显式声明所有控制和排版布局相关的 Tkinter 状态变量 """
        dv = Config.DEFAULT_VALUES
        self.data_var = tk.StringVar(value=dv['data'])
        self.divisor_var = tk.StringVar(value=dv['divisor'])
        self.show_gray_var = tk.BooleanVar(value=dv['show_gray'])
        
        # 物理排版参数微调变量
        self.font_size_var = tk.IntVar(value=dv['font_size'])
        self.spacing_var = tk.DoubleVar(value=dv['h_spacing'])
        self.v_spacing_var = tk.DoubleVar(value=dv['v_spacing'])
        self.line_width_var = tk.IntVar(value=dv['line_width'])
        self.padding_var = tk.IntVar(value=dv['padding'])
        self.line_ext_left_var = tk.DoubleVar(value=dv['ext_left'])
        self.line_ext_right_var = tk.DoubleVar(value=dv['ext_right'])
        self.curve_span_left_var = tk.DoubleVar(value=dv['span_left'])
        self.curve_span_right_var = tk.DoubleVar(value=dv['span_right'])

    def _load_default_colors(self):
        """ 从配置中心加载默认颜色属性 """
        for attr, color in Config.DEFAULT_COLORS.items():
            setattr(self, attr, color)

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

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TCombobox', padding=Config.LAYOUT['entry_ipady'])
        self.style.configure('TCombobox', font=Config.FONTS['combo'])

    # --- UI 构建逻辑 ---

    def setup_ui(self):
        """ 构建整体 UI 框架：左侧解耦参数面板 + 右侧核心画布区域 """
        win_w = self.root.winfo_width()
        if win_w <= 1:
            win_w = min(1600, int(self.root.winfo_screenwidth() * 0.9))
        side_w = max(Config.LAYOUT['min_side_width'], int(win_w * Config.LAYOUT['side_ratio']))
        
        # 1. 挂载解耦的控制侧边栏视图
        self.sidebar = SidebarPanel(self.root, self, side_w)
        
        # 2. 构建右侧核心画布展示区
        self._setup_canvas_area()

    def _setup_canvas_area(self):
        """ 构建右侧核心展示画布区域 """
        cont = tk.Frame(self.root, bg=Config.LAYOUT['canvas_bg'], bd=2)
        cont.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.canvas = tk.Canvas(cont, bg=Config.COLORS['canvas_default_bg'], highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self._setup_canvas_toolbar(cont)
        
        # 绑定物理平移及滚轮缩放事件
        self.renderer = CanvasRenderer(self.canvas)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def _setup_canvas_toolbar(self, parent):
        """ 构建悬浮于画布上方的现代化浮动控制工具栏 """
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

    # --- 核心渲染驱动与防抖管道 ---

    def generate(self, auto_center=False, force_rebuild=True):
        """ 核心生成入口：采用双通道缓存加速，15ms 智能防抖合并滑块拖拽 """
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
                
        self.root.after(15, run_generation)

    def _actual_generate(self, auto_center=False, force_rebuild=True):
        """ 实际的渲染物理管线：利用基准大图缓存，将缩放视角与排版重绘深度解耦 """
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

        # 1. 仅在参数数据实际变化，或缓存未初始化时，才重新进行 SSAA 内存排版绘制
        if force_rebuild or not getattr(self, 'base_image', None):
            q, rows, dividend = self.engine.calculate(data, divisor)
            ctx = self._get_render_context()
            ctx['view_scale'] = 1.0  # 基础缓存图的渲染物理原尺寸固定为 1.0
            self.base_image = self.renderer.render(data, dividend, divisor, q, rows, ctx)

        # 2. 从极其轻量级的内存缓存中直接根据当前 view_scale 极速缩放视角
        vs = getattr(self, 'view_scale', 1.0)
        from PIL import Image, ImageTk # 延迟导入，减少主线程加载负担
        if abs(vs - 1.0) > 1e-4:
            tw = max(1, int(self.base_image.width * vs))
            th = max(1, int(self.base_image.height * vs))
            img = self.base_image.resize((tw, th), Image.Resampling.BILINEAR)
        else:
            img = self.base_image
        
        # 3. 贴在 Canvas 中央并更新视口范围
        self.photo_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.config(bg=self.canvas_bg_color)
        self.canvas.create_image(0, 0, image=self.photo_img, anchor="center")
        self.canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
        
        if auto_center:
            self.center_view()

    def _get_render_context(self):
        """ 收集并返回当前配置变量的精细渲染上下文字典 """
        ctx = {
            'view_scale': getattr(self, 'view_scale', 1.0),
            'font_size': self.font_size_var.get(),
            'grid_base': Config.GRID_BASE,
            'h_spacing': self.spacing_var.get(),
            'v_spacing': self.v_spacing_var.get(),
            'line_width': self.line_width_var.get(),
            'padding': self.padding_var.get(),
            'show_gray': self.show_gray_var.get(),
            'show_border': True,
            'ext_left': self.line_ext_left_var.get(),
            'ext_right': self.line_ext_right_var.get(),
            'curve_span_left': self.curve_span_left_var.get(),
            'curve_span_right': self.curve_span_right_var.get(),
            **{k: getattr(self, k) for k in Config.DEFAULT_COLORS}
        }
        return ctx

    # --- 交互事件处理 ---

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
        self.view_scale = 1.0
        self.update_zoom_display()
        self.generate(True, force_rebuild=False)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def pick_color(self, attr):
        """ 唤起系统色彩盘挑选色值，并同步更新侧边栏预览色块与物理 Canvas 重绘 """
        color = colorchooser.askcolor(initialcolor=getattr(self, attr))[1]
        if color:
            setattr(self, attr, color)
            self.sidebar.update_swatches()
            self.generate()

    def reset_colors(self):
        self._load_default_colors()
        self.sidebar.update_swatches()
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
        poly = Config.STD_POLYS.get(self.sidebar.poly_combo.get())
        if poly:
            self.divisor_var.set(poly)
            self.generate(True)

    def on_toggle_gray(self):
        self.update_ui_states()
        self.generate(False)

    def update_ui_states(self):
        is_gray_enabled = self.show_gray_var.get()
        if hasattr(self, 'sidebar'):
            self.sidebar.update_states(is_gray_enabled)

    def open_export_dialog(self):
        """ 唤起高保真导出配置对话框 """
        ExportDialog(self)

if __name__ == "__main__":
    # Windows 系统高 DPI 物理缩放拉伸清晰度补强
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = CRCVisualizerApp(root)
    root.mainloop()