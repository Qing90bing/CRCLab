import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from config.constants import Config

class ExportPreview(tk.Frame):
    """
    导出图表配置中的左侧实时预览画布面板。
    
    采用高内聚封装，包含背景灰白棋盘格绘制与渲染公式图片
    """
    def __init__(self, parent, app):
        """
        初始化预览面板。
        :param parent: 父级容器。
        :param app: 主应用程序 CRCLabApp 实例。
        """
        bg_color = parent.cget('bg')
        super().__init__(parent, bg=bg_color)
        self.app = app
        self.preview_photo = None
        
        preview_group = ttk.LabelFrame(self, text=Config.UI_TEXT['export_preview'])
        preview_group.pack(fill=tk.BOTH, expand=True)

        preview_inner = tk.Frame(preview_group, bg=bg_color, padx=12, pady=10)
        preview_inner.pack(fill=tk.BOTH, expand=True)
        
        # 核心预览 Canvas，配置浅色内嵌边框
        self.preview_canvas = tk.Canvas(
            preview_inner, 
            bg=Config.COLORS['preview_canvas_bg'], 
            highlightthickness=1, 
            highlightbackground=Config.COLORS['preview_canvas_border']
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def render_preview(self, img):
        """
        根据当前预览画布物理尺寸，将 Pillow 的 RGBA 图解等比高清晰缩放并渲染贴图。
        
        :param img: Pillow Image 实例。
        """
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if cw > 10 and ch > 10:
            fit_scale = min((cw - 40) / img.width, (ch - 40) / img.height)
            fit_scale = min(1.0, fit_scale)
            if fit_scale < 0.99:
                tw = max(1, int(img.width * fit_scale))
                th = max(1, int(img.height * fit_scale))
                img = img.resize((tw, th), Image.Resampling.LANCZOS)
        
        self.preview_canvas.delete("all")
        
        # 将预览放置在画布的绝对物理中心
        cx, cy = cw / 2, ch / 2
        
        # 1. 优先在最底层铺设大背景棋盘格图，对齐 15 像素网格，避免网格闪烁
        size = 15
        cx_aligned = int((cx // size) * size)
        cy_aligned = int((cy // size) * size)
        
        self.preview_canvas.create_image(cx_aligned, cy_aligned, image=self.app.canvas_bg_image, anchor="center", tags="canvas_bg")
        
        # 2. 贴上缩放完成后的公式算式图
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(cx, cy, image=self.preview_photo, anchor="center", tags="formula")
        
        # 无需配置 scrollregion，因为该预览画布不支持拖拽平移，内容始终物理居中

    def recenter_canvas(self):
        """
        在画布大小被调整（或调整中）时，快速将现有的视觉元素物理平移到新中心。
        无需重绘即可保持视觉完美的居中体验。
        """
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if cw <= 10 or ch <= 10:
            return
            
        cx, cy = cw / 2, ch / 2
        
        # 快速平移背景网格（保持科技感像素对齐）
        size = 15
        cx_aligned = int((cx // size) * size)
        cy_aligned = int((cy // size) * size)
        self.preview_canvas.coords("canvas_bg", cx_aligned, cy_aligned)
        
        # 快速平移前景公式图像
        self.preview_canvas.coords("formula", cx, cy)

    def clear(self):
        """ 清空画布内所有绘制图元 """
        self.preview_canvas.delete("all")
