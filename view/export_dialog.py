import os
import io
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from config.constants import Config
from view.success_dialog import SuccessDialog
from view.exporter import Exporter
from view.export_preview import ExportPreview
from view.export_form import ExportForm

class ExportDialog:
    """
    导出图表配置与预览弹出对话框。
    
    高级协调类 (Coordinator)。统一协调左侧预览 (`ExportPreview`) 和右侧表单选项 (`ExportForm`)。
    通过事件绑定、状态跟踪、防抖计算及物理导出完成完整的导出生命周期管理。
    """
    def __init__(self, app):
        """
        初始化导出对话框。
        :param app: 主应用程序 CRCVisualizerApp 实例。
        """
        self.app = app
        self._calc_timer = None
        self.dlg = tk.Toplevel(app.root)
        self.dlg.title(Config.UI_TEXT['export_title'])
        self.dlg.transient(app.root)
        self.dlg.grab_set()  # 设置模态对话框，防范多窗体并发
        
        # 1. 窗口几何位置自适应
        self._setup_geometry()
        
        # 2. 构建左右双栏并挂载精细组件
        self._build_layout()
        
        # 3. 联动状态追踪与事件绑定
        self._setup_bindings()
        
        # 4. 首次同步与延迟定位居中
        self._update_preview()
        self.dlg.after(100, self._update_preview)

    def _setup_geometry(self):
        """ 根据物理屏幕分辨率自适应居中显示 """
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()
        w = min(Config.LAYOUT['export_max_w'], int(sw * Config.LAYOUT['export_dialog_w_ratio']))
        h = min(Config.LAYOUT['export_max_h'], int(sh * Config.LAYOUT['export_dialog_h_ratio']))
        self.dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.dlg.minsize(Config.LAYOUT['export_min_w'], Config.LAYOUT['export_min_h'])

    def _build_layout(self):
        """ 构建导出界面的左右双栏框架 """
        # 挂载左侧自适应预览画布组件
        self.preview_panel = ExportPreview(self.dlg, self.app)
        self.preview_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 挂载右侧配置参数表单组件
        self.form_panel = ExportForm(self.dlg, self)
        self.form_panel.pack(side=tk.RIGHT, fill=tk.Y)

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
                
                form.dir_block.config(bg="#f1f5f9", highlightbackground="#e2e8f0")
                form.dir_entry.config(
                    state="disabled",
                    disabledbackground="#f1f5f9",
                    disabledforeground="#94a3b8"
                )
            else:
                # 自定义位置模式：同步 custom_dir_var，高亮显示可编辑模式
                form.dir_block.config(bg="#ffffff", highlightbackground="#cbd5e1")
                form.dir_entry.config(
                    state="normal",
                    background="#ffffff",
                    foreground="#1e293b",
                    selectbackground="#cbd5e1"
                )
                if form.display_dir_var.get() != form.custom_dir_var.get():
                    form.display_dir_var.set(form.custom_dir_var.get())
                
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
            is_vector = (form.fmt_var.get() in ("svg", "pdf", "emf"))
            state = "disabled" if is_vector else "readonly"
            form.quality_combo.config(state=state)
            form.dpi_combo.config(state=state)
            
            # 矢量格式不支持黑白双色，对颜色列表做过滤
            if is_vector:
                form.color_combo.config(values=Config.EXPORT_OPTIONS['colors'][:2])
                if form.color_var.get() == Config.EXPORT_OPTIONS['colors'][2]:
                    form.color_var.set(Config.EXPORT_OPTIONS['colors'][0])
            else:
                form.color_combo.config(values=Config.EXPORT_OPTIONS['colors'])
            self._update_preview()
            
        form.fmt_var.trace_add("write", on_format_changed)
        on_format_changed()

        # 3. 勾选及各下拉变动后实时触发重绘与估算
        form.border_var.trace_add("write", lambda *a: self._update_preview())
        form.color_var.trace_add("write", lambda *a: self._update_preview())
        form.quality_var.trace_add("write", lambda *a: self._update_preview())
        form.dpi_var.trace_add("write", lambda *a: self._update_preview())
        
        # 窗口大小改动后自动对齐画布居中
        self.preview_panel.preview_canvas.bind("<Configure>", lambda e: self._update_preview())

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
            # 二值黑白转换
            if img.mode in ("RGBA", "LA"):
                r, g, b, a = img.split()
                rgb_bw = Image.merge("RGB", (r, g, b)).convert("1").convert("L")
                img = Image.merge("RGBA", (rgb_bw, rgb_bw, rgb_bw, a))
            else:
                img = img.convert("1")
        
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
        
        if fmt in ("svg", "pdf", "emf"):
            form.width_lbl.config(text=f"导出宽度: {img.width} 像素 (矢量)")
            form.height_lbl.config(text=f"导出高度: {img.height} 像素 (矢量)")
        else:
            w_real = img.width * multiplier
            h_real = img.height * multiplier
            form.width_lbl.config(text=f"导出宽度: {w_real} 像素")
            form.height_lbl.config(text=f"导出高度: {h_real} 像素")
            
        # 精密估算大小（应用防抖）
        self._debounce_size_calc(data, dividend, divisor, q, rows, ctx, multiplier, fmt)

    def _debounce_size_calc(self, data, dividend, divisor, q, rows, ctx, multiplier, fmt):
        """ 采用统一防抖机制（250毫秒）联动异步线程模拟物理写入，测算百分之百精确的文件大小 """
        form = self.form_panel
        if getattr(self, '_calc_timer', None):
            try:
                self.dlg.after_cancel(self._calc_timer)
            except Exception:
                pass
                
        form.size_lbl.config(text="预估大小: 计算中...")
        
        # 生成递增自增的计算版本标识符，防止前一次慢计算返回后脏写覆盖新版界面显示
        if not hasattr(self, '_current_calc_id'):
            self._current_calc_id = 0
        self._current_calc_id = (self._current_calc_id + 1) % 10000
        calc_id = self._current_calc_id
        
        def run_precise_calc_thread():
            import threading
            
            def worker():
                try:
                    if fmt in ("svg", "pdf", "emf"):
                        size_text = Exporter.estimate_vector_size(
                            self.app, fmt, data, dividend, divisor, q, rows, ctx,
                            form.color_var.get(), form.border_var.get()
                        )
                    else:
                        save_fmt = "JPEG" if fmt == "jpg" else "PNG"
                        precise_size = Exporter.calculate_precise_bitmap_size(
                            self.app, data, dividend, divisor, q, rows, ctx,
                            form.color_var.get(), form.border_var.get(), multiplier, save_fmt, form.dpi_var.get()
                        )
                        size_text = f"{precise_size:.1f} KB"
                    
                    # 线程安全回调
                    def update_ui():
                        if getattr(self, '_current_calc_id', None) == calc_id:
                            form.size_lbl.config(text=f"预估大小: {size_text}")
                            
                    self.dlg.after(0, update_ui)
                except Exception:
                    pass
            
            # 以守护线程启动计算任务
            t = threading.Thread(target=worker, daemon=True)
            t.start()
                
        self._calc_timer = self.dlg.after(250, run_precise_calc_thread)

    def _on_export_success(self, out_path, export_dir):
        """ 导出成功的主线程回调，唤起打勾徽章模态提示窗 """
        form = self.form_panel
        form.progress.stop()
        form.progress.pack_forget()
        form.set_widgets_state(tk.NORMAL)
        SuccessDialog(self.dlg, out_path, export_dir)

    def _on_export_failure(self, e):
        """ 导出失败的主线程回调 """
        form = self.form_panel
        form.progress.stop()
        form.progress.pack_forget()
        form.set_widgets_state(tk.NORMAL)
        self._show_error_dialog(e)

    def export_chart(self):
        """ 核心物理导出操作：拉起守护后台线程，避免写盘假死，实现极其顺滑的无阻塞用户体验 """
        import threading
        form = self.form_panel
        
        # 1. 前置校验：如果选择自定义目录，检验其路径是否在物理磁盘上真实存在，且是一个有效的目录
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
        form.set_widgets_state(tk.DISABLED)
        form.progress.pack(fill=tk.BOTH, expand=True)
        form.progress.start(10)
        
        # 3. 收集表单状态参数以供渲染计算使用
        fmt = form.fmt_var.get()
        show_border = form.border_var.get()
        color_mode = form.color_var.get()
        quality = form.quality_var.get()
        dpi = form.dpi_var.get()
        
        # 4. 后台物理写入
        def async_worker():
            try:
                out_path, export_dir = Exporter.export(
                    self.app,
                    fmt,
                    show_border,
                    color_mode,
                    quality,
                    dpi,
                    dir_mode,
                    custom_dir
                )
                # 成功回调
                self.dlg.after(0, lambda: self._on_export_success(out_path, export_dir))
            except Exception as e:
                # 失败回调
                self.dlg.after(0, lambda: self._on_export_failure(e))
                
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
