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
        
        # 1. 优先在最底层铺设大背景棋盘格图，指示背景透明部分，保持全系统底图格子大小对齐
        self.preview_canvas.create_image(0, 0, image=self.app.canvas_bg_image, anchor="center", tags="canvas_bg")
        
        # 2. 贴上缩放完成后的公式算式图
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor="center")
        
        # 3. 动态配置滚动范围上限以满足坐标平移
        self.preview_canvas.config(scrollregion=(-3000, -3000, 3000, 3000))
        self.recenter_canvas()

    def recenter_canvas(self):
        """
        物理平移视口原点，使公式图像完美地水平和垂直居中对齐在 Canvas 展示区中。
        """
        self.preview_canvas.update_idletasks()
        cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        bbox = self.preview_canvas.bbox("all")
        if bbox:
            self.preview_canvas.xview_moveto(((bbox[0] + bbox[2]) / 2 - cw / 2 + 3000) / 6000)
            self.preview_canvas.yview_moveto(((bbox[1] + bbox[3]) / 2 - ch / 2 + 3000) / 6000)

    def clear(self):
        """ 清空画布内所有绘制图元 """
        self.preview_canvas.delete("all")
