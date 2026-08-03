import tkinter as tk
from config.constants import Config

class InteractiveCanvas(tk.Canvas):
    """
    智能交互画布。
    封装平移、缩放、双击还原、拖动模式切换及底层背景贴合的所有物理逻辑。
    解耦主窗口代码。
    """
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._drag_mode = True
        self.config(cursor="hand2")
        
        self.bind("<ButtonPress-1>", self.start_pan)
        self.bind("<B1-Motion>", self.do_pan)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind("<Configure>", lambda e: self.update_bg_position())

    def adjust_zoom(self, factor):
        new_scale = self.app.view_scale * factor
        if Config.LAYOUT['zoom_min'] <= new_scale <= Config.LAYOUT['zoom_max']:
            self.app.view_scale = new_scale
            self.update_zoom_display()
            self.app.generate(auto_center=False)

    def on_mousewheel(self, event):
        zoom_factor = Config.LAYOUT['zoom_in_factor'] if event.delta > 0 else Config.LAYOUT['zoom_out_factor']
        self.app.view_scale = max(
            Config.LAYOUT['zoom_min'], 
            min(Config.LAYOUT['zoom_mousewheel_max'], getattr(self.app, 'view_scale', 1.0) * zoom_factor)
        )
        self.update_zoom_display()
        self.app.generate(auto_center=False)

    def update_zoom_display(self):
        if hasattr(self.app, 'toolbar'):
            self.app.toolbar.set_zoom_text(f"{int(self.app.view_scale * 100)}%")

    def center_view(self):
        bbox = self.bbox("formula")
        if not bbox: return
        cw, ch = self.winfo_width(), self.winfo_height()
        scroll_bound = Config.LAYOUT['canvas_scroll_bound']
        self.xview_moveto(((bbox[0]+bbox[2])/2 - cw/2 + scroll_bound) / (scroll_bound * 2))
        self.yview_moveto(((bbox[1]+bbox[3])/2 - ch/2 + scroll_bound) / (scroll_bound * 2))
        self.update_bg_position()

    def fit_view(self):
        if not hasattr(self.app, 'photo_img') or not self.app.photo_img:
            return
            
        cw = self.winfo_width() - 40
        ch = self.winfo_height() - 40
        
        if cw <= 0 or ch <= 0:
            return
            
        orig_w = self.app.photo_img.width() / self.app.view_scale
        orig_h = self.app.photo_img.height() / self.app.view_scale
        
        if orig_w <= 0 or orig_h <= 0:
            return
            
        target_scale = min(cw / orig_w, ch / orig_h)
        target_scale = max(Config.LAYOUT['zoom_min'], min(Config.LAYOUT['zoom_max'], target_scale))
        
        self.app.view_scale = target_scale
        self.update_zoom_display()
        self.app.generate(auto_center=True)

    def reset_view(self):
        self.app.view_scale = 1.0
        self.update_zoom_display()
        self.app.generate(auto_center=True)

    def toggle_drag_mode(self):
        self._drag_mode = not self._drag_mode
        if hasattr(self.app, 'toolbar'):
            self.app.toolbar.set_drag_mode_ui(self._drag_mode)
        if self._drag_mode:
            self.config(cursor="hand2")
        else:
            self.config(cursor="")

    def start_pan(self, event):
        if not self._drag_mode:
            return
        self.scan_mark(event.x, event.y)

    def do_pan(self, event):
        if not self._drag_mode:
            return
        self.scan_dragto(event.x, event.y, gain=1)
        self.update_bg_position()

    def update_bg_position(self):
        # 棋盘格背景是“屏幕静止”贴图：无论内容如何平移/缩放，
        # 它始终锚定在当前视口中心（相对窗口不动），模拟常见绘图软件的固定工作区底纹。
        if self.find_withtag("canvas_bg"):
            w = self.winfo_width()
            h = self.winfo_height()
            if w > 10 and h > 10:
                cx = self.canvasx(w / 2)
                cy = self.canvasy(h / 2)
                self.coords("canvas_bg", cx, cy)
