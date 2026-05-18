import os
import io
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from config.constants import Config
from view.widgets import ModernCheckbutton
from view.svg_renderer import SVGRenderer

class ExportDialog:
    """
    导出图表弹出对话框类。
    
    采用高内聚设计，将原本混杂在 main.py 中的导出 UI 构建、
    实时高保真预览重绘、以及多倍率物理图像输出逻辑完全抽离，实现 SRP 单一职责原则。
    使用 view/widgets.py 通用组件以消减大量重复的 Canvas 复选框几何重绘。
    """
    def __init__(self, app):
        """
        初始化并打开导出对话框。
        :param app: 主应用程序实例，用于共享数据和渲染器。
        """
        self.app = app
        self._calc_timer = None
        self.dlg = tk.Toplevel(app.root)
        self.dlg.title(Config.UI_TEXT['export_title'])
        self.dlg.transient(app.root)
        
        self._setup_geometry()
        self._build_layout()
        self._setup_bindings()
        
        # 首次同步与双通道防闪烁定位延迟居中，确保初始化呈现正常
        self._update_preview()
        self.dlg.after(100, self._update_preview)

    def _setup_geometry(self):
        """ 智能自适应屏幕分辨率并居中显示，使用统一的布局比例 """
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()
        w = min(Config.LAYOUT['export_max_w'], int(sw * Config.LAYOUT['export_dialog_w_ratio']))
        h = min(Config.LAYOUT['export_max_h'], int(sh * Config.LAYOUT['export_dialog_h_ratio']))
        self.dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.dlg.minsize(Config.LAYOUT['export_min_w'], Config.LAYOUT['export_min_h'])

    def _build_layout(self):
        """ 构建导出界面的双栏框架，背景颜色和边距提取自统一配置中心 """
        self.left_frame = tk.Frame(self.dlg, bg=Config.LAYOUT['export_preview_bg'], padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(
            self.dlg, 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            padx=16, 
            pady=16, 
            width=Config.LAYOUT['export_side_width']
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)
        
        self._init_preview_frame(self.left_frame)
        self._init_control_frame(self.right_frame)

    def _init_preview_frame(self, parent):
        """ 初始化左侧的高清实时重绘预览面板 """
        tk.Label(
            parent, 
            text=Config.UI_TEXT['export_preview'], 
            bg=Config.LAYOUT['export_preview_bg'], 
            font=Config.FONTS['zh_bold']
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.preview_canvas = tk.Canvas(
            parent, 
            bg=Config.COLORS['preview_canvas_bg'], 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['preview_canvas_border']
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def _init_control_frame(self, parent):
        """ 构建右侧的全部控制参数表单及触发按钮 """
        tk.Label(
            parent, 
            text=Config.UI_TEXT['export_params'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_bold']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 1. 初始化业务状态变量，完全采用配置中心的 EXPORT_VALUES
        self.fmt_var = tk.StringVar(value=Config.EXPORT_VALUES['format'])
        self.quality_var = tk.StringVar(value=Config.EXPORT_VALUES['quality'])
        self.dpi_var = tk.IntVar(value=Config.EXPORT_VALUES['dpi'])
        self.color_var = tk.StringVar(value=Config.EXPORT_VALUES['color'])
        self.border_var = tk.BooleanVar(value=Config.EXPORT_VALUES['show_border'])
        self.dir_mode_var = tk.StringVar(value=Config.EXPORT_VALUES['dir_mode'])
        self.custom_dir_var = tk.StringVar(value=Config.EXPORT_VALUES['custom_dir'])
 
        # 2. 绑定下拉菜单的元数据集合，完全来自于配置中心的 EXPORT_OPTIONS
        self.fmt_combo = self._add_combo(parent, Config.UI_TEXT['export_format'], self.fmt_var, Config.EXPORT_OPTIONS['formats'])
        self.quality_combo = self._add_combo(parent, Config.UI_TEXT['export_quality'], self.quality_var, Config.EXPORT_OPTIONS['qualities'])
        self.dpi_combo = self._add_combo(parent, Config.UI_TEXT['export_dpi'], self.dpi_var, Config.EXPORT_OPTIONS['dpis'])
        self.color_combo = self._add_combo(parent, Config.UI_TEXT['export_color'], self.color_var, Config.EXPORT_OPTIONS['colors'])
        
        # 引入通用的 ModernCheckbutton 小部件，消灭 Canvas 冗余绘制
        self.border_check = ModernCheckbutton(
            parent, 
            Config.UI_TEXT['export_show_border'], 
            self.border_var, 
            self._update_preview,
            bg=Config.LAYOUT['export_ctrl_bg']
        )
        self.border_check.pack(anchor=tk.W, pady=(0, Config.LAYOUT['section_pady']))
        
        self._add_combo(parent, Config.UI_TEXT['export_dir'], self.dir_mode_var, Config.EXPORT_OPTIONS['dir_modes'])
 
        self.browse_btn = ttk.Button(parent, text=Config.UI_TEXT['export_btn_browse'], state=tk.DISABLED, command=self._pick_export_dir)
        self.browse_btn.pack(fill=tk.X, pady=(5, 2))
        
        self.dir_lbl = tk.Label(
            parent, 
            textvariable=self.custom_dir_var, 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            fg=Config.COLORS['dir_lbl_fg'], 
            anchor="w", 
            wraplength=300
        )
        self.dir_lbl.pack(fill=tk.X, pady=(0, 8))
        
        # 3. 新增导出信息估算面板，展示宽度、高度与估算大小
        # 升级为优雅的 Windows 原生 ttk.LabelFrame
        self.info_group = ttk.LabelFrame(
            parent, 
            text=Config.UI_TEXT['export_info_group']
        )
        self.info_group.pack(fill=tk.X, pady=(15, 10))
        
        # 使用内嵌 Frame 确保 100% 兼容的内间距
        info_inner = tk.Frame(self.info_group, bg=Config.LAYOUT['export_ctrl_bg'], padx=12, pady=10)
        info_inner.pack(fill=tk.BOTH, expand=True)
        
        self.width_lbl = tk.Label(
            info_inner, 
            text=Config.UI_TEXT['export_width_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.width_lbl.pack(fill=tk.X, pady=2)
        
        self.height_lbl = tk.Label(
            info_inner, 
            text=Config.UI_TEXT['export_height_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.height_lbl.pack(fill=tk.X, pady=2)
        
        self.size_lbl = tk.Label(
            info_inner, 
            text=Config.UI_TEXT['export_size_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.size_lbl.pack(fill=tk.X, pady=2)

        # 4. 双排动作按钮（取消 vs 开始导出）
        btn_frame = tk.Frame(parent, bg=Config.LAYOUT['export_ctrl_bg'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 取消按钮，采用 Windows 原生圆角微立体 ttk.Button，手感极其细腻
        self.cancel_btn = ttk.Button(
            btn_frame,
            text=Config.UI_TEXT['btn_cancel'],
            command=self.dlg.destroy
        )
        self.cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        # 开始导出按钮，采用 Windows 原生重点高亮样式的 ttk.Button
        self.export_btn = ttk.Button(
            btn_frame,
            text=Config.UI_TEXT['btn_start_export'],
            command=self.export_chart,
            style='Action.TButton'
        )
        self.export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

    def _setup_bindings(self):
        """ 绑定变量变化及窗口尺寸重构事件的实时监听 """
        def on_dir_mode_changed(*_):
            is_custom = (self.dir_mode_var.get() == Config.EXPORT_OPTIONS['dir_modes'][1])
            self.browse_btn.config(state=(tk.NORMAL if is_custom else tk.DISABLED))
        self.dir_mode_var.trace_add("write", on_dir_mode_changed)

        def on_format_changed(*_):
            is_svg = (self.fmt_var.get() == "svg")
            state = "disabled" if is_svg else "readonly"
            self.quality_combo.config(state=state)
            self.dpi_combo.config(state=state)
            
            if is_svg:
                # SVG 模式下仅提供 "彩色" 和 "灰度"，隐藏 "黑白" 选项
                self.color_combo.config(values=Config.EXPORT_OPTIONS['colors'][:2])
                if self.color_var.get() == Config.EXPORT_OPTIONS['colors'][2]:
                    self.color_var.set(Config.EXPORT_OPTIONS['colors'][0])
            else:
                # 其他常规位图模式下还原所有色彩选项
                self.color_combo.config(values=Config.EXPORT_OPTIONS['colors'])
            
            self._update_preview()
            
        self.fmt_var.trace_add("write", on_format_changed)
        on_format_changed()

        # 联动重绘预览
        self.border_var.trace_add("write", lambda *a: self._update_preview())
        self.color_var.trace_add("write", lambda *a: self._update_preview())
        self.quality_var.trace_add("write", lambda *a: self._update_preview())
        self.dpi_var.trace_add("write", lambda *a: self._update_preview())

        # 监听画布大小改变，动态缩放以完美适应窗口
        self.preview_canvas.bind("<Configure>", lambda e: self._update_preview())

    def _update_preview(self):
        """ 在预览画布上毫秒级实时联动重绘包含或不含纸张边框及不同颜色模式的物理原图 """
        self.preview_canvas.delete("all")
        data = self.app.data_var.get().strip()
        divisor = self.app.divisor_var.get().strip()
        if not data or not divisor:
            return
            
        q, rows, dividend = self.app.engine.calculate(data, divisor)
        ctx = self.app._get_render_context()
        ctx['view_scale'] = 1.0  # 导出预览的物理 view_scale 应当始终恒等于 1.0，完全不受主界面缩放干扰
        ctx['show_border'] = self.border_var.get()
        
        img = self.app.renderer.render(data, dividend, divisor, q, rows, ctx)
        if self.color_var.get() == Config.EXPORT_OPTIONS['colors'][1]:
            img = img.convert("L")
        elif self.color_var.get() == Config.EXPORT_OPTIONS['colors'][2]:
            img = img.convert("1")
        
        # 实时联动计算并更新物理尺寸与预估文件大小标签
        self._update_export_info(img, data, dividend, divisor, q, rows, ctx)
        
        # 对预览图片进行智能自适应缩放以完美适应预览区
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if cw > 10 and ch > 10:
            fit_scale = min((cw - 40) / img.width, (ch - 40) / img.height)
            fit_scale = min(1.0, fit_scale)
            if fit_scale < 0.99:
                tw = max(1, int(img.width * fit_scale))
                th = max(1, int(img.height * fit_scale))
                img = img.resize((tw, th), Image.Resampling.LANCZOS)
        
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor="center")
        self.preview_canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
        self._recenter_canvas()

    def _update_export_info(self, img, data, dividend, divisor, q, rows, ctx):
        """ 动态计算并刷新当前导出选项下的物理分辨率与预估文件字节大小 """
        fmt = self.fmt_var.get()
        opt_q = Config.EXPORT_OPTIONS['qualities']
        
        multiplier = {
            opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
            opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
        }.get(self.quality_var.get(), 1)
        
        if fmt == "svg":
            w_real = img.width
            h_real = img.height
            
            # 调用全新的 SVGRenderer 进行内存转换，高内聚低耦合
            svg_ctx = ctx.copy()
            svg_ctx['color_mode'] = self.color_var.get()
            svg_content = SVGRenderer.render_to_svg(self.app.renderer, data, dividend, divisor, q, rows, svg_ctx)
            size_kb = len(svg_content.encode("utf-8")) / 1024.0
            
            self.width_lbl.config(text=f"导出宽度: {w_real} 像素 (矢量)")
            self.height_lbl.config(text=f"导出高度: {h_real} 像素 (矢量)")
            self.size_lbl.config(text=f"预估大小: {size_kb:.2f} KB")
        else:
            w_real = img.width * multiplier
            h_real = img.height * multiplier
            
            # 取消之前挂起的防抖精密测算，防止滑块密集操作时阻塞主线程
            if getattr(self, '_calc_timer', None):
                try:
                    self.dlg.after_cancel(self._calc_timer)
                except Exception:
                    pass
            
            # 1. 第一阶段：极速粗算评估（直接在内存中测试保存 1.0 的预览原图，耗时 < 0.5ms，消灭任何滑块拖拽卡顿）
            color_mode = self.color_var.get()
            if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                img_rough = img.convert("L")
            elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                img_rough = img.convert("1")
            else:
                img_rough = img
                
            save_fmt = "JPEG" if fmt == "jpg" else "PNG"
            bio = io.BytesIO()
            try:
                img_rough.save(bio, format=save_fmt, dpi=(self.dpi_var.get(), self.dpi_var.get()))
                rough_size = (len(bio.getvalue()) / 1024.0) * (multiplier ** 1.15)
            except Exception:
                rough_size = 0.0
                
            self.width_lbl.config(text=f"导出宽度: {w_real} 像素")
            self.height_lbl.config(text=f"导出高度: {h_real} 像素")
            self.size_lbl.config(text=f"预估大小: {rough_size:.1f} KB (计算中...)")
            
            # 2. 第二阶段：防抖 250ms 后，在后台超高清静默重绘并精密测算 100% 绝对物理大小
            def run_precise_calc():
                ctx_calc = ctx.copy()
                ctx_calc['view_scale'] = 1.0 * multiplier
                ctx_calc['show_border'] = self.border_var.get()
                try:
                    img_calc = self.app.renderer.render(data, dividend, divisor, q, rows, ctx_calc)
                    
                    if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                        img_calc = img_calc.convert("L")
                    elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                        img_calc = img_calc.convert("1")
                    else:
                        img_calc = img_calc.convert("RGB")
                        
                    bio_precise = io.BytesIO()
                    img_calc.save(bio_precise, format=save_fmt, dpi=(self.dpi_var.get(), self.dpi_var.get()))
                    precise_size = len(bio_precise.getvalue()) / 1024.0
                    self.size_lbl.config(text=f"预估大小: {precise_size:.1f} KB")
                except Exception:
                    pass
            
            self._calc_timer = self.dlg.after(250, run_precise_calc)

    def _recenter_canvas(self):
        """ 智能重算对齐，保证预览图片完美贴附于画布正中央 """
        self.preview_canvas.update_idletasks()
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        bbox = self.preview_canvas.bbox("all")
        if bbox:
            self.preview_canvas.xview_moveto(((bbox[0] + bbox[2]) / 2 - cw / 2 + 3000) / 6000)
            self.preview_canvas.yview_moveto(((bbox[1] + bbox[3]) / 2 - ch / 2 + 3000) / 6000)

    def _pick_export_dir(self):
        """ 弹出目录选择对话框 """
        d = filedialog.askdirectory(title=Config.UI_TEXT['dialog_pick_dir_title'])
        if d:
            self.custom_dir_var.set(d)

    def export_chart(self):
        """ 执行高保真大图导出的核心逻辑，统一处理 SVG 和高倍率位图输出 """
        try:
            opt_q = Config.EXPORT_OPTIONS['qualities']
            multiplier = {
                opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
                opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
            }[self.quality_var.get()]

            default_dir_mode = Config.EXPORT_OPTIONS['dir_modes'][0]
            if self.dir_mode_var.get() == default_dir_mode:
                export_dir = os.path.join(os.getcwd(), "导出结果")
            else:
                export_dir = self.custom_dir_var.get()

            if not export_dir:
                raise ValueError(Config.MESSAGES['warning_custom_dir_empty'])
            os.makedirs(export_dir, exist_ok=True)
            
            fmt = self.fmt_var.get()
            out_path = os.path.join(export_dir, f"crc_export.{fmt}")

            if fmt == "svg":
                self._save_svg(out_path)
            else:
                self._save_bitmap(out_path, multiplier)

            SuccessDialog(self.dlg, out_path, export_dir)
        except Exception as e:
            self._show_error_dialog(e)


    def _save_svg(self, out_path):
        """ 保存为 SVG 矢量格式 """
        data = self.app.data_var.get().strip()
        divisor = self.app.divisor_var.get().strip()
        q, rows, dividend = self.app.engine.calculate(data, divisor)
        
        ctx = self.app._get_render_context()
        ctx['view_scale'] = 1.0  # 矢量 SVG 导出使用基准 1.0 物理比例即可，无需超采样
        ctx['show_border'] = self.border_var.get()
        ctx['color_mode'] = self.color_var.get()
        
        # 引入外部专一的 SVGRenderer 进行高保真矢量渲染
        svg_content = SVGRenderer.render_to_svg(self.app.renderer, data, dividend, divisor, q, rows, ctx)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

    def _save_bitmap(self, out_path, multiplier):
        """ 在内存中以指定 high-DPI 物理重绘并写入位图文件 """
        data = self.app.data_var.get().strip()
        divisor = self.app.divisor_var.get().strip()
        q, rows, dividend = self.app.engine.calculate(data, divisor)
        
        ctx = self.app._get_render_context()
        ctx['view_scale'] = 1.0 * multiplier
        ctx['show_border'] = self.border_var.get()
        
        img = self.app.renderer.render(data, dividend, divisor, q, rows, ctx)
        color_mode = self.color_var.get()
        if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
            img = img.convert("L")
        elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
            img = img.convert("1")
        else:
            img = img.convert("RGB")
            
        save_fmt = "JPEG" if out_path.endswith(".jpg") else "PNG"
        img.save(out_path, format=save_fmt, dpi=(self.dpi_var.get(), self.dpi_var.get()))

    def _show_error_dialog(self, e):
        """ 展示导出失败信息对话框 """
        messagebox.showerror(
            Config.MESSAGES['export_fail_title'],
            Config.MESSAGES['export_fail_body'].format(
                error_type=type(e).__name__,
                error_msg=str(e)
            )
        )

    def _add_combo(self, parent, label, var, values):
        """ 通用组合框下拉组件封装 """
        tk.Label(
            parent, 
            text=label, 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal']
        ).pack(anchor=tk.W, pady=(6, 2))
        
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        combo.pack(fill=tk.X)
        return combo


class SuccessDialog:
    """
    导出成功自定义精致提示框。
    
    100% 采用 Windows 原生 ttk 控件重绘。
    包含翡翠绿实心圆形白色勾号成功徽章、大字大描述排版、圆角只读路径框，以及等高的右对齐动作按钮。
    """
    def __init__(self, parent, out_path, export_dir):
        self.dlg = tk.Toplevel(parent)
        self.dlg.title("导出成功")
        self.dlg.transient(parent)
        self.dlg.grab_set()
        
        # 统一系统背景底色
        self.dlg.configure(bg=Config.COLORS['main_bg'])
        
        # 从配置文件读取大尺寸高雅物理参数
        w = Config.LAYOUT['success_dialog_w']
        h = Config.LAYOUT['success_dialog_h']
        pad = Config.LAYOUT['success_dialog_pad']
        icon_sz = Config.LAYOUT['success_icon_size']
        
        # 智能居中物理坐标计算
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        self.dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.dlg.resizable(False, False)
        
        # 主体布局容器，提供充足的内边距，实现极佳的空灵呼吸留白感
        main_frame = tk.Frame(self.dlg, bg=Config.COLORS['main_bg'], padx=pad, pady=pad)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 优先布局底部按钮栏，确保物理高度绝不被压缩
        btn_frame = tk.Frame(main_frame, bg=Config.COLORS['main_bg'])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 2. 其次布局顶部内容栏（徽章 + 描述）
        top_bar = tk.Frame(main_frame, bg=Config.COLORS['main_bg'])
        top_bar.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # 绘制高端的手绘现代翡翠绿打勾徽章 Canvas (Success Badge)
        try:
            icon_cv = tk.Canvas(top_bar, width=icon_sz, height=icon_sz, bg=Config.COLORS['main_bg'], highlightthickness=0)
            icon_cv.pack(side=tk.LEFT, anchor="n", padx=(0, 16))
            
            # 画一个翡翠绿实心圆形 (#10b981)
            icon_cv.create_oval(2, 2, icon_sz - 2, icon_sz - 2, fill="#10b981", outline="")
            
            # 画白色粗线条打勾，勾角采用圆润端点
            icon_cv.create_line(icon_sz * 0.28, icon_sz * 0.5, icon_sz * 0.45, icon_sz * 0.68, fill="white", width=3, capstyle=tk.ROUND)
            icon_cv.create_line(icon_sz * 0.45, icon_sz * 0.68, icon_sz * 0.72, icon_sz * 0.32, fill="white", width=3, capstyle=tk.ROUND)
        except Exception:
            pass
            
        # 大气的大字标题与二级描述排版区
        txt_frame = tk.Frame(top_bar, bg=Config.COLORS['main_bg'])
        txt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title_lbl = ttk.Label(txt_frame, text="导出成功！", font=Config.FONTS['side_title'], background=Config.COLORS['main_bg'])
        title_lbl.pack(anchor="w", pady=(0, 4))
        
        desc_lbl = ttk.Label(txt_frame, text="您的文件已保存至本地：", font=Config.FONTS['zh_normal'], background=Config.COLORS['main_bg'], foreground="#64748b")
        desc_lbl.pack(anchor="w")
        
        # 3. 部署高品位的“只读路径展示卡”，支持横向滚动与 Ctrl+C 复制，排版极其整洁！
        path_entry = ttk.Entry(main_frame, font=Config.FONTS['combo'], justify="left")
        path_entry.pack(fill=tk.X, pady=(12, 18))
        
        path_entry.insert(0, out_path)
        path_entry.config(state="readonly")  # 只读框，完美规整，用户双击即可选定完整路径
        
        # “好的”标准系统确认按钮
        ttk.Button(
            btn_frame,
            text=" 好的 ",
            command=self.dlg.destroy
        ).pack(side=tk.RIGHT, padx=(12, 0))
        
        # “打开当前导出目录”标准系统按钮
        def open_dir():
            self.dlg.destroy()
            import subprocess
            try:
                norm_path = os.path.normpath(out_path)
                subprocess.run(f'explorer /select,"{norm_path}"', shell=True)
            except Exception:
                try:
                    os.startfile(export_dir)
                except Exception:
                    pass
                    
        ttk.Button(
            btn_frame,
            text="打开当前导出目录",
            command=open_dir,
            style='Action.TButton'  # 使用高亮样式方便用户引导
        ).pack(side=tk.RIGHT)
