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
        bg_color = parent.cget("bg")
        super().__init__(parent, bg=bg_color)
        self.app = app
        self.preview_photo = None

        preview_group = ttk.LabelFrame(self, text=Config.UI_TEXT["export_preview"])
        preview_group.pack(fill=tk.BOTH, expand=True)

        preview_inner = tk.Frame(preview_group, bg=bg_color, padx=12, pady=10)
        preview_inner.pack(fill=tk.BOTH, expand=True)

        # 核心预览 Canvas，配置浅色内嵌边框
        self.preview_canvas = tk.Canvas(
            preview_inner,
            bg=Config.COLORS["preview_canvas_bg"],
            highlightthickness=1,
            highlightbackground=Config.COLORS["preview_canvas_border"],
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

        self.preview_canvas.delete("canvas_bg")
        self.preview_canvas.delete("formula")

        # 将预览放置在画布的绝对物理中心
        cx, cy = cw / 2, ch / 2

        # 1. 优先在最底层铺设大背景棋盘格图（与主画布一致：精确居中，不做网格对齐）
        self.preview_canvas.create_image(cx, cy, image=self.app.canvas_bg_image, anchor="center", tags="canvas_bg")

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

        # 背景与公式均精确锚定画布中心（静态底纹，不做网格对齐）
        self.preview_canvas.coords("canvas_bg", cx, cy)

        # 快速平移前景公式图像
        self.preview_canvas.coords("formula", cx, cy)

    def clear(self):
        """清空画布内所有绘制图元"""
        self.preview_canvas.delete("canvas_bg")
        self.preview_canvas.delete("formula")

    def start_loading(self):
        """开始在右上角显示顺时针旋转的加载动画"""
        if hasattr(self, "_loading_timer") and self._loading_timer:
            return
        self._loading_angle = 0
        self._animate_loading()

    def stop_loading(self):
        """停止加载动画"""
        if hasattr(self, "_loading_timer") and self._loading_timer:
            self.after_cancel(self._loading_timer)
            self._loading_timer = None
        self.preview_canvas.delete("loading_anim")
        self.preview_canvas.delete("loading_track")

    def _animate_loading(self):
        """加载动画帧循环"""
        self.preview_canvas.delete("loading_anim")
        self.preview_canvas.delete("loading_track")

        cw = self.preview_canvas.winfo_width()

        # 如果画布太小还没完全初始化，稍后再试
        if cw > 40:
            # 扩大尺寸到 36x36
            size = 36
            # 绘制在右上角，留出一定边距
            px, py = cw - size - 16, 16
            bbox = (px, py, px + size, py + size)

            # 底部的圆形管道轨道 (使用比较浅的颜色)
            self.preview_canvas.create_oval(*bbox, outline=Config.COLORS.get("divider", "#e5e7eb"), width=4, tags="loading_track")

            # 顺时针旋转，需要减少 angle
            self.preview_canvas.create_arc(
                *bbox,
                start=self._loading_angle,
                extent=100,  # 让旋转部分缩短，像在管道里跑
                style=tk.ARC,
                outline=Config.COLORS["primary"],
                width=4,
                tags="loading_anim",
            )

            self._loading_angle = (self._loading_angle - 15) % 360

        self._loading_timer = self.after(30, self._animate_loading)
