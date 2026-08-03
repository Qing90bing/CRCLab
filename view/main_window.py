import ctypes
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk
from PIL import Image, ImageTk

import os
import sys

# 动态确保项目根目录在 sys.path 中，防范直接运行此脚本时的模块导入错误
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 解除 PIL 最大像素限制，确保超高分辨率导出（例如 4 倍放大时）不会因为像素总数超限而抛出 DecompressionBombError
Image.MAX_IMAGE_PIXELS = None

# 导入自定义模块
from core.engine import CRCEngine
from config.constants import Config
from view.components.checkerboard import create_checkerboard_image
from view.components.renderer import CanvasRenderer
from view.panels.sidebar import SidebarPanel
from view.dialogs.export_dialog import ExportDialog
from view.panels.dashboard import DashboardPanel
from view.components.toolbar import CanvasToolbar
from view.components.interactive_canvas import InteractiveCanvas

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
        
        # 灰白棋盘格背景图：先初始化占位，窗口几何确定后由 _setup_checkerboard_background 动态生成
        self.canvas_bg_image_pil = None
        self.canvas_bg_image = None
        
        # 2. 基础数据状态与配色加载
        self._init_variables()
        self._load_default_colors()
        
        # 3. 基础环境及窗口自适应配置
        self._setup_window_geometry()
        self._setup_styles()
        self._setup_checkerboard_background()
        
        # 4. 构建解耦后的 GUI 界面
        self.setup_ui()
        
        # 5. 执行首次图像渲染生成与居中显示
        self.root.update_idletasks()
        self.generate(auto_center=True)
        self.root.after(100, self.canvas.center_view)

    def _setup_window_icon(self):
        """ 安全地设置窗口及任务栏高清图标 """
        # 兼容单文件打包和常规运行环境，动态定位绝对路径，防范 CWD 漂移的影响
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        self.calc_mode_var = tk.StringVar(value="encode") # encode (发送端补零编码) | verify (接收端校验)
        
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
            # 尝试以窗口最大化启动（Windows/Mac）
            self.root.state('zoomed')
        except Exception:
            try:
                # 兼容 Linux X11 环境的最大化
                self.root.attributes('-zoomed', True)
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
        
        # 修复复选框、单选框与原生 LabelFrame 标题默认英文字体的问题
        self.style.configure('TCheckbutton', font=Config.FONTS['zh_normal'])
        self.style.configure('TRadiobutton', font=Config.FONTS['zh_normal'])
        self.style.configure('TLabelframe.Label', font=Config.FONTS['zh_bold'])
        self.style.configure('TLabel', font=Config.FONTS['zh_normal'])
        
        # 终极保险：强行接管系统中所有原生 Tk 组件及 Combobox 弹出列表的字体
        self.root.option_add('*Font', Config.FONTS['zh_normal'])
        
        # 常规按钮样式，统一 padding 配置
        self.style.configure('TButton', font=Config.FONTS['zh_normal'], padding=(20, 8))
        
        # 高亮动作按钮样式，统一 padding 以确保与常规按钮高度等高
        self.style.configure('Action.TButton', font=Config.FONTS['zh_normal'], padding=(20, 8))
        
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
        
        self.canvas = InteractiveCanvas(cont, self, bg=Config.COLORS['canvas_default_bg'], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.toolbar = CanvasToolbar(
            cont,
            on_zoom_in=lambda: self.canvas.adjust_zoom(Config.LAYOUT['zoom_in_factor']),
            on_zoom_out=lambda: self.canvas.adjust_zoom(Config.LAYOUT['zoom_out_factor']),
            on_reset_view=self.canvas.reset_view,
            on_fit_view=self.canvas.fit_view,
            on_toggle_drag_mode=self.canvas.toggle_drag_mode
        )
        
        # 绑定物理平移及滚轮缩放事件由 InteractiveCanvas 内部接管
        self.renderer = CanvasRenderer(self.canvas)
        
        # 2. 底部的实时解析看板
        self.dashboard = DashboardPanel(self.right_container, self)
        self.dashboard.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    # --- 核心渲染驱动与防抖管道 ---

    def generate(self, auto_center=False):
        """ 图像生成主入口，包含防抖处理以合并高频触发事件 """
        if getattr(self, '_render_pending', False):
            # 正在渲染：记录最新请求，当前轮结束后补跑一次，避免防抖合并丢失最终输入
            self._next_auto_center = auto_center
            self._render_requested_again = True
            return
            
        self._render_pending = True
        self._render_requested_again = False
        self._next_auto_center = auto_center
        
        def run_generation():
            try:
                self._actual_generate(self._next_auto_center)
            finally:
                self._render_pending = False
                if getattr(self, '_render_requested_again', False):
                    self._render_requested_again = False
                    self.generate(auto_center=self._next_auto_center)
                
        self.root.after(Config.LAYOUT['render_debounce_ms'], run_generation)

    def calculate_current(self, data, divisor):
        """
        根据当前选择的计算模式 (encode / verify) 执行相应的 CRC 算法计算，
        统一返回用于渲染与导出的元组 (q, rows, dividend)。
        """
        mode = getattr(self, 'calc_mode_var', None)
        if mode and mode.get() == "verify":
            q, rows, dividend, _, _ = self.engine.verify(data, divisor)
        else:
            q, rows, dividend = self.engine.calculate(data, divisor)
        return q, rows, dividend

    def _actual_generate(self, auto_center=False):
        """ 渲染执行逻辑，以当前实际的缩放比例 view_scale 进行绝对高清晰的矢量级内存重绘 """
        data = self.data_var.get().strip()
        divisor = self.divisor_var.get().strip()
        
        if not data:
            self.sidebar.show_input_error(self.sidebar.data_entry, "数据位不能为空！")
            return
        if not divisor:
            self.sidebar.show_input_error(self.sidebar.poly_entry, "多项式不能为空！")
            return
            
        if not all(c in '01' for c in data):
            self.sidebar.show_input_error(self.sidebar.data_entry, Config.MESSAGES['warning_invalid_binary'])
            return
        if not all(c in '01' for c in divisor):
            self.sidebar.show_input_error(self.sidebar.poly_entry, Config.MESSAGES['warning_invalid_binary'])
            return
            
        if divisor[0] == '0':
            self.sidebar.show_input_error(self.sidebar.poly_entry, Config.MESSAGES['warning_poly_first_bit_1'])
            return
        if len(divisor) < 2:
            self.sidebar.show_input_error(self.sidebar.poly_entry, Config.MESSAGES['warning_poly_len_min_2'])
            return

        # 1. 运行二进制 CRC 算法计算引擎 (自动适应当前选择的 encode / verify 模式)
        q, rows, dividend = self.calculate_current(data, divisor)
        
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

        scroll_bound = Config.LAYOUT['canvas_scroll_bound']
        self.canvas.config(scrollregion=(-scroll_bound, -scroll_bound, scroll_bound, scroll_bound))

        # 棋盘格背景为“屏幕静止”贴图：先创建，再由 update_bg_position 锚定到当前视口中心。
        # 平移/缩放时它相对窗口不动，只有算式图纸随之移动（符合常见绘图软件习惯）。
        self.canvas.create_image(0, 0, image=self.canvas_bg_image, anchor="center", tags="canvas_bg")
        self.canvas.update_bg_position()

        # 贴上长除法算式纸面图
        self.canvas.create_image(0, 0, image=self.photo_img, anchor="center", tags="formula")

        if auto_center:
            self.canvas.center_view()
            
        # 5. 实时刷新底部解析看板
        self.dashboard.update_data(data, divisor, q, rows)

        # 6. 同步侧边栏“补零/校验码高亮”开关状态（在渲染成功后，与最终结果保持一致）：
        # 校验模式且检测无错误 → 补零背景块与加粗均无效，置灰不可点击；其余情况启用
        mode = getattr(self, 'calc_mode_var', None)
        is_verify = bool(mode and mode.get() == "verify")
        has_error = False
        if is_verify and rows and rows[-1]['type'] == 'remainder':
            has_error = any(c == '1' for c in rows[-1]['val'])
        if hasattr(self, 'sidebar'):
            self.sidebar.set_padding_feature_state(not is_verify or has_error)


    def _get_render_context(self):
        """ 收集并返回当前配置变量的渲染上下文字典 """
        mode = getattr(self, 'calc_mode_var', None)
        ctx = {
            'view_scale': getattr(self, 'view_scale', 1.0),
            'is_verify': bool(mode and mode.get() == "verify"),
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

    def on_calc_mode_changed(self):
        """ 响应工作模式切换 (发送端编码 vs 接收端校验) """
        mode = self.calc_mode_var.get()
        if hasattr(self.sidebar, 'data_lbl'):
            if mode == "verify":
                self.sidebar.data_lbl.config(text="接收数据帧:")
            else:
                self.sidebar.data_lbl.config(text=Config.UI_TEXT['data_label'])
        self.generate(auto_center=True)

    def open_export_dialog(self):
        """ 打开导出配置对话框 """
        ExportDialog(self)


    def _checkerboard_base_size(self):
        """ 计算棋盘格背景的基准（最小）尺寸：需同时盖满导出预览对话框与主画布视口 """
        margin = Config.CHECKERBOARD['size_margin']
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * Config.LAYOUT['export_dialog_w_ratio']) + margin
        h = int(sh * Config.LAYOUT['export_dialog_h_ratio']) + margin
        return w, h

    def _setup_checkerboard_background(self):
        """ 动态生成灰白棋盘格背景图：基准尺寸覆盖导出预览对话框（0.75×屏幕） + 安全余量，并由 create_checkerboard_image 做相位对齐 """
        floor_w, floor_h = self._checkerboard_base_size()
        self.canvas_bg_image_pil = create_checkerboard_image(floor_w, floor_h)
        self.canvas_bg_image = ImageTk.PhotoImage(self.canvas_bg_image_pil)

    def ensure_checkerboard_size(self, w, h):
        """ 按需扩容 / 滞回缩容背景图：扩容后窗口缩回会自动释放内存，重建保持棋盘格相位稳定 """
        if self.canvas_bg_image_pil is None:
            return
        img_w, img_h = self.canvas_bg_image_pil.size
        margin = Config.CHECKERBOARD['size_margin']
        floor_w, floor_h = self._checkerboard_base_size()
        need_w = max(w + margin, floor_w)
        need_h = max(h + margin, floor_h)

        if w > img_w or h > img_h:
            # 扩容：视口超出图片边缘 → 新尺寸 = max(需求, 当前) 并留足缓冲
            new_w = max(need_w, img_w)
            new_h = max(need_h, img_h)
        elif img_w > need_w * 2 or img_h > need_h * 2:
            # 滞回缩容：图片比需求大一倍以上才重建缩小，避免拖动窗口时反复重建
            new_w = need_w
            new_h = need_h
        else:
            return

        self.canvas_bg_image_pil = create_checkerboard_image(new_w, new_h)
        self.canvas_bg_image = ImageTk.PhotoImage(self.canvas_bg_image_pil)
        if self.canvas.find_withtag("canvas_bg"):
            self.canvas.itemconfig("canvas_bg", image=self.canvas_bg_image)
