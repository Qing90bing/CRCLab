import ctypes
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk
from PIL import Image, ImageTk, ImageDraw

# 解除 PIL 最大像素限制，确保超高分辨率导出（例如 4 倍放大时）不会因为像素总数超限而抛出 DecompressionBombError
Image.MAX_IMAGE_PIXELS = None

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.renderer import CanvasRenderer
from view.sidebar import SidebarPanel
from view.export_dialog import ExportDialog
from view.dashboard import DashboardPanel

class CRCLabApp:
    """
    CRCLab 应用程序主类。
    
    管理主界面视图与核心渲染管线，通过侧边栏面板进行参数控制交互，
    统一管理状态变量并协调图像的重绘与导出。
    """
    def __init__(self, root):
        self.root = root
        self.root.title(Config.UI_TEXT['title'])
        
        # 加载并配置窗口/任务栏图标
        self._setup_window_icon()
        
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

    def _setup_window_icon(self):
        """ 安全地设置窗口及任务栏高清图标 """
        import os
        import sys
        
        # 兼容单文件打包和常规运行环境，动态定位绝对路径，防范 CWD 漂移的影响
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_ico = os.path.join(base_dir, "resources", "app_icon.ico")
        icon_png = os.path.join(base_dir, "resources", "app_icon.png")
        
        try:
            # Windows 任务栏高分辨率 App ID 适配，防止任务栏显示 Python 默认的“蟒蛇”图标
            import ctypes
            myappid = f"{Config.AUTHOR}.CRCLab.version.{Config.VERSION}"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        try:
            if os.path.exists(icon_png):
                self.app_icon_img = ImageTk.PhotoImage(file=icon_png)
                self.root.iconphoto(True, self.app_icon_img)
            elif os.path.exists(icon_ico):
                self.root.iconbitmap(icon_ico)
        except Exception:
            pass

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
        self.bold_zeros_var = tk.BooleanVar(value=dv.get('bold_zeros', False))
        self.bold_divisor_var = tk.BooleanVar(value=dv.get('bold_divisor', False))
        self.bold_quotient_var = tk.BooleanVar(value=dv.get('bold_quotient', False))
        self.bold_dividend_var = tk.BooleanVar(value=dv.get('bold_dividend', False))

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
        # 下拉框使用主题默认尺寸，避免全局 padding/font 覆盖导致各处高度被定制化撑大。
        self.style.configure('TEntry', padding=(10, 7))
        
        # 修复复选框与原生 LabelFrame 标题默认英文字体的问题
        self.style.configure('TCheckbutton', font=Config.FONTS['zh_normal'])
        self.style.configure('TLabelframe.Label', font=Config.FONTS['zh_bold'])
        self.style.configure('TLabel', font=Config.FONTS['zh_normal'])
        
        # 终极保险：强行接管系统中所有原生 Tk 组件及 Combobox 弹出列表的字体
        self.root.option_add('*Font', Config.FONTS['zh_normal'])
        
        # 常规按钮样式，统一 padding 配置
        self.style.configure('TButton', font=Config.FONTS['zh_normal'], padding=(10, 5))
        
        # 高亮动作按钮样式，统一 padding 以确保与常规按钮高度等高
        self.style.configure('Action.TButton', font=Config.FONTS['zh_normal'], padding=(10, 5))
        
        # 顶部浮动工具栏按钮样式（不再使用，改用原生 tk.Button）

    # --- UI 构建逻辑 ---

    def setup_ui(self):
        """ 构建整体 UI 框架：左侧解耦参数面板 + 右侧核心画布及解析看板区域 """
        win_w = self.root.winfo_width()
        if win_w <= 1:
            win_w = min(Config.LAYOUT['default_screen_width_fallback'], int(self.root.winfo_screenwidth() * 0.9))
        side_w = max(Config.LAYOUT['min_side_width'], int(win_w * Config.LAYOUT['side_ratio']))
        
        # 1. 挂载解耦的控制侧边栏视图
        self.sidebar = SidebarPanel(self.root, self, side_w)
        
        # 2. 构建右侧核心画布及解析看板区域
        self._setup_right_area()

    def _setup_right_area(self):
        """ 构建右侧主容器及其内部结构 """
        # 右侧的整体垂直排列容器
        self.right_container = tk.Frame(self.root, bg=Config.COLORS['main_bg'])
        self.right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        # 1. 顶部的核心展示画布容器，采用原有的黑色高科技底板色
        cont = tk.Frame(self.right_container, bg=Config.LAYOUT['canvas_bg'], bd=2)
        cont.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
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
        
        # 2. 底部的实时解析看板
        self.dashboard = DashboardPanel(self.right_container, self)
        self.dashboard.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def _setup_canvas_toolbar(self, parent):
        """ 构建画布上方的浮动控制工具栏，采用 Windows 原生按钮风格 """
        tb = tk.Frame(
            parent,
            bg=Config.COLORS['toolbar_bg'],
            bd=0,
            highlightthickness=1,
            highlightbackground='#000000',
            padx=Config.LAYOUT['toolbar_padding_x'],
            pady=Config.LAYOUT['toolbar_padding_y']
        )
        tb.place(relx=0.5, y=Config.LAYOUT['toolbar_y_offset'], anchor="n")

        # 通用原生按钮样式参数
        btn_cfg = {
            'bg': Config.COLORS['toolbar_bg'],
            'activebackground': '#e2e8f0',
            'bd': 0,
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'font': Config.FONTS['zh_normal'],
            'padx': 10,
            'pady': 4,
        }

        # 1. 放大按钮
        tk.Button(tb, text=Config.UI_TEXT['btn_zoom_in'],
                  command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_in_factor']),
                  **btn_cfg).pack(side=tk.LEFT, padx=2)

        # 2. 当前缩放百分比指示标签
        self.zoom_lbl = tk.Label(
            tb, text="100%", font=Config.FONTS['zoom_lbl'],
            bg=Config.COLORS['toolbar_bg'], width=6
        )
        self.zoom_lbl.pack(side=tk.LEFT, padx=4)

        # 3. 缩小按钮
        tk.Button(tb, text=Config.UI_TEXT['btn_zoom_out'],
                  command=lambda: self._adjust_zoom(Config.LAYOUT['zoom_out_factor']),
                  **btn_cfg).pack(side=tk.LEFT, padx=2)

        # 垂直分割线
        tk.Frame(
            tb, width=1, bg=Config.COLORS['toolbar_divider'],
            height=Config.LAYOUT['toolbar_divider_height']
        ).pack(side=tk.LEFT, padx=Config.LAYOUT['toolbar_divider_padx'])

        # 4. 拖动模式切换按钮（按下后保持 SUNKEN 凹陷状态）
        self._drag_mode = True  # 默认启用拖动模式
        self.drag_btn = tk.Button(
            tb, text=Config.UI_TEXT['btn_drag'],
            command=self._toggle_drag_mode,
            **{**btn_cfg, 'relief': tk.SUNKEN, 'bg': '#0078d4', 'fg': '#ffffff', 'activebackground': '#005a9e', 'activeforeground': '#ffffff'}
        )
        self.drag_btn.pack(side=tk.LEFT, padx=2)

        # 5. 重置 100% 比例按钮
        tk.Button(tb, text=Config.UI_TEXT['btn_reset_view'],
                  command=self.reset_view, **btn_cfg).pack(side=tk.LEFT, padx=2)

        # 6. 适应窗口按钮
        tk.Button(tb, text=Config.UI_TEXT['btn_fit'],
                  command=self.fit_view, **btn_cfg).pack(side=tk.LEFT, padx=2)

        # 绑定悬浮显灰效果 (官方 API 颜色 SystemButtonFace)
        def on_enter(e):
            btn = e.widget
            if btn == getattr(self, 'drag_btn', None) and getattr(self, '_drag_mode', False):
                return
            btn.config(bg='SystemButtonFace')
            
        def on_leave(e):
            btn = e.widget
            if btn == getattr(self, 'drag_btn', None) and getattr(self, '_drag_mode', False):
                return
            btn.config(bg=Config.COLORS['toolbar_bg'])

        for child in tb.winfo_children():
            if isinstance(child, tk.Button):
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)

    # --- 核心渲染驱动与防抖管道 ---

    def generate(self, auto_center=False):
        """ 图像生成主入口，包含防抖处理以合并高频触发事件 """
        if getattr(self, '_render_pending', False):
            self._next_auto_center = auto_center
            return
            
        self._render_pending = True
        self._next_auto_center = auto_center
        
        def run_generation():
            try:
                self._actual_generate(self._next_auto_center)
            finally:
                self._render_pending = False
                
        self.root.after(Config.LAYOUT['render_debounce_ms'], run_generation)

    def _actual_generate(self, auto_center=False):
        """ 渲染执行逻辑，以当前实际的缩放比例 view_scale 进行绝对高清晰的矢量级内存重绘 """
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

        # 1. 运行二进制 CRC 算法计算引擎
        q, rows, dividend = self.engine.calculate(data, divisor)
        
        # 2. 收集排版环境字典（此时已包含当前真实的 view_scale 缩放参数）
        ctx = self._get_render_context()
        
        # 3. 委托 CanvasRenderer 以当前真实尺寸进行百分之百清晰的矢量渲染，彻底消灭位图拉伸模糊
        renderer = self.renderer
        if renderer is None:
            return
        img = renderer.render(data, dividend, divisor, q, rows, ctx)
        
        # 4. 在画布上渲染图像并更新滚动范围
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
            
        # 5. 实时刷新底部解析看板
        self.dashboard.update_data(data, divisor, q, rows)

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
            'bold_zeros': self.bold_zeros_var.get(),
            'bold_divisor': self.bold_divisor_var.get(),
            'bold_quotient': self.bold_quotient_var.get(),
            'bold_dividend': self.bold_dividend_var.get(),
            **{k: getattr(self, k) for k in Config.DEFAULT_COLORS}
        }
        return ctx

    # --- 交互事件处理 ---

    def _adjust_zoom(self, factor):
        new_scale = self.view_scale * factor
        if Config.LAYOUT['zoom_min'] <= new_scale <= Config.LAYOUT['zoom_max']:
            self.view_scale = new_scale
            self.update_zoom_display()
            self.generate(auto_center=False)

    def on_mousewheel(self, event):
        self.view_scale = max(Config.LAYOUT['zoom_min'], min(Config.LAYOUT['zoom_mousewheel_max'], getattr(self, 'view_scale', 1.0) * (Config.LAYOUT['zoom_in_factor'] if event.delta > 0 else Config.LAYOUT['zoom_out_factor'])))
        self.update_zoom_display()
        self.generate(auto_center=False)

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

    def fit_view(self):
        """ 自动计算最佳缩放比例，使图解完整显示在当前画布可视区域内 """
        if not hasattr(self, 'photo_img') or not self.photo_img:
            return
            
        # 预留 40 像素的内边距，防止图像完全贴边
        cw = self.canvas.winfo_width() - 40
        ch = self.canvas.winfo_height() - 40
        
        if cw <= 0 or ch <= 0:
            return
            
        # 还原计算 view_scale=1.0 时的原始逻辑尺寸
        orig_w = self.photo_img.width() / self.view_scale
        orig_h = self.photo_img.height() / self.view_scale
        
        if orig_w <= 0 or orig_h <= 0:
            return
            
        # 按照宽高计算缩放比例，取较小值以保证两个方向都能放下
        target_scale = min(cw / orig_w, ch / orig_h)
        
        # 将缩放比例限制在配置允许的最小与最大范围内
        target_scale = max(Config.LAYOUT['zoom_min'], min(Config.LAYOUT['zoom_max'], target_scale))
        
        self.view_scale = target_scale
        self.update_zoom_display()
        self.generate(auto_center=True)

    def reset_view(self):
        self.view_scale = 1.0
        self.update_zoom_display()
        self.generate(auto_center=True)

    def _toggle_drag_mode(self):
        """ 切换拖动模式的开关状态，并更新按钮视觉 """
        self._drag_mode = not self._drag_mode
        if self._drag_mode:
            self.drag_btn.config(relief=tk.SUNKEN, bg='#0078d4', fg='#ffffff')
            self.canvas.config(cursor="hand2")
        else:
            self.drag_btn.config(relief=tk.FLAT, bg=Config.COLORS['toolbar_bg'], fg='black')
            self.canvas.config(cursor="")

    def start_pan(self, event):
        if not getattr(self, '_drag_mode', True):
            return
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        if not getattr(self, '_drag_mode', True):
            return
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
            'ext_right': 'line_ext_right_var', 'span_left': 'curve_span_left_var', 'span_right': 'curve_span_right_var',
            'bold_zeros': 'bold_zeros_var', 'bold_divisor': 'bold_divisor_var',
            'bold_quotient': 'bold_quotient_var', 'bold_dividend': 'bold_dividend_var'
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
    app = CRCLabApp(root)
    root.mainloop()
