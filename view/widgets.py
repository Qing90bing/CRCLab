import tkinter as tk
from tkinter import ttk
from config.constants import Config

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
    采用 ttk.Scale 实现，并在右侧实时显示当前数值。
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
        
        # 使用 ttk.Scale 以获得更好的滑块样式
        self.scale = ttk.Scale(
            self, 
            from_=from_, 
            to=to, 
            orient=tk.HORIZONTAL, 
            variable=var, 
            command=self._on_scale_move
        )
        self.scale.pack(fill=tk.X, pady=(0, 10))

    def _format_value(self, val):
        """ 格式化数值显示 """
        try:
            f_val = float(val)
            if self.resolution >= 1:
                return f"{int(round(f_val))}"
            else:
                # 针对 0.1 步长的小数保留 1 位小数
                return f"{f_val:.1f}"
        except Exception:
            return str(val)

    def _on_scale_move(self, val):
        """ 滑动时更新数值标签与回调 """
        self.val_lbl.config(text=self._format_value(val))
        if self.user_command:
            self.user_command(val)


class ColorSwatchRow(tk.Frame):
    """
    色彩配置行。
    左侧显示名称标签，右侧显示对齐的色彩框，支持拾色交互与联动。
    """
    def __init__(self, parent, text, attr, initial_color, on_click_callback, bg=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        
        self.attr = attr
        self.on_click_callback = on_click_callback
        
        # 左侧优雅标签
        self.lbl = tk.Label(self, text=text, bg=bg_color, font=Config.FONTS['zh_normal'])
        self.lbl.pack(side=tk.LEFT, anchor=tk.W)
        
        # 右侧色彩块，其高度与宽度从配置文件中读取
        # 具有微内凹立体边缘
        self.canvas = tk.Canvas(
            self, 
            width=Config.LAYOUT['color_swatch_w'], 
            height=Config.LAYOUT['color_swatch_h'], 
            bg=initial_color, 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['border_enabled'],
            relief=tk.SUNKEN, 
            bd=1,
            cursor="hand2"
        )
        self.canvas.pack(side=tk.RIGHT, anchor=tk.E)
        
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        
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
        self.canvas.config(bg=color)
        
    def set_state(self, enabled):
        """ 设置该配置项的启用/禁用置灰状态 """
        if enabled:
            self.canvas.config(cursor="hand2", highlightbackground=Config.COLORS['border_enabled'])
            self.lbl.config(fg=Config.COLORS['fg_enabled'])
        else:
            self.canvas.config(cursor="", highlightbackground=Config.COLORS['border_disabled'])
            self.lbl.config(fg=Config.COLORS['fg_disabled'])
