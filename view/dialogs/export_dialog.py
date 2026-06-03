import os
import io
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from config.constants import Config
from view.dialogs.success_dialog import SuccessDialog
from services.exporter_service import Exporter
from view.dialogs.export_preview import ExportPreview
from view.dialogs.export_form import ExportForm

_BW_THRESHOLD_TABLE = [0 if pixel < 128 else 255 for pixel in range(256)]

class ExportDialog:
    """
    导出图表配置与预览弹出对话框。
    
    高级协调类 (Coordinator)。统一协调左侧预览 (`ExportPreview`) 和右侧表单选项 (`ExportForm`)。
    通过事件绑定、状态跟踪、防抖计算及物理导出完成完整的导出生命周期管理。
    """
    def __init__(self, app):
        """
        初始化导出对话框。
        :param app: 主应用程序 CRCLabApp 实例。
        """
        self.app = app
        self._calc_timer = None
        self._last_scale_params = (None, None, None)
        self.dlg = tk.Toplevel(app.root)
        self.dlg.withdraw()
        self.dlg.configure(bg=Config.COLORS['main_bg'])
        self.dlg.title(Config.UI_TEXT['export_title'])
        self.dlg.transient(app.root)
        
        # 禁用父窗口以实现模态，并避免 grab_set() 导致任务栏最小化失效问题
        try:
            app.root.attributes("-disabled", True)
        except Exception:
            pass
            
        def restore_parent(event):
            if event.widget == self.dlg:
                try:
                    app.root.attributes("-disabled", False)
                except Exception:
                    pass
        self.dlg.bind("<Destroy>", restore_parent)
        
        # 1. 窗口几何位置自适应
        self._setup_geometry()
        
        # 2. 构建左右双栏并挂载精细组件
        self._build_layout()
        
        # 3. 联动状态追踪与事件绑定
        self._setup_bindings()
        
        # 4. 首次同步与延迟定位居中
        self._update_preview()
        
        # 5. 计算并应用安全的最小窗口高度（必须在 UI 完全构建后）
        self._enforce_safe_minsize()
        
        self.dlg.deiconify()
        self.dlg.after(100, self._update_preview)

    def _enforce_safe_minsize(self):
        """ 
        强制根据右侧参数面板内各组件的真实物理排版高度总和，更新窗口的最小高度。
        防止操作系统 DPI 缩放或用户极端缩小窗口导致的组件互相挤压遮挡。
        """
        self.dlg.update_idletasks()
        
        # 由于 form_panel 使用了 pack_propagate(False)，其自身的 winfo_reqheight() 会失真。
        # 因此我们必须遍历其直系子容器（top_content 和 bottom_actions）来算出真实的绝对需求高度。
        content_h = sum(child.winfo_reqheight() for child in self.form_panel.winfo_children())
        
        # 加上 form_panel 本身在 pack 时设置的外边距 (pady=16 上下各 16)
        real_req_h = content_h + 32
        
        # 保底依然使用 Config 中的默认最小值
        safe_min_h = max(Config.LAYOUT['export_min_h'], real_req_h)
        self.dlg.minsize(Config.LAYOUT['export_min_w'], safe_min_h)

    def _setup_geometry(self):
        """ 根据物理屏幕分辨率及实际工作区（排除任务栏）自适应居中显示 """
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()
        
        # 获取实际工作区大小（排除任务栏）
        work_x, work_y, work_w, work_h = 0, 0, sw, sh
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            # SPI_GETWORKAREA = 0x30
            ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)
            work_x = rect.left
            work_y = rect.top
            work_w = rect.right - rect.left
            work_h = rect.bottom - rect.top
        except Exception:
            pass

        # 严格按照设定的屏幕比例显示，以实际工作区为基准计算
        w = int(work_w * Config.LAYOUT['export_dialog_w_ratio'])
        h = int(work_h * Config.LAYOUT['export_dialog_h_ratio'])
        
        # 确保不小于最小限制
        w = max(Config.LAYOUT['export_min_w'], w)
        h = max(Config.LAYOUT['export_min_h'], h)
        
        # 确保不超出工作区可见区域
        w = min(work_w, w)
        h = min(work_h, h)
        
        # 在实际工作区内居中
        pos_x = work_x + (work_w - w) // 2
        pos_y = work_y + (work_h - h) // 2
        
        self.dlg.geometry(f"{w}x{h}+{pos_x}+{pos_y}")
        self.dlg.minsize(Config.LAYOUT['export_min_w'], Config.LAYOUT['export_min_h'])

    def _build_layout(self):
        """ 构建导出界面的左右双栏框架 """
        # 挂载右侧配置参数表单组件 (先 pack 右侧，确保在窗口缩小的时候不会被左侧抢占空间而导致挤压变形)
        self.form_panel = ExportForm(self.dlg, self)
        self.form_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 16), pady=16)

        # 挂载左侧自适应预览画布组件
        self.preview_panel = ExportPreview(self.dlg, self.app)
        self.preview_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 8), pady=16)

    def _setup_bindings(self):
        """ 联动绑定下拉菜单、复选框变量 trace 并配置画布 Configure 自动响应 """
        form = self.form_panel
        
        # 1. 物理导出路径与目录类型切换联动
        def on_dir_mode_changed(*_):
            is_custom = (form.dir_mode_var.get() == Config.EXPORT_OPTIONS['dir_modes'][1])
            form.browse_btn.config(state=(tk.NORMAL if is_custom else tk.DISABLED))
        form.dir_mode_var.trace_add("write", on_dir_mode_changed)

        def update_dir_display(*_):
            dir_mode = form.dir_mode_var.get()
            is_custom = (dir_mode == Config.EXPORT_OPTIONS['dir_modes'][1])
            
            if not is_custom:
                # 默认当前目录模式：计算绝对化物理路径，设置禁用视觉样式
                export_dir = os.path.join(os.getcwd(), "导出结果")
                form.display_dir_var.set(os.path.abspath(export_dir))
            else:
                # 自定义位置模式：同步 custom_dir_var，高亮显示可编辑模式
                if form.display_dir_var.get() != form.custom_dir_var.get():
                    form.display_dir_var.set(form.custom_dir_var.get())
            
            form.dir_entry.set_mode(is_custom)
                
        def on_display_dir_changed(*_):
            # 仅在自定义模式下，路径文本框手动输入的改变才同步写回 custom_dir_var
            dir_mode = form.dir_mode_var.get()
            if dir_mode == Config.EXPORT_OPTIONS['dir_modes'][1]:
                if form.custom_dir_var.get() != form.display_dir_var.get():
                    form.custom_dir_var.set(form.display_dir_var.get())

        form.dir_mode_var.trace_add("write", update_dir_display)
        form.custom_dir_var.trace_add("write", update_dir_display)
        form.display_dir_var.trace_add("write", on_display_dir_changed)
        update_dir_display()  # 首次初始化路径显示

        # 2. 导出文件物理格式切换联动（如果是矢量格式，则置灰倍数与分辨率）
        def on_format_changed(*_):
            fmt = form.fmt_var.get()
            is_vector = (fmt in ("svg", "pdf", "emf"))
            state = "disabled" if is_vector else "readonly"
            form.quality_combo.set_state(state)
            form.dpi_combo.set_state(state)
            form.set_jpg_quality_state(tk.NORMAL if fmt == "jpg" else tk.DISABLED)
            
            # 所有物理格式均支持彩色、灰度、黑白等颜色模式
            form.color_combo.combo.config(values=Config.EXPORT_OPTIONS['colors'])
            self._update_preview()
            
        form.fmt_var.trace_add("write", on_format_changed)
        on_format_changed()

        # 3. 勾选及各下拉变动后实时触发重绘与估算
        form.border_var.trace_add("write", lambda *a: self._update_preview())
        form.color_var.trace_add("write", lambda *a: self._update_preview())
        form.quality_var.trace_add("write", lambda *a: self._update_preview())
        form.dpi_var.trace_add("write", lambda *a: self._update_preview())
        
        # 窗口大小改动后自动对齐画布居中（防抖处理避免卡顿）
        self.preview_panel.preview_canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        """ 画布大小改变时的实时居中与防抖重绘 """
        # 1. 立即在视觉上居中现有内容，避免拖拽边框时白边闪烁
        self.preview_panel.recenter_canvas()
        
        # 2. 防抖触发仅针对画布缩放的重绘，不再触发耗时的后台大小预估计算
        if getattr(self, '_resize_timer', None) is not None:
            self.dlg.after_cancel(self._resize_timer)
        self._resize_timer = self.dlg.after(200, self._refresh_preview_scale)

    def _refresh_preview_scale(self):
        """ 仅根据画布新尺寸重新缩放已有图像，彻底跳过 CRC 计算和文件物理大小预估 """
        if hasattr(self, '_last_rendered_img') and self._last_rendered_img:
            self.preview_panel.render_preview(self._last_rendered_img)

    def _update_preview(self):
        """
        实时预览核心重绘驱动方法。
        根据当前的配置参数，在内存中渲染图解并等比缩放贴至预览画布中。
        """
        form = self.form_panel
        self.preview_panel.clear()
        
        data = self.app.data_var.get().strip()
        divisor = self.app.divisor_var.get().strip()
        if not data or not divisor:
            return
            
        # 1. 运行 CRC 引擎重新计算步骤
        q, rows, dividend = self.app.engine.calculate(data, divisor)
        
        # 2. 获取当前的上下文环境，固定预览 view_scale 为 1.0 并覆盖参数
        ctx = self.app._get_render_context()
        ctx['view_scale'] = 1.0
        ctx['show_border'] = form.border_var.get()
        ctx['is_preview'] = True
        
        # 3. 物理重绘生成基础 Pillow RGBA 图像
        img = self.app.renderer.render(data, dividend, divisor, q, rows, ctx)
        
        # 4. 根据当前选定的颜色模式执行像素灰度/黑白转换，同时无损维持透明通道
        color_opt = Config.EXPORT_OPTIONS['colors']
        if form.color_var.get() == color_opt[1]:
            # 灰度转换
            if img.mode in ("RGBA", "LA"):
                r, g, b, a = img.split()
                rgb_gray = Image.merge("RGB", (r, g, b)).convert("L")
                img = Image.merge("RGBA", (rgb_gray, rgb_gray, rgb_gray, a))
            else:
                img = img.convert("L")
        elif form.color_var.get() == color_opt[2]:
            # 二值黑白转换（采用纯阈值过滤，避免 Floyd-Steinberg 抖动产生的杂点）
            if img.mode in ("RGBA", "LA"):
                r, g, b, a = img.split()
                rgb_gray = Image.merge("RGB", (r, g, b)).convert("L")
                rgb_bw = rgb_gray.point(_BW_THRESHOLD_TABLE, 'L')
                img = Image.merge("RGBA", (rgb_bw, rgb_bw, rgb_bw, a))
            else:
                img = img.convert("L").point(_BW_THRESHOLD_TABLE, 'L').convert("1")
        
        # 保存最后的原始高分辨率渲染图以便后续纯拖拽窗口时进行零成本快速重缩放
        self._last_rendered_img = img
        
        # 5. 更新导出宽度、高度及文件大小的指示文本
        self._update_export_info(img, data, dividend, divisor, q, rows, ctx)
        
        # 6. 将生成的图像渲染到画布上
        self.preview_panel.render_preview(img)

    def _update_export_info(self, img, data, dividend, divisor, q, rows, ctx):
        """ 联动更新右侧表单中的长宽估算指标，并防抖触发大小精密测算 """
        form = self.form_panel
        fmt = form.fmt_var.get()
        opt_q = Config.EXPORT_OPTIONS['qualities']
        
        multiplier = {
            opt_q[0]: 1, opt_q[1]: 2,
            opt_q[2]: 3, opt_q[3]: 4
        }.get(form.quality_var.get(), 1)
        
        dpi_val = form.dpi_var.get()
        dpi_scale = dpi_val / 96.0
        
        # 检查是否真的改变了影响像素物理大小的缩放比例或格式参数，以避免改变边框/色彩时刷新粗估导致数字跳变
        current_params = (multiplier, dpi_val, fmt)
        scale_changed = (current_params != getattr(self, '_last_scale_params', (None, None, None)))
        self._last_scale_params = current_params
        
        if scale_changed:
            if fmt in ("svg", "pdf", "emf"):
                form.width_lbl.config(text="导出宽度:（矢量）")
                form.height_lbl.config(text="导出高度:（矢量）")
            else:
                w_real = int(img.width * multiplier * dpi_scale)
                h_real = int(img.height * multiplier * dpi_scale)
                form.width_lbl.config(text=f"导出宽度: {w_real} 像素")
                form.height_lbl.config(text=f"导出高度: {h_real} 像素")
            
        # 精密估算大小（应用防抖）
        self._debounce_size_calc(data, dividend, divisor, q, rows, ctx, multiplier, fmt)

    def _debounce_size_calc(self, data, dividend, divisor, q, rows, ctx, multiplier, fmt):
        """ 采用统一防抖机制（250毫秒）联动异步线程模拟物理写入，测算百分之百精确的文件大小 """
        if getattr(self, '_is_exporting', False):
            return
            
        form = self.form_panel
        calc_timer = self._calc_timer
        if calc_timer is not None:
            try:
                self.dlg.after_cancel(calc_timer)
            except Exception:
                pass
            self._calc_timer = None
                
        form.size_lbl.config(text="预估大小: 计算中...")
        
        # 生成递增自增的计算版本标识符，防止前一次慢计算返回后脏写覆盖新版界面显示
        if not hasattr(self, '_current_calc_id'):
            self._current_calc_id = 0
        self._current_calc_id = (self._current_calc_id + 1) % 10000
        calc_id = self._current_calc_id
        
        def run_precise_calc_thread():
            self._calc_timer = None
            import threading
            
            def worker():
                try:
                    if fmt in ("svg", "pdf", "emf"):
                        size_bytes, w, h = Exporter.estimate_vector_size(
                            self.app, fmt, data, dividend, divisor, q, rows, ctx,
                            form.color_var.get(), form.border_var.get()
                        )
                    else:
                        save_fmt = "JPEG" if fmt == "jpg" else "PNG"
                        size_bytes, w, h = Exporter.calculate_precise_bitmap_size(
                            self.app, data, dividend, divisor, q, rows, ctx,
                            form.color_var.get(), form.border_var.get(), multiplier, save_fmt, form.dpi_var.get(),
                            int(round(float(form.jpg_quality_var.get())))
                        )
                    
                    if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                        size_kb = size_bytes / 1024.0
                        size_text = f"{size_bytes:,} 字节 ({size_kb:.1f} KB)"
                    else:
                        size_text = "估算失败"
                    
                    # 线程安全回调
                    def update_ui():
                        if getattr(self, '_is_exporting', False):
                            return
                        if getattr(self, '_current_calc_id', None) == calc_id:
                            form.size_lbl.config(text=f"预估大小: {size_text}")
                            if fmt in ("svg", "pdf", "emf"):
                                form.width_lbl.config(text="导出宽度:（矢量）")
                                form.height_lbl.config(text="导出高度:（矢量）")
                            else:
                                form.width_lbl.config(text=f"导出宽度: {w} 像素")
                                form.height_lbl.config(text=f"导出高度: {h} 像素")
                            
                    self.dlg.after(0, update_ui)
                except Exception as ex:
                    # 如果估算因为像素过大等物理原因抛出异常，必须及时阻断“计算中...”的状态挂起
                    def fail_ui():
                        if getattr(self, '_is_exporting', False):
                            return
                        if getattr(self, '_current_calc_id', None) == calc_id:
                            form.size_lbl.config(text=f"预估大小: 估算失败")
                            form.width_lbl.config(text="导出宽度: 估算失败")
                            form.height_lbl.config(text="导出高度: 估算失败")
                    self.dlg.after(0, fail_ui)
            
            # 以守护线程启动计算任务
            t = threading.Thread(target=worker, daemon=True)
            t.start()
                
        self._calc_timer = self.dlg.after(250, run_precise_calc_thread)

    def _on_export_success(self, out_path, export_dir, width, height):
        """ 导出成功的主线程回调，唤起打勾徽章模态提示窗 """
        self._is_exporting = False
        form = self.form_panel
        form.progress.stop()
        form.progress.config(mode='determinate', value=0)
        form.set_widgets_state(tk.NORMAL)
        
        # 收集详细的导出数据以用于显示在成功窗口中
        fmt = form.fmt_var.get()
        dpi = str(form.dpi_var.get())
        color = form.color_var.get()
        quality = form.quality_var.get()
        border = "是" if form.border_var.get() else "否"
        
        # 获取透明背景状态
        ctx = self.app._get_render_context()
        sheet_bg = ctx.get('sheet_bg_color', '#ffffff')
        is_transparent = sheet_bg in ("transparent", "none")
        if fmt.lower() in ("png", "svg") and is_transparent:
            transparent_bg = "是"
        else:
            transparent_bg = "否"
            
        # 计算文件真实大小
        try:
            size_bytes = os.path.getsize(out_path)
            if size_bytes > 0:
                size_kb = size_bytes / 1024.0
                size_text = f"{size_bytes:,} 字节（{size_kb:.1f} KB）"
            else:
                size_text = "未知"
        except Exception:
            size_text = "未知"
            
        # 组装明细数据
        is_vector = fmt.lower() in ("svg", "pdf", "emf")
        details = {
            "文件名": os.path.basename(out_path),
            "格式": fmt.upper(),
            "DPI": dpi,
            "颜色": color,
        }
        
        if is_vector:
            details["宽度"] = "（矢量）"
            details["高度"] = "（矢量）"
        else:
            details["像素倍率"] = quality
            if fmt.lower() in ("jpg", "jpeg"):
                details["JPG 质量"] = str(int(round(float(form.jpg_quality_var.get())))) + "%"
            details["宽度"] = f"{width} 像素" if width > 0 else "未知"
            details["高度"] = f"{height} 像素" if height > 0 else "未知"
            
        details["纸张边框"] = border
        details["透明背景"] = transparent_bg
        details["文件大小"] = size_text
        
        SuccessDialog(self.dlg, out_path, export_dir, details)

    def _on_export_failure(self, e):
        """ 导出失败的主线程回调 """
        self._is_exporting = False
        form = self.form_panel
        form.progress.stop()
        form.progress.config(mode='determinate', value=0)
        form.set_widgets_state(tk.NORMAL)
        self._show_error_dialog(e)

    def export_chart(self):
        """ 核心物理导出操作：拉起守护后台线程，避免写盘假死，实现极其顺滑的无阻塞用户体验 """
        import threading
        form = self.form_panel
        
        # 1. 前置校验：校验文件名是否合法，以及自定义目录是否有效
        filename = form.filename_var.get().strip()
        invalid_chars = set('\\/:*?"<>|')
        if not filename or any(char in invalid_chars for char in filename):
            messagebox.showwarning(
                Config.MESSAGES['warning_title_invalid'], 
                Config.MESSAGES['warning_invalid_filename']
            )
            return

        dir_mode = form.dir_mode_var.get()
        custom_dir = form.custom_dir_var.get().strip()
        
        if dir_mode == Config.EXPORT_OPTIONS['dir_modes'][1]:  # 自定义位置
            if not custom_dir:
                messagebox.showwarning(
                    Config.MESSAGES['warning_title_invalid'], 
                    Config.MESSAGES['warning_custom_dir_empty']
                )
                return
            if not os.path.exists(custom_dir):
                messagebox.showerror(
                    "路径不存在",
                    f"您指定的自定义导出目录不存在：\n\n{custom_dir}\n\n请先在系统中手动创建该目录，或在输入框中填入正确的路径。"
                )
                return
            if not os.path.isdir(custom_dir):
                messagebox.showerror(
                    "路径无效",
                    f"您指定的路径不是一个有效的目录：\n\n{custom_dir}\n\n请重新输入或点击“浏览目录”按钮选择。"
                )
                return

        # 2. 锁定配置表单，阻断高频重复点击，展示浮动滑动进度条
        self._is_exporting = True
        
        # 仅在后台估算还未完成（处于“计算中...”或者有挂起的 timer）时，才覆写提示文案，保留已算出的有用信息
        was_calculating = "计算中" in form.size_lbl.cget("text")
        if getattr(self, '_calc_timer', None) is not None:
            try:
                self.dlg.after_cancel(self._calc_timer)
            except Exception:
                pass
            self._calc_timer = None
            was_calculating = True
            
        if was_calculating:
            form.size_lbl.config(text="预估大小: 正在导出，忽略本次估算结果")
            form.width_lbl.config(text="导出宽度: 正在导出，忽略本次估算结果")
            form.height_lbl.config(text="导出高度: 正在导出，忽略本次估算结果")
        
        form.set_widgets_state(tk.DISABLED)
        form.progress.config(mode='indeterminate')
        form.progress.start(10)
        
        # 3. 收集表单状态参数以供渲染计算使用
        fmt = form.fmt_var.get()
        show_border = form.border_var.get()
        color_mode = form.color_var.get()
        quality = form.quality_var.get()
        jpg_quality = int(round(float(form.jpg_quality_var.get())))
        dpi = form.dpi_var.get()
        
        # 4. 后台物理写入
        def async_worker():
            try:
                out_path, export_dir, width, height = Exporter.export(
                    self.app,
                    filename,
                    fmt,
                    show_border,
                    color_mode,
                    quality,
                    jpg_quality,
                    dpi,
                    dir_mode,
                    custom_dir
                )
                # 成功回调
                self.dlg.after(0, lambda: self._on_export_success(out_path, export_dir, width, height))
            except Exception as e:
                # 失败回调（关键修复：通过 err=e 建立局部默认参数，防止在异步执行时原始的局部变量 e 已被作用域销毁而引发 NameError）
                self.dlg.after(0, lambda err=e: self._on_export_failure(err))
                
        threading.Thread(target=async_worker, daemon=True).start()

    def _show_error_dialog(self, e):
        """ 格式化错误反馈 """
        messagebox.showerror(
            Config.MESSAGES['export_fail_title'],
            Config.MESSAGES['export_fail_body'].format(
                error_type=type(e).__name__,
                error_msg=str(e)
            )
        )
