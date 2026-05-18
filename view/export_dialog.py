import os
import io
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
from config.constants import Config
from view.widgets import ModernCheckbutton
from view.exporter import Exporter
from view.success_dialog import SuccessDialog

class ExportDialog:
    """
    导出图表配置与预览弹出对话框。
    
    统一协调导出选项配置、画布异步/防抖预览更新，并代理调用 Exporter 服务进行物理写入。
    """
    def __init__(self, app):
        """
        初始化导出对话框。
        """
        self.app = app
        self._calc_timer = None
        self.dlg = tk.Toplevel(app.root)
        self.dlg.title(Config.UI_TEXT['export_title'])
        self.dlg.transient(app.root)
        
        self._setup_geometry()
        self._build_layout()
        self._setup_bindings()
        
        # 首次同步与延迟定位居中
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
        """ 初始化左侧实时重绘预览面板 """
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
        """ 构建右侧的参数表单与动作按钮 """
        tk.Label(
            parent, 
            text=Config.UI_TEXT['export_params'], 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_bold']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 1. 变量加载
        self._init_form_variables()
        
        # 2. 下拉菜单与勾选框挂载
        self._build_form_widgets(parent)
        
        # 3. 后台估算面板及底部动作按钮
        self._build_info_and_actions(parent)

    def _init_form_variables(self):
        """ 载入默认状态参数 """
        self.fmt_var = tk.StringVar(value=Config.EXPORT_VALUES['format'])
        self.quality_var = tk.StringVar(value=Config.EXPORT_VALUES['quality'])
        self.dpi_var = tk.IntVar(value=Config.EXPORT_VALUES['dpi'])
        self.color_var = tk.StringVar(value=Config.EXPORT_VALUES['color'])
        self.border_var = tk.BooleanVar(value=Config.EXPORT_VALUES['show_border'])
        self.dir_mode_var = tk.StringVar(value=Config.EXPORT_VALUES['dir_mode'])
        self.custom_dir_var = tk.StringVar(value=Config.EXPORT_VALUES['custom_dir'])

    def _build_form_widgets(self, parent):
        """ 绑定下拉菜单并挂载 ModernCheckbutton 小部件 """
        self.fmt_combo = self._add_combo(parent, Config.UI_TEXT['export_format'], self.fmt_var, Config.EXPORT_OPTIONS['formats'])
        self.quality_combo = self._add_combo(parent, Config.UI_TEXT['export_quality'], self.quality_var, Config.EXPORT_OPTIONS['qualities'])
        self.dpi_combo = self._add_combo(parent, Config.UI_TEXT['export_dpi'], self.dpi_var, Config.EXPORT_OPTIONS['dpis'])
        self.color_combo = self._add_combo(parent, Config.UI_TEXT['export_color'], self.color_var, Config.EXPORT_OPTIONS['colors'])
        
        self.border_check = ModernCheckbutton(
            parent, 
            Config.UI_TEXT['export_show_border'], 
            self.border_var, 
            self._update_preview,
            bg=Config.LAYOUT['export_ctrl_bg']
        )
        self.border_check.pack(anchor=tk.W, pady=(28, Config.LAYOUT['section_pady']))
        
        self._add_combo(parent, Config.UI_TEXT['export_dir'], self.dir_mode_var, Config.EXPORT_OPTIONS['dir_modes'])
 
        self.browse_btn = ttk.Button(parent, text=Config.UI_TEXT['export_btn_browse'], state=tk.DISABLED, command=self._pick_export_dir)
        self.browse_btn.pack(fill=tk.X, pady=(5, 2))
        
        self.dir_lbl = tk.Label(parent, textvariable=self.custom_dir_var, bg=Config.LAYOUT['export_ctrl_bg'], fg=Config.COLORS['dir_lbl_fg'], anchor="w", wraplength=300)
        self.dir_lbl.pack(fill=tk.X, pady=(0, 8))

    def _build_info_and_actions(self, parent):
        """ 绘制导出预估值面板及底层取消和确认导出按钮 """
        self.info_group = ttk.LabelFrame(parent, text=Config.UI_TEXT['export_info_group'])
        self.info_group.pack(fill=tk.X, pady=(15, 10))
        
        info_inner = tk.Frame(self.info_group, bg=Config.LAYOUT['export_ctrl_bg'], padx=12, pady=10)
        info_inner.pack(fill=tk.BOTH, expand=True)
        
        self.width_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_width_placeholder'], bg=Config.LAYOUT['export_ctrl_bg'], font=Config.FONTS['zh_normal'], anchor="w")
        self.width_lbl.pack(fill=tk.X, pady=2)
        
        self.height_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_height_placeholder'], bg=Config.LAYOUT['export_ctrl_bg'], font=Config.FONTS['zh_normal'], anchor="w")
        self.height_lbl.pack(fill=tk.X, pady=2)
        
        self.size_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_size_placeholder'], bg=Config.LAYOUT['export_ctrl_bg'], font=Config.FONTS['zh_normal'], anchor="w")
        self.size_lbl.pack(fill=tk.X, pady=2)

        # 弹性推力，使按钮强对齐底部
        tk.Frame(parent, bg=Config.LAYOUT['export_ctrl_bg']).pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(parent, bg=Config.LAYOUT['export_ctrl_bg'])
        btn_frame.pack(fill=tk.X, pady=(10, 16))
        
        ttk.Button(btn_frame, text=Config.UI_TEXT['btn_cancel'], command=self.dlg.destroy).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        self.export_btn = ttk.Button(btn_frame, text=Config.UI_TEXT['btn_start_export'], command=self.export_chart, style='Action.TButton')
        self.export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

    def _setup_bindings(self):
        """ 联动绑定下拉菜单、勾选框和自适应重绘事件 """
        def on_dir_mode_changed(*_):
            is_custom = (self.dir_mode_var.get() == Config.EXPORT_OPTIONS['dir_modes'][1])
            self.browse_btn.config(state=(tk.NORMAL if is_custom else tk.DISABLED))
        self.dir_mode_var.trace_add("write", on_dir_mode_changed)

        def on_format_changed(*_):
            is_vector = (self.fmt_var.get() in ("svg", "pdf", "emf"))
            state = "disabled" if is_vector else "readonly"
            self.quality_combo.config(state=state)
            self.dpi_combo.config(state=state)
            
            if is_vector:
                self.color_combo.config(values=Config.EXPORT_OPTIONS['colors'][:2])
                if self.color_var.get() == Config.EXPORT_OPTIONS['colors'][2]:
                    self.color_var.set(Config.EXPORT_OPTIONS['colors'][0])
            else:
                self.color_combo.config(values=Config.EXPORT_OPTIONS['colors'])
            self._update_preview()
            
        self.fmt_var.trace_add("write", on_format_changed)
        on_format_changed()

        self.border_var.trace_add("write", lambda *a: self._update_preview())
        self.color_var.trace_add("write", lambda *a: self._update_preview())
        self.quality_var.trace_add("write", lambda *a: self._update_preview())
        self.dpi_var.trace_add("write", lambda *a: self._update_preview())
        self.preview_canvas.bind("<Configure>", lambda e: self._update_preview())

    def _update_preview(self):
        """ 预览窗口的重绘实现，物理 view_scale 固定为 1.0 """
        self.preview_canvas.delete("all")
        data = self.app.data_var.get().strip()
        divisor = self.app.divisor_var.get().strip()
        if not data or not divisor:
            return
            
        q, rows, dividend = self.app.engine.calculate(data, divisor)
        ctx = self.app._get_render_context()
        ctx['view_scale'] = 1.0
        ctx['show_border'] = self.border_var.get()
        
        img = self.app.renderer.render(data, dividend, divisor, q, rows, ctx)
        if self.color_var.get() == Config.EXPORT_OPTIONS['colors'][1]:
            img = img.convert("L")
        elif self.color_var.get() == Config.EXPORT_OPTIONS['colors'][2]:
            img = img.convert("1")
        
        self._update_export_info(img, data, dividend, divisor, q, rows, ctx)
        self._render_scaled_preview(img)

    def _render_scaled_preview(self, img):
        """ 自适应预览画布尺寸，缩放并居中图像 """
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
        """ 调度 Exporter 估算模块刷新文件预估属性 """
        fmt = self.fmt_var.get()
        opt_q = Config.EXPORT_OPTIONS['qualities']
        
        multiplier = {
            opt_q[0]: 1, opt_q[1]: 1, opt_q[2]: 2,
            opt_q[3]: 3, opt_q[4]: 4, opt_q[5]: 6
        }.get(self.quality_var.get(), 1)
        
        if fmt in ("svg", "pdf", "emf"):
            self.width_lbl.config(text=f"导出宽度: {img.width} 像素 (矢量)")
            self.height_lbl.config(text=f"导出高度: {img.height} 像素 (矢量)")
            size_text = Exporter.estimate_vector_size(self.app, fmt, data, dividend, divisor, q, rows, ctx, self.color_var.get(), self.border_var.get())
            self.size_lbl.config(text=f"预估大小: {size_text}")
        else:
            w_real = img.width * multiplier
            h_real = img.height * multiplier
            self.width_lbl.config(text=f"导出宽度: {w_real} 像素")
            self.height_lbl.config(text=f"导出高度: {h_real} 像素")
            self._debounce_bitmap_size_calc(data, dividend, divisor, q, rows, ctx, multiplier, fmt)

    def _debounce_bitmap_size_calc(self, data, dividend, divisor, q, rows, ctx, multiplier, fmt):
        """ 对位图精密大小评估应用防抖缓冲，提升交互平滑度 """
        if getattr(self, '_calc_timer', None):
            try:
                self.dlg.after_cancel(self._calc_timer)
            except Exception:
                pass
                
        self.size_lbl.config(text="预估大小: 计算中...")
        save_fmt = "JPEG" if fmt == "jpg" else "PNG"
        
        def run_precise_calc():
            try:
                precise_size = Exporter.calculate_precise_bitmap_size(
                    self.app, data, dividend, divisor, q, rows, ctx,
                    self.color_var.get(), self.border_var.get(), multiplier, save_fmt, self.dpi_var.get()
                )
                self.size_lbl.config(text=f"预估大小: {precise_size:.1f} KB")
            except Exception:
                pass
                
        self._calc_timer = self.dlg.after(250, run_precise_calc)

    def _recenter_canvas(self):
        """ 物理平移归零，使预览图像始终居中 """
        self.preview_canvas.update_idletasks()
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        bbox = self.preview_canvas.bbox("all")
        if bbox:
            self.preview_canvas.xview_moveto(((bbox[0] + bbox[2]) / 2 - cw / 2 + 3000) / 6000)
            self.preview_canvas.yview_moveto(((bbox[1] + bbox[3]) / 2 - ch / 2 + 3000) / 6000)

    def _pick_export_dir(self):
        """ 唤起系统目录挑选面板 """
        d = filedialog.askdirectory(title=Config.UI_TEXT['dialog_pick_dir_title'])
        if d:
            self.custom_dir_var.set(d)

    def export_chart(self):
        """ 调度 Exporter 执行文件物理写入，并弹出 SuccessDialog """
        try:
            out_path, export_dir = Exporter.export(
                self.app,
                self.fmt_var.get(),
                self.border_var.get(),
                self.color_var.get(),
                self.quality_var.get(),
                self.dpi_var.get(),
                self.dir_mode_var.get(),
                self.custom_dir_var.get()
            )
            SuccessDialog(self.dlg, out_path, export_dir)
        except Exception as e:
            self._show_error_dialog(e)

    def _show_error_dialog(self, e):
        """ 格式化错误反馈 """
        messagebox.showerror(
            Config.MESSAGES['export_fail_title'],
            Config.MESSAGES['export_fail_body'].format(
                error_type=type(e).__name__,
                error_msg=str(e)
            )
        )

    def _add_combo(self, parent, label, var, values):
        """ 快速组合框小部件构建 helper """
        tk.Label(
            parent, 
            text=label, 
            bg=Config.LAYOUT['export_ctrl_bg'], 
            font=Config.FONTS['zh_normal']
        ).pack(anchor=tk.W, pady=(6, 2))
        
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        combo.pack(fill=tk.X)
        return combo
