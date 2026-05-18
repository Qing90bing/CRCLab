import tkinter as tk
from config.constants import Config

class ModernCheckbutton(tk.Frame):
    """
    现代化高品质大尺寸自定义复选框。
    利用 Canvas 精密重绘外边框与勾选对齐线，100% 杜绝原生平台样式差异。
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
    现代化滑块参数调节器封装。
    包含统一的说明标签与参数刻度样式控制。
    """
    def __init__(self, parent, label, from_, to, var, resolution=1, command=None, bg=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        
        tk.Label(self, text=label, bg=bg_color, font=Config.FONTS['zh_normal']).pack(anchor=tk.W, pady=(5, 0))
        
        self.scale = tk.Scale(
            self, 
            from_=from_, 
            to=to, 
            resolution=resolution, 
            orient=tk.HORIZONTAL, 
            variable=var, 
            sliderlength=Config.LAYOUT['slider_len'], 
            width=Config.LAYOUT['slider_thick'],
            font=("Times New Roman", 10), 
            bg=bg_color, 
            highlightthickness=0, 
            command=command
        )
        self.scale.pack(fill=tk.X, pady=(0, 10))


class ColorSwatchRow(tk.Frame):
    """
    现代化高品质色彩配置行。
    左侧显示名称标签，右侧显示精美物理色彩框，支持高保真点击交互与启用/置灰联动控制。
    """
    def __init__(self, parent, text, attr, initial_color, on_click_callback, bg=None):
        bg_color = bg if bg else Config.COLORS['sidebar_bg']
        super().__init__(parent, bg=bg_color)
        
        self.attr = attr
        self.on_click_callback = on_click_callback
        
        self.lbl = tk.Label(self, text=text, bg=bg_color, font=Config.FONTS['zh_normal'])
        self.lbl.pack(side=tk.LEFT)
        
        self.sz = Config.LAYOUT['check_size']
        self.canvas = tk.Canvas(
            self, 
            width=self.sz * 2.5, 
            height=self.sz, 
            bg=initial_color, 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['border_enabled'],
            cursor="hand2"
        )
        self.canvas.pack(side=tk.RIGHT)
        
        self.canvas.bind("<Button-1>", self._on_click)
        
    def _on_click(self, event):
        if self.canvas.cget("cursor") == "hand2":
            self.on_click_callback(self.attr)
            
    def update_color(self, color):
        """ 刷新色彩块的物理背景颜色 """
        self.canvas.config(bg=color)
        
    def set_state(self, enabled):
        """ 设置该配置项的启用/禁用置灰状态 """
        if enabled:
            self.canvas.config(cursor="hand2", highlightbackground=Config.COLORS['border_enabled'])
            self.lbl.config(fg=Config.COLORS['fg_enabled'])
        else:
            self.canvas.config(cursor="", highlightbackground=Config.COLORS['border_disabled'])
            self.lbl.config(fg=Config.COLORS['fg_disabled'])
