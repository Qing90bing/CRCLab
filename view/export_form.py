import os
import tkinter as tk
from tkinter import ttk, filedialog
from config.constants import Config

class ExportForm(tk.Frame):
    """
    导出图表配置中的右侧参数表单与动作按钮面板。
    
    高内聚封装参数绑定、按钮绑定和状态控制，通过代理通知外层对话框进行重绘与计算。
    """
    def __init__(self, parent, dialog):
        """
        初始化参数控制表单。
        :param parent: 父级容器。
        :param dialog: 导出对话框 ExportDialog 协调器实例。
        """
        self.bg_color = parent.cget('bg')
        super().__init__(parent, bg=self.bg_color, padx=0, pady=0, width=Config.LAYOUT['export_side_width'])
        self.dialog = dialog
        self.app = dialog.app
        self.pack_propagate(False)

        # 1. 区域主标题描述
        tk.Label(
            self, 
            text=Config.UI_TEXT['export_params'], 
            bg=self.bg_color,
            font=Config.FONTS['zh_bold']
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # 2. 状态变量统一加载
        self._init_form_variables()
        
        # 3. 构造界面选项控件（下拉菜单与多选框等）
        self._build_form_widgets()
        
        # 4. 后台预估信息区与底部操作按钮
        self._build_info_and_actions()

    def _init_form_variables(self):
        """ 显式初始化所有局部表单控制相关的 Tkinter 变量 """
        self.fmt_var = tk.StringVar(value=Config.EXPORT_VALUES['format'])
        self.quality_var = tk.StringVar(value=Config.EXPORT_VALUES['quality'])
        self.jpg_quality_var = tk.DoubleVar(value=Config.EXPORT_VALUES['jpg_quality'])
        self.dpi_var = tk.IntVar(value=Config.EXPORT_VALUES['dpi'])
        self.color_var = tk.StringVar(value=Config.EXPORT_VALUES['color'])
        self.border_var = tk.BooleanVar(value=Config.EXPORT_VALUES['show_border'])
        self.dir_mode_var = tk.StringVar(value=Config.EXPORT_VALUES['dir_mode'])
        self.custom_dir_var = tk.StringVar(value=Config.EXPORT_VALUES['custom_dir'])
        self.display_dir_var = tk.StringVar()

    def _build_form_widgets(self):
        """ 构建表单的核心下拉组合框及自适应路径展示框 """
        _, spec_inner = self._make_group(Config.UI_TEXT['export_spec_group'], pady=(0, 10))

        # 第一行：“格式” 和 “像素倍率”
        row1_frame = tk.Frame(spec_inner, bg=self.bg_color)
        row1_frame.pack(fill=tk.X, pady=(0, 8))
        row1_frame.columnconfigure(0, weight=1)
        row1_frame.columnconfigure(1, weight=1)
        
        col1_1 = tk.Frame(row1_frame, bg=self.bg_color)
        col1_1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        col1_2 = tk.Frame(row1_frame, bg=self.bg_color)
        col1_2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        
        self.fmt_combo = self._add_combo_to_parent(col1_1, Config.UI_TEXT['export_format'], self.fmt_var, Config.EXPORT_OPTIONS['formats'])
        self.quality_combo = self._add_combo_to_parent(col1_2, Config.UI_TEXT['export_quality'], self.quality_var, Config.EXPORT_OPTIONS['qualities'])
        
        # 第二行：“DPI” 和 “颜色”
        row2_frame = tk.Frame(spec_inner, bg=self.bg_color)
        row2_frame.pack(fill=tk.X, pady=(0, 8))
        row2_frame.columnconfigure(0, weight=1)
        row2_frame.columnconfigure(1, weight=1)
        
        col2_1 = tk.Frame(row2_frame, bg=self.bg_color)
        col2_1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        col2_2 = tk.Frame(row2_frame, bg=self.bg_color)
        col2_2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        
        self.dpi_combo = self._add_combo_to_parent(col2_1, Config.UI_TEXT['export_dpi'], self.dpi_var, Config.EXPORT_OPTIONS['dpis'])
        self.color_combo = self._add_combo_to_parent(col2_2, Config.UI_TEXT['export_color'], self.color_var, Config.EXPORT_OPTIONS['colors'])

        self.jpg_quality_label = tk.Label(
            spec_inner,
            text=self._format_jpg_quality_text(),
            bg=self.bg_color,
            font=Config.FONTS['zh_normal'],
            anchor="w"
        )
        self.jpg_quality_label.pack(fill=tk.X, pady=(2, 3))

        style = ttk.Style()
        style.configure(
            'Export.Horizontal.TScale',
            background=self.bg_color,
            troughcolor=self.bg_color
        )

        self.jpg_quality_scale = ttk.Scale(
            spec_inner,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.jpg_quality_var,
            command=self._on_jpg_quality_changed,
            style='Export.Horizontal.TScale'
        )
        self.jpg_quality_scale.pack(fill=tk.X, pady=(0, 2))
        self.jpg_quality_scale.bind("<Button-1>", self._on_jpg_quality_pointer)
        self.jpg_quality_scale.bind("<B1-Motion>", self._on_jpg_quality_pointer)
        
        # 使用现代原生 API 按钮 (ttk.Checkbutton)
        style = ttk.Style()
        style.configure('ExportCheck.TCheckbutton', background=self.bg_color, font=Config.FONTS['zh_normal'])
        
        self.border_check = ttk.Checkbutton(
            spec_inner, 
            text=Config.UI_TEXT['export_show_border'], 
            variable=self.border_var, 
            command=self.dialog._update_preview,
            style='ExportCheck.TCheckbutton'
        )
        self.border_check.pack(anchor=tk.W, pady=(8, 0))

        _, output_inner = self._make_group(Config.UI_TEXT['export_output_group'], pady=(0, 10))
        
        # 导出路径及自定义选择区
        self.dir_mode_combo = self._add_combo_to_parent(output_inner, Config.UI_TEXT['export_dir'], self.dir_mode_var, Config.EXPORT_OPTIONS['dir_modes'])
  
        self.browse_btn = ttk.Button(output_inner, text=Config.UI_TEXT['export_btn_browse'], state=tk.DISABLED, command=self._pick_export_dir)
        self.browse_btn.pack(fill=tk.X, pady=(8, 8))
        
        # 精美的信息块 (Block) 来展示当前选定的导出路径
        self.dir_block = tk.Frame(
            output_inner,
            bg="#f8fafc",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            padx=10,
            pady=8
        )
        self.dir_block.pack(fill=tk.X)
        
        # 只读的 Entry 小部件来承载路径显示，支持鼠标左右拖动、全选复制，且绝不折行或挤占布局
        self.dir_entry = tk.Entry(
            self.dir_block,
            textvariable=self.display_dir_var,
            font=Config.FONTS['zh_normal'],
            bg="#f8fafc",
            fg="#475569",
            bd=0,
            highlightthickness=0,
            state="readonly",
            readonlybackground="#f8fafc",
            selectbackground="#cbd5e1"
        )
        self.dir_entry.pack(fill=tk.X, expand=True)

    def _make_group(self, title, pady):
        """ 创建原生分组框及统一内边距容器。 """
        group = ttk.LabelFrame(self, text=title)
        group.pack(fill=tk.X, pady=pady)
        inner = tk.Frame(group, bg=self.bg_color, padx=12, pady=10)
        inner.pack(fill=tk.BOTH, expand=True)
        return group, inner

    def _build_info_and_actions(self):
        """ 绘制导出规格预估面板，动画进度条及底层取消、确认按钮 """
        self.info_group = ttk.LabelFrame(self, text=Config.UI_TEXT['export_info_group'])
        self.info_group.pack(fill=tk.X, pady=(0, 10))
        
        info_inner = tk.Frame(self.info_group, bg=self.bg_color, padx=12, pady=9)
        info_inner.pack(fill=tk.BOTH, expand=True)
        
        # 宽、高与体积预估显示标签
        self.width_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_width_placeholder'], bg=self.bg_color, font=Config.FONTS['zh_normal'], anchor="w")
        self.width_lbl.pack(fill=tk.X, pady=2)
        
        self.height_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_height_placeholder'], bg=self.bg_color, font=Config.FONTS['zh_normal'], anchor="w")
        self.height_lbl.pack(fill=tk.X, pady=2)
        
        self.size_lbl = tk.Label(info_inner, text=Config.UI_TEXT['export_size_placeholder'], bg=self.bg_color, font=Config.FONTS['zh_normal'], anchor="w")
        self.size_lbl.pack(fill=tk.X, pady=2)

        # 底部按钮强对齐填充器 (弹簧弹性框架)
        tk.Frame(self, bg=self.bg_color).pack(fill=tk.BOTH, expand=True)

        # 固定的进度条，默认设置为 determinate 且进度为 0，这样空闲时不显示绿色滑块
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate', value=0)
        self.progress.pack(fill=tk.X, pady=(6, 4))

        # 确认与取消动作区域
        btn_frame = tk.Frame(self, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=(8, 12))
        
        ttk.Button(btn_frame, text=Config.UI_TEXT['btn_cancel'], command=self.dialog.dlg.destroy).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        self.export_btn = ttk.Button(btn_frame, text=Config.UI_TEXT['btn_start_export'], command=self.dialog.export_chart, style='Action.TButton')
        self.export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

    def _add_combo(self, label, var, values):
        """ 组合框小部件构建 helper """
        label_widget = tk.Label(
            self, 
            text=label, 
            bg=self.bg_color,
            font=Config.FONTS['zh_normal']
        )
        label_widget.pack(anchor=tk.W, pady=(6, 2))
        
        combo = ttk.Combobox(self, textvariable=var, values=values, state="readonly")
        setattr(combo, "label_widget", label_widget)
        combo.pack(fill=tk.X)
        return combo

    def _add_combo_to_parent(self, parent, label, var, values):
        """ 组合框小部件构建 helper，指定父级容器 """
        label_widget = tk.Label(
            parent, 
            text=label, 
            bg=self.bg_color,
            font=Config.FONTS['zh_normal']
        )
        label_widget.pack(anchor=tk.W, pady=(2, 2))
        
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        setattr(combo, "label_widget", label_widget)
        combo.pack(fill=tk.X, expand=True)
        return combo

    def _format_jpg_quality_text(self):
        """ 生成 JPG 质量滑块的展示文本。 """
        value = int(round(float(self.jpg_quality_var.get())))
        if value < 50:
            level = "低"
        elif value < 80:
            level = "中"
        else:
            level = "高"
        return f"{Config.UI_TEXT['export_jpg_quality']}：{value}%（{level}）"

    def _on_jpg_quality_changed(self, _=None):
        """ 同步质量文案，并在 JPG 格式下刷新预估大小。 """
        value = int(round(float(self.jpg_quality_var.get())))
        value = max(10, min(100, value))
        if float(self.jpg_quality_var.get()) != value:
            self.jpg_quality_var.set(value)
        self.jpg_quality_label.config(text=self._format_jpg_quality_text())
        if self.fmt_var.get() == "jpg":
            self.dialog._update_preview()

    def _on_jpg_quality_pointer(self, event):
        """ 让质量滑块支持点击轨道立即跳转到对应百分比。 """
        if "disabled" in self.jpg_quality_scale.state():
            return "break"

        low = float(self.jpg_quality_scale.cget("from"))
        high = float(self.jpg_quality_scale.cget("to"))
        try:
            start_coords = self.jpg_quality_scale.tk.call(str(self.jpg_quality_scale), "coords", low)
            end_coords = self.jpg_quality_scale.tk.call(str(self.jpg_quality_scale), "coords", high)
            if isinstance(start_coords, str):
                start_coords = self.jpg_quality_scale.tk.splitlist(start_coords)
            if isinstance(end_coords, str):
                end_coords = self.jpg_quality_scale.tk.splitlist(end_coords)
            x0 = float(start_coords[0])
            x1 = float(end_coords[0])
        except Exception:
            x0 = 0.0
            x1 = float(max(1, self.jpg_quality_scale.winfo_width()))

        if x0 == x1:
            return "break"

        ratio = (event.x - x0) / (x1 - x0)
        value = int(round(low + max(0.0, min(1.0, ratio)) * (high - low)))
        self.jpg_quality_var.set(value)
        self._on_jpg_quality_changed()
        return "break"

    def set_labeled_combo_state(self, combo, state):
        """ 同步设置下拉框状态和对应标签的启用/禁用文字颜色。 """
        combo.config(state=state)
        label = getattr(combo, "label_widget", None)
        if label is not None:
            fg = Config.COLORS['text_muted'] if state == tk.DISABLED else Config.COLORS['fg_enabled']
            label.config(fg=fg)

    def set_jpg_quality_state(self, state):
        """ 根据当前格式启用或禁用 JPG 质量滑块。 """
        self.jpg_quality_scale.config(state=state)
        fg = Config.COLORS['fg_enabled'] if state == tk.NORMAL else Config.COLORS['text_muted']
        self.jpg_quality_label.config(fg=fg, text=self._format_jpg_quality_text())

    def _pick_export_dir(self):
        """ 打开系统文件夹浏览器以挑选目标路径 """
        d = filedialog.askdirectory(title=Config.UI_TEXT['dialog_pick_dir_title'])
        if d:
            self.custom_dir_var.set(d)

    def set_widgets_state(self, state):
        """
        统一批量改变该表单下所有交互组件的启用/禁用视觉状态，防范高频二次点按及线程冲突。
        
        :param state: tk.NORMAL 或 tk.DISABLED。
        """
        self.export_btn.config(state=state)
        # 协同设定底层取消按钮
        for child in self.export_btn.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state=state)
        
        # 联动下拉选择菜单（当启用时，下拉菜单应设置为 readonly 而非 normal，防止用户输入文字）
        combo_state = "readonly" if state == tk.NORMAL else tk.DISABLED
        self.set_labeled_combo_state(self.fmt_combo, combo_state)
        self.set_labeled_combo_state(self.color_combo, combo_state)
        self.set_labeled_combo_state(self.dir_mode_combo, combo_state)
        self.border_check.config(state=state)
        
        is_vector = (self.fmt_var.get() in ("svg", "pdf", "emf"))
        self.set_labeled_combo_state(self.quality_combo, combo_state if not is_vector else tk.DISABLED)
        self.set_labeled_combo_state(self.dpi_combo, combo_state if not is_vector else tk.DISABLED)
        self.set_jpg_quality_state(tk.NORMAL if state == tk.NORMAL and self.fmt_var.get() == "jpg" else tk.DISABLED)
        
        is_custom = (self.dir_mode_var.get() == Config.EXPORT_OPTIONS['dir_modes'][1])
        self.browse_btn.config(state=state if is_custom else tk.DISABLED)
        
        # 自定义路径输入框的只读/常规及发灰样式控制
        if state == tk.DISABLED:
            self.dir_entry.config(state="disabled")
        else:
            self.dir_entry.config(state="normal" if is_custom else "disabled")
