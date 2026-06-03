import tkinter as tk
from tkinter import ttk
from typing import Literal
from config.constants import Config

Justify = Literal["left", "center", "right"]

class ReadonlyEntry(tk.Entry):
    """
    自定义扁平且只读的文本框。
    外观与常规 Label 无异，但支持用户手动选定、双击或拖拽进行 Ctrl+C 复制。
    """
    def __init__(self, parent, text_val, font, fg, bg, width=24, justify: Justify = "right"):
        super().__init__(
            parent, 
            relief="flat", 
            state="normal", 
            font=font, 
            fg=fg, 
            bg=bg, 
            width=width, 
            highlightthickness=0,
            justify=justify
        )
        self.insert(0, text_val)
        self.config(state="readonly")
        
    def set_value(self, val):
        self.config(state="normal")
        self.delete(0, tk.END)
        self.insert(0, val)
        self.config(state="readonly")

class ModernCheckbutton(tk.Frame):
    """
    大尺寸自定义复选框。
    利用 Canvas 绘制外边框与勾选对齐线，保证平台样式一致。
    """
    def __init__(self, parent, text, var, command=None, bg=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        self.var = var
        self.command = command
        self.bg_color = bg_color
        
        self.sz = Config.LAYOUT['check_size']
        self.canvas = tk.Canvas(self, width=self.sz+4, height=self.sz+4, bg=self.bg_color, highlightthickness=0, cursor="hand2")
        self.canvas.pack(side=tk.LEFT)
        
        self.lbl = tk.Label(self, text=text, bg=self.bg_color, font=Config.FONTS['zh_normal'], cursor="hand2")
        self.lbl.pack(side=tk.LEFT, padx=5)
        
        self.canvas.bind("<Button-1>", self.toggle)
        self.lbl.bind("<Button-1>", self.toggle)
        self.refresh()
        
    def refresh(self):
        self.canvas.delete("all")
        color = Config.LAYOUT['check_color'] if self.var.get() else Config.COLORS['border_enabled']
        self.canvas.create_rectangle(2, 2, self.sz+1, self.sz+1, outline=color, width=2)
        if self.var.get():
            self.canvas.create_line(self.sz*0.2, self.sz*0.5, self.sz*0.45, self.sz*0.8, fill=color, width=3)
            self.canvas.create_line(self.sz*0.45, self.sz*0.8, self.sz*0.85, self.sz*0.25, fill=color, width=3)
            
    def toggle(self, event=None):
        self.var.set(not self.var.get())
        self.refresh()
        if self.command:
            self.command()


class ModernScale(tk.Frame):
    """
    滑块参数调节器封装。
    采用 ttk.Scale 实现，并在左右两侧添加加减微调按钮，
    且完全接管点击与拖拽事件，实现无偏移的精准绝对定位。
    """
    def __init__(self, parent, label, from_, to, var, resolution=1, command=None, bg=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        
        self.var = var
        self.resolution = resolution
        self.user_command = command
        
        # 头部标签栏容器（左侧为中文参数名，右侧为实时更新的值）
        header = tk.Frame(self, bg=bg_color)
        header.pack(fill=tk.X, pady=(5, 2))
        
        tk.Label(header, text=label, bg=bg_color, font=Config.FONTS['zh_normal']).pack(side=tk.LEFT)
        self.val_lbl = tk.Label(header, text=self._format_value(var.get()), bg=bg_color, fg=Config.COLORS['primary'], font=Config.FONTS['en_main'])
        self.val_lbl.pack(side=tk.RIGHT)
        
        # 水平控制容器，容纳 减号按钮、滑块、加号按钮
        control_frame = tk.Frame(self, bg=bg_color)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 自动配置小按钮样式，确保小巧精致
        style = ttk.Style()
        style.configure('ScaleBtn.TButton', font=('SimSun', 10, 'bold'), padding=(2, 1), width=2)
        
        # 减号按钮
        self.dec_btn = ttk.Button(
            control_frame, 
            text="－", 
            style='ScaleBtn.TButton', 
            command=self._decrement
        )
        self.dec_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 使用 ttk.Scale 以获得更好的滑块样式
        self.scale = ttk.Scale(
            control_frame, 
            from_=from_, 
            to=to, 
            orient=tk.HORIZONTAL, 
            variable=var, 
            command=self._on_scale_move
        )
        self.scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        # 加号按钮
        self.inc_btn = ttk.Button(
            control_frame, 
            text="＋", 
            style='ScaleBtn.TButton', 
            command=self._increment
        )
        self.inc_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 完美接管鼠标点击与拖动，消灭 Tkinter 默认 trough 点击的偏移 bug
        self.scale.bind("<Button-1>", self._on_scale_click)
        self.scale.bind("<B1-Motion>", self._on_scale_drag)

    def _format_value(self, val):
        """ 格式化数值显示 """
        try:
            f_val = float(val)
            if self.resolution >= 1:
                return f"{int(round(f_val))}"
            else:
                return f"{f_val:.1f}"
        except Exception:
            return str(val)

    def _on_scale_move(self, val):
        """ 滑动时更新数值标签与回调 """
        self.val_lbl.config(text=self._format_value(val))
        if self.user_command:
            self.user_command(val)

    def _align_to_resolution(self, val):
        """ 辅助方法：将输入值对齐到 resolution 步长，并限制在 from_ 和 to_ 范围内 """
        try:
            val = float(val)
            from_ = float(self.scale.cget("from"))
            to = float(self.scale.cget("to"))
            min_val = min(from_, to)
            max_val = max(from_, to)
            
            # 对齐步长
            if self.resolution:
                val = round(val / self.resolution) * self.resolution
                
            # 限制范围边界
            val = max(min_val, min(max_val, val))
            
            # 返回整型或高精度浮点
            if self.resolution >= 1:
                return int(round(val))
            else:
                return round(val, 2)
        except Exception:
            return val

    def _update_val_from_x(self, x):
        """ 核心数学逻辑：根据鼠标在滑块中的 X 坐标计算出精确的目标物理值 """
        try:
            width = self.scale.winfo_width()
            if width > 0:
                from_ = float(self.scale.cget("from"))
                to = float(self.scale.cget("to"))
                fraction = max(0.0, min(1.0, float(x) / width))
                val = from_ + fraction * (to - from_)
                val = self._align_to_resolution(val)
                self.var.set(val)
                self._on_scale_move(val)
        except Exception:
            pass

    def _on_scale_click(self, event):
        self._update_val_from_x(event.x)
        return "break"

    def _on_scale_drag(self, event):
        self._update_val_from_x(event.x)
        return "break"

    def _decrement(self):
        """ 微调变小一格 """
        try:
            curr = float(self.var.get())
            step = float(self.resolution)
            from_ = float(self.scale.cget("from"))
            to = float(self.scale.cget("to"))
            
            direction = -1 if from_ < to else 1
            new_val = curr + direction * step
            new_val = self._align_to_resolution(new_val)
            self.var.set(new_val)
            self._on_scale_move(new_val)
        except Exception:
            pass

    def _increment(self):
        """ 微调变大一格 """
        try:
            curr = float(self.var.get())
            step = float(self.resolution)
            from_ = float(self.scale.cget("from"))
            to = float(self.scale.cget("to"))
            
            direction = 1 if from_ < to else -1
            new_val = curr + direction * step
            new_val = self._align_to_resolution(new_val)
            self.var.set(new_val)
            self._on_scale_move(new_val)
        except Exception:
            pass


class ColorSwatchRow(tk.Frame):
    """
    色彩配置行。
    左侧显示名称标签，右侧显示对齐的色彩框，支持拾色交互与透明联动。
    """
    def __init__(self, parent, text, attr, initial_color, on_click_callback, on_transparent_toggle=None, allow_transparent=False, bg=None, bold_var=None, on_bold_toggle=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        
        self.attr = attr
        self.on_click_callback = on_click_callback
        self.on_transparent_toggle = on_transparent_toggle
        self.allow_transparent = allow_transparent
        self.last_solid_color = initial_color if initial_color not in ("transparent", "none") else "#ffffff"
        
        # 左侧优雅标签
        self.lbl = tk.Label(self, text=text, bg=bg_color, font=Config.FONTS['zh_normal'])
        self.lbl.pack(side=tk.LEFT, anchor=tk.W)
        
        # 右侧色彩块，其高度与宽度从配置文件中读取
        # 具有微内凹立体边缘
        self.canvas = tk.Canvas(
            self, 
            width=Config.LAYOUT['color_swatch_w'], 
            height=Config.LAYOUT['color_swatch_h'], 
            bg="#ffffff" if initial_color in ("transparent", "none") else initial_color, 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['border_enabled'],
            relief=tk.SUNKEN, 
            bd=1,
            cursor="" if initial_color in ("transparent", "none") else "hand2"
        )
        self.canvas.pack(side=tk.RIGHT, anchor=tk.E)
        
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        
        # 如果支持透明，在色彩块左侧加透明复选框
        if self.allow_transparent:
            self.is_transparent_var = tk.BooleanVar(value=(initial_color in ("transparent", "none")))
            # 使用现代的原生 ttk.Checkbutton 以优化系统勾选视觉体验
            self.trans_check = ttk.Checkbutton(
                self, 
                text="透明", 
                variable=self.is_transparent_var, 
                command=self._on_trans_toggle
            )
            self.trans_check.pack(side=tk.RIGHT, padx=(0, 10), anchor=tk.E)
            
            # 若初始化时就是透明，绘制棋盘格
            if self.is_transparent_var.get():
                self.after(10, self._draw_checkerboard)
                
        # 加粗复选框
        if bold_var:
            bold_command = on_bold_toggle if on_bold_toggle is not None else (lambda: None)
            self.bold_check = ttk.Checkbutton(
                self,
                text="加粗",
                variable=bold_var,
                command=bold_command
            )
            self.bold_check.pack(side=tk.RIGHT, padx=(0, 10), anchor=tk.E)
                
    def _draw_checkerboard(self):
        """ 绘制灰白相间的棋盘格，指示透明 """
        self.canvas.delete("checker")
        w = Config.LAYOUT['color_swatch_w']
        h = Config.LAYOUT['color_swatch_h']
        size = 6  # 棋盘格大小为 6 像素
        for x in range(0, w, size):
            for y in range(0, h, size):
                if ((x // size) + (y // size)) % 2 == 1:
                    self.canvas.create_rectangle(
                        x + 1, y + 1, x + size + 1, y + size + 1,
                        fill="#e2e8f0", outline="", tags="checker"
                    )

    def _on_trans_toggle(self):
        """ 用户勾选或取消勾选透明复选框时的动作 """
        is_trans = self.is_transparent_var.get()
        if is_trans:
            self.canvas.config(cursor="")
            self._draw_checkerboard()
            if self.on_transparent_toggle:
                self.on_transparent_toggle(self.attr, True)
        else:
            self.canvas.config(cursor="hand2")
            self.canvas.delete("checker")
            self.canvas.config(bg=self.last_solid_color)
            if self.on_transparent_toggle:
                self.on_transparent_toggle(self.attr, False, self.last_solid_color)

    def _on_enter(self, event):
        """ 鼠标悬停时高亮色彩槽边框 """
        if self.canvas.cget("cursor") == "hand2":
            self.canvas.config(highlightbackground=Config.COLORS['primary'])
            
    def _on_leave(self, event):
        """ 鼠标离开时恢复标准边框色 """
        if self.canvas.cget("cursor") == "hand2":
            self.canvas.config(highlightbackground=Config.COLORS['border_enabled'])
        
    def _on_click(self, event):
        if self.canvas.cget("cursor") == "hand2":
            self.on_click_callback(self.attr)
            
    def update_color(self, color):
        """ 刷新色彩块的背景颜色 """
        if color in ("transparent", "none"):
            if self.allow_transparent:
                self.is_transparent_var.set(True)
            self.canvas.config(cursor="", bg="#ffffff")
            self._draw_checkerboard()
        else:
            if self.allow_transparent:
                self.is_transparent_var.set(False)
            self.last_solid_color = color
            self.canvas.config(cursor="hand2")
            self.canvas.delete("checker")
            self.canvas.config(bg=color)
        
    def set_state(self, enabled):
        """ 设置该配置项的启用/禁用置灰状态 """
        if enabled:
            if not (self.allow_transparent and self.is_transparent_var.get()):
                self.canvas.config(cursor="hand2", highlightbackground=Config.COLORS['border_enabled'])
            self.lbl.config(fg=Config.COLORS['fg_enabled'])
            if self.allow_transparent:
                self.trans_check.config(state=tk.NORMAL)
        else:
            self.canvas.config(cursor="", highlightbackground=Config.COLORS['border_disabled'])
            self.lbl.config(fg=Config.COLORS['fg_disabled'])
            if self.allow_transparent:
                self.trans_check.config(state=tk.DISABLED)

class LabeledGroup(ttk.LabelFrame):
    """
    带有原生标签外框及统一定制内边距的分组容器。
    """
    def __init__(self, parent, title, bg=None, inner_padx=12, inner_pady=10):
        super().__init__(parent, text=title)
        bg_color = bg if bg else Config.COLORS.get('main_bg', '#ffffff')
        self.inner = tk.Frame(self, bg=bg_color, padx=inner_padx, pady=inner_pady)
        self.inner.pack(fill=tk.BOTH, expand=True)

class LabeledCombobox(tk.Frame):
    """
    带独立标签说明的组合下拉框，内置标签与下拉框的禁用样式联动控制。
    """
    def __init__(self, parent, label_text, var, values, bg=None):
        bg_color = bg if bg else Config.COLORS.get('main_bg', '#ffffff')
        super().__init__(parent, bg=bg_color)
        
        self.label_widget = tk.Label(
            self, 
            text=label_text, 
            bg=bg_color,
            font=Config.FONTS['zh_normal']
        )
        self.label_widget.pack(anchor=tk.W, pady=(2, 2))
        
        self.combo = ttk.Combobox(self, textvariable=var, values=values, state="readonly")
        self.combo.pack(fill=tk.X, expand=True)

    def set_state(self, state):
        """ 同步设置下拉框状态和对应标签的启用/禁用文字颜色。 """
        self.combo.config(state=state)
        fg = Config.COLORS['text_muted'] if state == tk.DISABLED else Config.COLORS['fg_enabled']
        self.label_widget.config(fg=fg)

class ReadOnlyPathEntry(tk.Frame):
    """
    精美的路径显示面板，支持自定义模式下的可编辑状态及禁用时的发灰反馈，
    并始终支持文本拖选复制，不挤占布局。
    """
    def __init__(self, parent, textvariable):
        super().__init__(
            parent,
            bg="#f8fafc",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            padx=10,
            pady=8
        )
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            font=Config.FONTS['zh_normal'],
            bg="#f8fafc",
            fg="#475569",
            bd=0,
            highlightthickness=0,
            state="readonly",
            readonlybackground="#f8fafc",
            selectbackground="#cbd5e1"
        )
        self.entry.pack(fill=tk.X, expand=True)
        
    def set_mode(self, is_custom):
        """ 切换显示模式：是否为自定义编辑模式 """
        if not is_custom:
            self.config(bg="#f1f5f9", highlightbackground="#e2e8f0")
            self.entry.config(
                state="disabled",
                disabledbackground="#f1f5f9",
                disabledforeground="#94a3b8"
            )
        else:
            self.config(bg="#ffffff", highlightbackground="#cbd5e1")
            self.entry.config(
                state="normal",
                background="#ffffff",
                foreground="#1e293b",
                selectbackground="#cbd5e1"
            )

    def set_state(self, state, is_custom):
        """ 配合整体界面启用/禁用状态刷新控件表现 """
        if state == tk.DISABLED:
            self.entry.config(state="disabled")
        else:
            self.entry.config(state="normal" if is_custom else "disabled")
