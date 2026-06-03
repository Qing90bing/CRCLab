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
        super().__init__(parent, bg=self.bg_color, padx=16, pady=16, width=Config.LAYOUT['export_side_width'])
        self.dialog = dialog
        self.app = dialog.app
        self.pack_propagate(False)

        # 1. 区域主标题描述
        tk.Label(
            self, 
            text=Config.UI_TEXT['export_params'], 
            bg=self.bg_color,
            font=Config.FONTS['zh_bold']
        ).pack(anchor=tk.W, pady=(0, 10))
        
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
        self.dpi_var = tk.IntVar(value=Config.EXPORT_VALUES['dpi'])
        self.color_var = tk.StringVar(value=Config.EXPORT_VALUES['color'])
        self.border_var = tk.BooleanVar(value=Config.EXPORT_VALUES['show_border'])
        self.dir_mode_var = tk.StringVar(value=Config.EXPORT_VALUES['dir_mode'])
        self.custom_dir_var = tk.StringVar(value=Config.EXPORT_VALUES['custom_dir'])
        self.display_dir_var = tk.StringVar()

    def _build_form_widgets(self):
        """ 构建表单的核心下拉组合框及自适应路径展示框 """
        # 第一行：“格式” 和 “像素倍率”
        row1_frame = tk.Frame(self, bg=self.bg_color)
        row1_frame.pack(fill=tk.X, pady=(4, 6))
        row1_frame.columnconfigure(0, weight=1)
        row1_frame.columnconfigure(1, weight=1)
        
        col1_1 = tk.Frame(row1_frame, bg=self.bg_color)
        col1_1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        col1_2 = tk.Frame(row1_frame, bg=self.bg_color)
        col1_2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        
        self.fmt_combo = self._add_combo_to_parent(col1_1, Config.UI_TEXT['export_format'], self.fmt_var, Config.EXPORT_OPTIONS['formats'])
        self.quality_combo = self._add_combo_to_parent(col1_2, Config.UI_TEXT['export_quality'], self.quality_var, Config.EXPORT_OPTIONS['qualities'])
        
        # 第二行：“DPI” 和 “颜色”
        row2_frame = tk.Frame(self, bg=self.bg_color)
        row2_frame.pack(fill=tk.X, pady=(6, 6))
        row2_frame.columnconfigure(0, weight=1)
        row2_frame.columnconfigure(1, weight=1)
        
        col2_1 = tk.Frame(row2_frame, bg=self.bg_color)
        col2_1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        col2_2 = tk.Frame(row2_frame, bg=self.bg_color)
        col2_2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        
        self.dpi_combo = self._add_combo_to_parent(col2_1, Config.UI_TEXT['export_dpi'], self.dpi_var, Config.EXPORT_OPTIONS['dpis'])
        self.color_combo = self._add_combo_to_parent(col2_2, Config.UI_TEXT['export_color'], self.color_var, Config.EXPORT_OPTIONS['colors'])
        
        # 使用现代原生 API 按钮 (ttk.Checkbutton)
        style = ttk.Style()
        style.configure('ExportCheck.TCheckbutton', background=self.bg_color, font=Config.FONTS['zh_normal'])
        
        self.border_check = ttk.Checkbutton(
            self, 
            text=Config.UI_TEXT['export_show_border'], 
            variable=self.border_var, 
            command=self.dialog._update_preview,
            style='ExportCheck.TCheckbutton'
        )
        self.border_check.pack(anchor=tk.W, pady=(15, 15))
        
        # 导出路径及自定义选择区
        self.dir_mode_combo = self._add_combo(Config.UI_TEXT['export_dir'], self.dir_mode_var, Config.EXPORT_OPTIONS['dir_modes'])
  
        self.browse_btn = ttk.Button(self, text=Config.UI_TEXT['export_btn_browse'], state=tk.DISABLED, command=self._pick_export_dir)
        self.browse_btn.pack(fill=tk.X, pady=(5, 8))
        
        # 精美的信息块 (Block) 来展示当前选定的导出路径
        self.dir_block = tk.Frame(
            self,
            bg="#f8fafc",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            padx=10,
            pady=8
        )
        self.dir_block.pack(fill=tk.X, pady=(0, 8))
        
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

    def _build_info_and_actions(self):
        """ 绘制导出规格预估面板，动画进度条及底层取消、确认按钮 """
        self.info_group = ttk.LabelFrame(self, text=Config.UI_TEXT['export_info_group'])
        self.info_group.pack(fill=tk.X, pady=(15, 10))
        
        info_inner = tk.Frame(self.info_group, bg=self.bg_color, padx=12, pady=10)
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

        # 进度条专属动画容器，高度固定为 18 像素，防止展开进度条时页面整体发生抖动
        self.progress_container = tk.Frame(self, bg=self.bg_color, height=18)
        self.progress_container.pack(fill=tk.X, pady=(8, 4))
        self.progress_container.pack_propagate(False)
        
        self.progress = ttk.Progressbar(self.progress_container, orient=tk.HORIZONTAL, mode='indeterminate')

        # 确认与取消动作区域
        btn_frame = tk.Frame(self, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=(10, 16))
        
        ttk.Button(btn_frame, text=Config.UI_TEXT['btn_cancel'], command=self.dialog.dlg.destroy).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        self.export_btn = ttk.Button(btn_frame, text=Config.UI_TEXT['btn_start_export'], command=self.dialog.export_chart, style='Action.TButton')
        self.export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

    def _add_combo(self, label, var, values):
        """ 组合框小部件构建 helper """
        tk.Label(
            self, 
            text=label, 
            bg=self.bg_color,
            font=Config.FONTS['zh_normal']
        ).pack(anchor=tk.W, pady=(6, 2))
        
        combo = ttk.Combobox(self, textvariable=var, values=values, state="readonly")
        combo.pack(fill=tk.X)
        return combo

    def _add_combo_to_parent(self, parent, label, var, values):
        """ 组合框小部件构建 helper，指定父级容器 """
        tk.Label(
            parent, 
            text=label, 
            bg=self.bg_color,
            font=Config.FONTS['zh_normal']
        ).pack(anchor=tk.W, pady=(2, 2))
        
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        combo.pack(fill=tk.X, expand=True)
        return combo

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
        self.fmt_combo.config(state=combo_state)
        self.color_combo.config(state=combo_state)
        self.dir_mode_combo.config(state=combo_state)
        self.border_check.config(state=state)
        
        is_vector = (self.fmt_var.get() in ("svg", "pdf", "emf"))
        self.quality_combo.config(state=combo_state if not is_vector else tk.DISABLED)
        self.dpi_combo.config(state=combo_state if not is_vector else tk.DISABLED)
        
        is_custom = (self.dir_mode_var.get() == Config.EXPORT_OPTIONS['dir_modes'][1])
        self.browse_btn.config(state=state if is_custom else tk.DISABLED)
        
        # 自定义路径输入框的只读/常规及发灰样式控制
        if state == tk.DISABLED:
            self.dir_entry.config(state="disabled")
        else:
            self.dir_entry.config(state="normal" if is_custom else "disabled")
