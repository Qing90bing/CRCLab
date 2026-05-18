import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from config.constants import Config

class ExportDialog:
    """
    导出图表弹出对话框类。
    
    采用高内聚设计，将原本混杂在 main.py 中的导出 UI 构建、
    实时高保真预览重绘、以及多倍率物理图像输出逻辑完全抽离，实现 SRP 单一职责原则。
    所有 UI 样式、默认业务状态和选项完全取自 Config 配置中心，实现单一事实来源。
    """
    def __init__(self, app):
        """
        初始化并打开导出对话框。
        :param app: 主应用程序实例，用于共享数据 and 渲染器。
        """
        self.app = app
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
        
        self.preview_canvas = tk.Canvas(parent, bg=Config.COLORS['preview_canvas_bg'], highlightthickness=1, highlightbackground=Config.COLORS['preview_canvas_border'])
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
        
        self._add_custom_check(parent, Config.UI_TEXT['export_show_border'], self.border_var, self._update_preview)
        self._add_combo(parent, Config.UI_TEXT['export_dir'], self.dir_mode_var, Config.EXPORT_OPTIONS['dir_modes'])
 
        self.browse_btn = tk.Button(parent, text=Config.UI_TEXT['export_btn_browse'], state=tk.DISABLED, command=self._pick_export_dir)
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
        self.info_group = tk.LabelFrame(
            parent, 
            text=Config.UI_TEXT['export_info_group'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_bold'],
            padx=12,
            pady=10
        )
        self.info_group.pack(fill=tk.X, pady=(15, 10))
        
        self.width_lbl = tk.Label(
            self.info_group, 
            text=Config.UI_TEXT['export_width_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.width_lbl.pack(fill=tk.X, pady=2)
        
        self.height_lbl = tk.Label(
            self.info_group, 
            text=Config.UI_TEXT['export_height_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.height_lbl.pack(fill=tk.X, pady=2)
        
        self.size_lbl = tk.Label(
            self.info_group, 
            text=Config.UI_TEXT['export_size_placeholder'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.size_lbl.pack(fill=tk.X, pady=2)

        # 4. 双排动作按钮（取消 vs 开始导出）
        btn_frame = tk.Frame(parent, bg=Config.LAYOUT['export_ctrl_bg'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 取消按钮，采用扁平化高雅红配色
        self.cancel_btn = tk.Button(
            btn_frame,
            text=Config.UI_TEXT['btn_cancel'],
            bg=Config.COLORS['cancel_bg'],
            fg="white",
            relief=tk.FLAT,
            font=Config.FONTS['zh_bold'],
            command=self.dlg.destroy
        )
        self.cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), ipady=4)
        
        # 开始导出按钮，采用扁平化翡翠绿配色
        self.export_btn = tk.Button(
            btn_frame,
            text=Config.UI_TEXT['btn_start_export'],
            bg=Config.COLORS['export_btn_bg'],
            fg="white",
            relief=tk.FLAT,
            font=Config.FONTS['zh_bold'],
            command=self.export_chart
        )
        self.export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0), ipady=4)

    def _setup_bindings(self):
        """ 绑定变量变化及窗口尺寸重构事件的实时监听 """
        def on_dir_mode_changed(*_):
            # 比对值采用统一配置元数据，避免硬编码 "自定义目录"
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
        
        # 获取品质相乘倍率数
        multiplier = {
            opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
            opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
        }.get(self.quality_var.get(), 1)
        
        if fmt == "svg":
            # SVG 是矢量图
            w_real = img.width
            h_real = img.height
            
            # 实时在内存中运行渲染生成临时 SVG 代码，以精确估算其字节文件大小
            svg_ctx = ctx.copy()
            svg_ctx['color_mode'] = self.color_var.get()
            svg_content = self.app.renderer.render_to_svg(data, dividend, divisor, q, rows, svg_ctx)
            size_kb = len(svg_content.encode("utf-8")) / 1024.0
            
            self.width_lbl.config(text=f"导出宽度: {w_real} 像素 (矢量)")
            self.height_lbl.config(text=f"导出高度: {h_real} 像素 (矢量)")
            self.size_lbl.config(text=f"预估大小: {size_kb:.2f} KB")
        else:
            # 常规位图模式（PNG/JPG）
            w_real = img.width * multiplier
            h_real = img.height * multiplier
            
            # 物理面积（像素数）
            pixels = w_real * h_real
            
            if fmt == "png":
                # PNG 压缩比，因为 CRC 表格是大面积白色无损，压缩率奇高，平均按 0.015 字节/像素估算
                size_kb = (pixels * 0.015) / 1024.0
            else:
                # JPG 有损中度压缩，平均按 0.035 字节/像素估算
                size_kb = (pixels * 0.035) / 1024.0
                
            # 灰度模式和黑白模式会极大地减少存储通道与位深，从而减小物理文件大小
            color_mode = self.color_var.get()
            if color_mode == Config.EXPORT_OPTIONS['colors'][1]:
                size_kb *= 0.55
            elif color_mode == Config.EXPORT_OPTIONS['colors'][2]:
                size_kb *= 0.22
                
            self.width_lbl.config(text=f"导出宽度: {w_real} 像素")
            self.height_lbl.config(text=f"导出高度: {h_real} 像素")
            self.size_lbl.config(text=f"预估大小: {max(1.0, size_kb):.1f} KB")

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
            # 动态检索品质选项元数据，彻底清空硬编码文字比对
            opt_q = Config.EXPORT_OPTIONS['qualities']
            multiplier = {
                opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
                opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
            }[self.quality_var.get()]

            # 目录判定亦改用统一配置项
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

            messagebox.showinfo(Config.MESSAGES['export_success_title'], f"{Config.MESSAGES['export_success_body']}{out_path}")
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
        
        svg_content = self.app.renderer.render_to_svg(data, dividend, divisor, q, rows, ctx)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

    def _save_bitmap(self, out_path, multiplier):
        """ 在内存中以指定高分辨率物理超采样重绘并写入位图文件 """
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

    def _add_custom_check(self, parent, text, var, command):
        """ 绘制现代化大尺寸的自定义高亮勾选框 """
        f = tk.Frame(parent, bg=Config.LAYOUT['export_ctrl_bg'])
        f.pack(anchor=tk.W, pady=(0, Config.LAYOUT['section_pady']))
        sz = Config.LAYOUT['check_size']
        canvas = tk.Canvas(f, width=sz+4, height=sz+4, bg=Config.LAYOUT['export_ctrl_bg'], highlightthickness=0, cursor="hand2")
        canvas.pack(side=tk.LEFT)
        lbl = tk.Label(f, text=text, bg=Config.LAYOUT['export_ctrl_bg'], font=Config.FONTS['zh_normal'], cursor="hand2")
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
            if command:
                command()
                
        canvas.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        refresh()
