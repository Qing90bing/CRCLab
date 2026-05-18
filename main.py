import ctypes
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk
from PIL import Image, ImageTk, ImageDraw

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.renderer import CanvasRenderer
from view.sidebar import SidebarPanel
from view.export_dialog import ExportDialog

class CRCVisualizerApp:
    """
    CRC Visualizer 应用程序主类。
    
    管理主界面视图与核心渲染管线，通过侧边栏面板进行参数控制交互，
    统一管理状态变量并协调图像的重绘与导出。
    """
    def __init__(self, root):
        self.root = root
        self.root.title(Config.UI_TEXT['title'])
        
        # 1. 初始化核心计算引擎
        self.engine = CRCEngine()
        self.renderer = None
        self.view_scale = 1.0  # 全局缩放比例
        self.photo_img = None  # 强引用保持，防止 Tkinter 图像垃圾回收
        
        # 预先物理渲染大画布的灰白棋盘格背景图
        self.canvas_bg_image_pil = self._create_large_checkerboard()
        self.canvas_bg_image = ImageTk.PhotoImage(self.canvas_bg_image_pil)
        
        # 2. 基础数据状态与配色加载
        self._init_variables()
        self._load_default_colors()
        
        # 3. 基础环境及窗口自适应配置
        self._setup_window_geometry()
        self._setup_styles()
        
        # 4. 构建解耦后的 GUI 界面
        self.setup_ui()
        
        # 5. 执行首次图像渲染生成与居中显示
        self.root.update_idletasks()
        self.generate(auto_center=True)
        self.root.after(100, self.center_view)

    # --- 状态与变量初始化 ---

    def _init_variables(self):
        """ 统一、显式声明所有控制和排版布局相关的 Tkinter 状态变量 """
        dv = Config.DEFAULT_VALUES
        self.data_var = tk.StringVar(value=dv['data'])
        self.divisor_var = tk.StringVar(value=dv['divisor'])
        
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
        """ 配置窗口初始大小及位置（居中显示，并在支持的平台上尝试最大化启动） """
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w = min(Config.LAYOUT['window_max_w'], int(sw * Config.LAYOUT['window_w_ratio']))
        h = min(Config.LAYOUT['window_max_h'], int(sh * Config.LAYOUT['window_h_ratio']))
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.minsize(Config.LAYOUT['window_min_w'], Config.LAYOUT['window_min_h'])
        self.root.configure(bg=Config.COLORS['main_bg'])
        
        try:
            # 尝试以窗口最大化启动
            self.root.state('zoomed')
        except Exception:
            pass

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('vista')
        except Exception:
            pass
            
        # 组件高度对齐配置
        # 对 vista 主题的 Entry、Combobox 和 Button 进行 Padding 微调以使高度对齐
        self.style.configure('TEntry', padding=(10, 7))
        self.style.configure('TCombobox', padding=(10, 6))
        self.style.configure('TCombobox', font=Config.FONTS['combo'])
        
        # 常规按钮样式，统一 padding 配置
        self.style.configure('TButton', font=Config.FONTS['zh_normal'], padding=(10, 5))
        
        # 高亮动作按钮样式，使用粗体并统一 padding 以确保与常规按钮高度等高
        self.style.configure('Action.TButton', font=Config.FONTS['zh_bold'], padding=(10, 5))
        
        # 顶部工具栏按钮样式：
        # 1. 常规文本按钮样式，增加 padding 以利于交互点按
        self.style.configure('Toolbutton', font=Config.FONTS['zh_normal'], padding=(12, 12))
        # 2. 缩放符号按钮样式（-、+），配置较大字号以使加减符号醒目清晰
        self.style.configure('Zoom.Toolbutton', font=Config.FONTS['zoom_btn'], padding=(10, 8))

    # --- UI 构建逻辑 ---

    def setup_ui(self):
        """ 构建整体 UI 框架：左侧解耦参数面板 + 右侧核心画布区域 """
        win_w = self.root.winfo_width()
        if win_w <= 1:
            win_w = min(Config.LAYOUT['default_screen_width_fallback'], int(self.root.winfo_screenwidth() * 0.9))
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
        # 绑定画布大小改变（及首次物理渲染显示事件），动态刷新大底图对齐
        self.canvas.bind("<Configure>", lambda e: self._update_bg_position())

    def _setup_canvas_toolbar(self, parent):
        """ 构建画布上方的浮动控制工具栏 """
        # 使用 1 像素扁平边框，配置内边距实现悬浮工具栏样式
        tb = tk.Frame(
            parent, 
            bg=Config.COLORS['toolbar_bg'], 
            bd=0, 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['border_enabled'], 
            padx=Config.LAYOUT['toolbar_padding_x'], 
            pady=Config.LAYOUT['toolbar_padding_y']
        )
        tb.place(relx=0.5, y=Config.LAYOUT['toolbar_y_offset'], anchor="n")
        
        # 缩放控制区域：包括放大、缩小及当前比例指示标签
        ttk.Button(tb, text="－", command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_out_factor']), 
                   style='Zoom.Toolbutton').pack(side=tk.LEFT, padx=3)
        self.zoom_lbl = tk.Label(tb, text="100%", font=Config.FONTS['zoom_lbl'], 
                                 bg=Config.COLORS['toolbar_bg'], width=6)
        self.zoom_lbl.pack(side=tk.LEFT, padx=4)
        ttk.Button(tb, text="＋", command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_in_factor']), 
                   style='Zoom.Toolbutton').pack(side=tk.LEFT, padx=3)
        
        # 垂直分割线
        tk.Frame(tb, width=1, bg=Config.COLORS['toolbar_divider'], height=Config.LAYOUT['toolbar_divider_height']).pack(side=tk.LEFT, padx=Config.LAYOUT['toolbar_divider_padx'])
        
        # 适应屏幕与重置比例控制按钮
        ttk.Button(tb, text=Config.UI_TEXT['btn_fit'], command=self.center_view, 
                   style='Toolbutton').pack(side=tk.LEFT, padx=4)
        ttk.Button(tb, text=Config.UI_TEXT['btn_reset_view'], command=self.reset_view, 
                   style='Toolbutton').pack(side=tk.LEFT, padx=4)

    # --- 核心渲染驱动与防抖管道 ---

    def generate(self, auto_center=False, force_rebuild=True):
        """ 图像生成主入口，包含防抖处理以合并高频触发事件 """
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
                
        self.root.after(Config.LAYOUT['render_debounce_ms'], run_generation)

    def _actual_generate(self, auto_center=False, force_rebuild=True):
        """ 渲染执行逻辑，通过基准缓存图解耦缩放计算与排版绘制 """
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

        # 1. 在参数数据变化或缓存未初始化时，重新进行内存排版绘制
        if force_rebuild or not getattr(self, 'base_image', None):
            q, rows, dividend = self.engine.calculate(data, divisor)
            ctx = self._get_render_context()
            ctx['view_scale'] = 1.0  # 基础缓存图的渲染物理原尺寸固定为 1.0
            self.base_image = self.renderer.render(data, dividend, divisor, q, rows, ctx)

        # 2. 根据当前缩放比例调整缓存图像尺寸
        vs = getattr(self, 'view_scale', 1.0)
        from PIL import Image, ImageTk # 延迟导入，减少主线程加载负担
        if abs(vs - 1.0) > 1e-4:
            tw = max(1, int(self.base_image.width * vs))
            th = max(1, int(self.base_image.height * vs))
            img = self.base_image.resize((tw, th), Image.Resampling.BILINEAR)
        else:
            img = self.base_image
        
        # 3. 在画布上渲染图像并更新滚动范围
        self.photo_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        
        # 核心数学奥义：获取当前视口中心，并用 15 像素格子对齐，使得背景图大棋盘格在空间中静止且永远铺满
        cx_aligned, cy_aligned = 0, 0
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 10 and h > 10:
            x0 = self.canvas.canvasx(0)
            y0 = self.canvas.canvasy(0)
            cx = x0 + w / 2
            cy = y0 + h / 2
            size = 15
            cx_aligned = int((cx // size) * size)
            cy_aligned = int((cy // size) * size)
            
        # 优先在底层铺设大棋盘格背景图
        self.canvas.create_image(cx_aligned, cy_aligned, image=self.canvas_bg_image, anchor="center", tags="canvas_bg")
        # 贴上长除法算式纸面图
        self.canvas.create_image(0, 0, image=self.photo_img, anchor="center", tags="formula")
        scroll_bound = Config.LAYOUT['canvas_scroll_bound']
        self.canvas.config(scrollregion=(-scroll_bound, -scroll_bound, scroll_bound, scroll_bound))
        
        if auto_center:
            self.center_view()

    def _get_render_context(self):
        """ 收集并返回当前配置变量的渲染上下文字典 """
        ctx = {
            'view_scale': getattr(self, 'view_scale', 1.0),
            'font_size': self.font_size_var.get(),
            'grid_base': Config.GRID_BASE,
            'h_spacing': self.spacing_var.get(),
            'v_spacing': self.v_spacing_var.get(),
            'line_width': self.line_width_var.get(),
            'padding': self.padding_var.get(),
            'show_gray': True,
            'show_border': True,
            'is_preview': True,
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
        self.view_scale = max(Config.LAYOUT['zoom_min'], min(Config.LAYOUT['zoom_mousewheel_max'], getattr(self, 'view_scale', 1.0) * (Config.LAYOUT['zoom_in_factor'] if event.delta > 0 else Config.LAYOUT['zoom_out_factor'])))
        self.update_zoom_display()
        self.generate(auto_center=False, force_rebuild=False)

    def update_zoom_display(self):
        if hasattr(self, 'zoom_lbl'):
            self.zoom_lbl.config(text=f"{int(self.view_scale * 100)}%")

    def center_view(self):
        bbox = self.canvas.bbox("formula")
        if not bbox: return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        scroll_bound = Config.LAYOUT['canvas_scroll_bound']
        self.canvas.xview_moveto(((bbox[0]+bbox[2])/2 - cw/2 + scroll_bound) / (scroll_bound * 2))
        self.canvas.yview_moveto(((bbox[1]+bbox[3])/2 - ch/2 + scroll_bound) / (scroll_bound * 2))
        # 居中平移视口后，立即重新更新背景棋盘格图元的位置
        self._update_bg_position()

    def reset_view(self):
        self.view_scale = 1.0
        self.update_zoom_display()
        self.generate(True, force_rebuild=False)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._update_bg_position()

    def _update_bg_position(self):
        """ 动态计算视区几何中心并对齐格子，使背景图永远稳定铺满视口且格底静止 """
        if hasattr(self, 'canvas') and self.canvas.find_withtag("canvas_bg"):
            x0 = self.canvas.canvasx(0)
            y0 = self.canvas.canvasy(0)
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w > 10 and h > 10:
                cx = x0 + w / 2
                cy = y0 + h / 2
                size = 15
                cx_aligned = int((cx // size) * size)
                cy_aligned = int((cy // size) * size)
                self.canvas.coords("canvas_bg", cx_aligned, cy_aligned)

    def pick_color(self, attr):
        """ 打开系统调色板选择颜色，并同步更新侧边栏预览色块与画布 """
        init_color = getattr(self, attr)
        if init_color in ("transparent", "none"):
            init_color = "#ffffff"
        color = colorchooser.askcolor(initialcolor=init_color)[1]
        if color:
            setattr(self, attr, color)
            self.sidebar.update_swatches()
            self.generate()

    def on_transparent_toggle(self, attr, is_trans, recovery_color=None):
        """ 响应色彩透明状态切换回调，并重绘图解 """
        if is_trans:
            setattr(self, attr, "transparent")
        else:
            setattr(self, attr, recovery_color if recovery_color else "#ffffff")
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



    def open_export_dialog(self):
        """ 打开导出配置对话框 """
        ExportDialog(self)

    def _create_large_checkerboard(self, w=3000, h=3000, size=15):
        """ 在大画布的背景图像上平铺柔和灰白相间的棋盘格，指示透明底层 """
        img = Image.new("RGBA", (w, h), "#ffffff")
        draw = ImageDraw.Draw(img)
        for x in range(0, w, size):
            for y in range(0, h, size):
                if ((x // size) + (y // size)) % 2 == 1:
                    # 使用极其柔雅的配置
                    draw.rectangle([x, y, x + size - 1, y + size - 1], fill="#f1f5f9", outline=None)
        return img

if __name__ == "__main__":
    # Windows 系统高 DPI 适配
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    root = tk.Tk()
    app = CRCVisualizerApp(root)
    root.mainloop()