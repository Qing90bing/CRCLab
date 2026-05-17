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
    """
    def __init__(self, app):
        """
        初始化并打开导出对话框。
        :param app: 主应用程序实例，用于共享数据和渲染器。
        """
        self.app = app
        self.dlg = tk.Toplevel(app.root)
        self.dlg.title("导出图表")
        self.dlg.transient(app.root)
        
        self._setup_geometry()
        self._build_layout()
        self._setup_bindings()
        
        # 首次同步与双通道防闪烁定位延迟居中，确保初始化呈现正常
        self._update_preview()
        self.dlg.after(100, self._update_preview)

    def _setup_geometry(self):
        """ 智能自适应屏幕分辨率并居中显示 """
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()
        w = min(1560, int(sw * 0.85))
        h = min(980, int(sh * 0.85))
        self.dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.dlg.minsize(1050, 700)

    def _build_layout(self):
        """ 构建导出界面的双栏框架 """
        self.left_frame = tk.Frame(self.dlg, bg="#f8fafc", padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.dlg, bg="#ffffff", padx=16, pady=16, width=340)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_frame.pack_propagate(False)
        
        self._init_preview_frame(self.left_frame)
        self._init_control_frame(self.right_frame)

    def _init_preview_frame(self, parent):
        """ 初始化左侧的高清实时重绘预览面板 """
        tk.Label(parent, text="导出预览", bg="#f8fafc", font=("SimSun", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        self.preview_canvas = tk.Canvas(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def _init_control_frame(self, parent):
        """ 构建右侧的全部控制参数表单及触发按钮 """
        tk.Label(parent, text="导出参数", bg="#ffffff", font=("SimSun", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.fmt_var = tk.StringVar(value="png")
        self.quality_var = tk.StringVar(value="标清默认尺寸1倍")
        self.dpi_var = tk.IntVar(value=96)
        self.color_var = tk.StringVar(value="彩色")
        self.border_var = tk.BooleanVar(value=True)
        self.dir_mode_var = tk.StringVar(value="当前目录（导出结果）")
        self.custom_dir_var = tk.StringVar(value="")

        self.fmt_combo = self._add_combo(parent, "格式", self.fmt_var, ["png", "jpg", "svg"])
        self.quality_combo = self._add_combo(parent, "画质", self.quality_var, [
            "标清默认尺寸", "标清默认尺寸1倍", "标清默认尺寸2倍", "标清默认尺寸3倍", "高清默认尺寸1倍", "高清默认尺寸2倍"
        ])
        self.dpi_combo = self._add_combo(parent, "DPI", self.dpi_var, [72, 96, 150, 200, 300, 600])
        self.color_combo = self._add_combo(parent, "颜色", self.color_var, ["彩色", "灰度", "黑白"])
        
        self._add_custom_check(parent, "显示纸张边框", self.border_var, self._update_preview)
        self._add_combo(parent, "导出目录", self.dir_mode_var, ["当前目录（导出结果）", "自定义目录"])

        self.browse_btn = tk.Button(parent, text="浏览目录", state=tk.DISABLED, command=self._pick_export_dir)
        self.browse_btn.pack(fill=tk.X, pady=(5, 2))
        
        self.dir_lbl = tk.Label(parent, textvariable=self.custom_dir_var, bg="#ffffff", fg="#64748b", anchor="w", wraplength=300)
        self.dir_lbl.pack(fill=tk.X, pady=(0, 8))
        
        tk.Button(
            parent, text="执行导出", bg="#3b82f6", fg="white", font=("SimSun", 10, "bold"),
            command=self.export_chart
        ).pack(fill=tk.X, pady=(10, 0))

    def _setup_bindings(self):
        """ 绑定变量变化及窗口尺寸重构事件的实时监听 """
        def on_dir_mode_changed(*_):
            self.browse_btn.config(state=(tk.NORMAL if self.dir_mode_var.get() == "自定义目录" else tk.DISABLED))
        self.dir_mode_var.trace_add("write", on_dir_mode_changed)

        def on_format_changed(*_):
            state = "disabled" if self.fmt_var.get() == "svg" else "readonly"
            self.quality_combo.config(state=state)
            self.dpi_combo.config(state=state)
        self.fmt_var.trace_add("write", on_format_changed)

        # 联动重绘预览
        self.border_var.trace_add("write", lambda *a: self._update_preview())
        self.color_var.trace_add("write", lambda *a: self._update_preview())

        # 监听画布大小改变，始终保持预览内容在中心
        self.preview_canvas.bind("<Configure>", lambda e: self._recenter_canvas())

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
        if self.color_var.get() == "灰度":
            img = img.convert("L")
        elif self.color_var.get() == "黑白":
            img = img.convert("1")
        
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor="center")
        self.preview_canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
        self._recenter_canvas()

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
        d = filedialog.askdirectory(title="选择导出目录")
        if d:
            self.custom_dir_var.set(d)

    def export_chart(self):
        """ 执行高保真大图导出的核心逻辑，统一处理 SVG 和高倍率位图输出 """
        try:
            multiplier = {
                "标清默认尺寸": 1, "标清默认尺寸1倍": 1, "标清默认尺寸2倍": 2,
                "标清默认尺寸3倍": 3, "高清默认尺寸1倍": 4, "高清默认尺寸2倍": 6
            }[self.quality_var.get()]

            export_dir = os.path.join(os.getcwd(), "导出结果") if self.dir_mode_var.get() == "当前目录（导出结果）" else self.custom_dir_var.get()
            if not export_dir:
                raise ValueError("已选择“自定义目录”，但尚未通过“浏览目录”按钮指定具体导出路径。")
            os.makedirs(export_dir, exist_ok=True)
            
            fmt = self.fmt_var.get()
            out_path = os.path.join(export_dir, f"crc_export.{fmt}")

            if fmt == "svg":
                self._save_svg(out_path)
            else:
                self._save_bitmap(out_path, multiplier)

            messagebox.showinfo("导出成功", f"图表已成功导出至：\n{out_path}")
        except Exception as e:
            self._show_error_dialog(e)

    def _save_svg(self, out_path):
        """ 保存为 SVG 矢量格式 """
        try:
            import canvasvg
        except ImportError as e:
            raise RuntimeError("SVG 导出依赖缺失：未安装 canvasvg。") from e
        canvasvg.saveall(out_path, self.app.canvas)

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
        if color_mode == "灰度":
            img = img.convert("L")
        elif color_mode == "黑白":
            img = img.convert("1")
        else:
            img = img.convert("RGB")
            
        save_fmt = "JPEG" if out_path.endswith(".jpg") else "PNG"
        img.save(out_path, format=save_fmt, dpi=(self.dpi_var.get(), self.dpi_var.get()))

    def _show_error_dialog(self, e):
        """ 展示导出失败信息对话框 """
        messagebox.showerror(
            "导出失败",
            "导出过程中发生错误，请按以下信息排查：\n\n"
            f"1) 错误类型: {type(e).__name__}\n"
            f"2) 错误详情: {str(e)}\n"
            f"3) 建议排查: 请确认目录写入权限或导出参数是否有效。"
        )

    def _add_combo(self, parent, label, var, values):
        """ 通用组合框下拉组件封装 """
        tk.Label(parent, text=label, bg="#ffffff", font=("SimSun", 10)).pack(anchor=tk.W, pady=(6, 2))
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        combo.pack(fill=tk.X)
        return combo

    def _add_custom_check(self, parent, text, var, command):
        """ 绘制现代化大尺寸的自定义高亮勾选框 """
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
            if command:
                command()
                
        canvas.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)
        refresh()
