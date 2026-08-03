import os
import tkinter as tk
from contextlib import suppress
from tkinter import ttk

from PIL import Image, ImageTk

from config.constants import Config


class AboutDialog:
    """
    弹出优雅的自定义关于本软件对话框，保证字体完全受控统一，并增加视觉美化设计
    """

    def __init__(self, app):
        self.app = app
        dlg = tk.Toplevel(self.app.root)
        dlg.title(Config.UI_TEXT["about_title"])
        dlg.transient(self.app.root)

        with suppress(Exception):
            self.app.root.attributes("-disabled", True)

        def restore_parent(event):
            if event.widget == dlg:
                with suppress(Exception):
                    self.app.root.attributes("-disabled", False)

        dlg.bind("<Destroy>", restore_parent)

        dlg.configure(bg=Config.COLORS["main_bg"])
        sw, sh = self.app.root.winfo_screenwidth(), self.app.root.winfo_screenheight()

        content = tk.Frame(dlg, bg=Config.COLORS["main_bg"], padx=30, pady=25)
        content.pack(fill=tk.BOTH, expand=True)

        self._create_about_header(content)
        tk.Frame(content, height=1, bg=Config.COLORS["divider"]).pack(fill=tk.X, pady=(0, 15))
        self._create_about_tech_info(content)
        tk.Frame(content, height=1, bg=Config.COLORS["divider"]).pack(fill=tk.X, pady=10)
        self._create_about_libs(content)
        self._create_about_footer(content, dlg)

        dlg.update_idletasks()
        rw = max(Config.LAYOUT["about_dialog_w"], dlg.winfo_reqwidth())
        rh = max(Config.LAYOUT["about_dialog_h"], dlg.winfo_reqheight())
        dlg.geometry(f"{rw}x{rh}+{(sw - rw) // 2}+{(sh - rh) // 2}")
        dlg.resizable(False, False)

    def _create_about_header(self, parent):
        """创建关于对话框的头部区域"""
        header_frame = tk.Frame(parent, bg=Config.COLORS["main_bg"])
        header_frame.pack(fill=tk.X, pady=(0, 20))

        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "app_icon2.png")
        try:
            img = Image.open(logo_path)
            resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else getattr(Image, "ANTIALIAS", 1)
            img.thumbnail((Config.LAYOUT["about_logo_w"], Config.LAYOUT["about_logo_h"]), resample_filter)  # type: ignore
            photo = ImageTk.PhotoImage(img)
            logo_lbl = tk.Label(header_frame, image=photo, bg=Config.COLORS["main_bg"])
            logo_lbl.image = photo
            logo_lbl.pack(side=tk.LEFT, padx=(0, 20))
        except Exception:
            tk.Label(
                header_frame, text="CRCLab", font=("Times New Roman", 24, "bold"), bg=Config.COLORS["main_bg"], fg=Config.COLORS["primary"]
            ).pack(side=tk.LEFT, padx=(0, 20))

        title_frame = tk.Frame(header_frame, bg=Config.COLORS["main_bg"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        tk.Label(
            title_frame, text="CRCLab", font=("Times New Roman", 22, "bold"), bg=Config.COLORS["main_bg"], fg=Config.COLORS["primary"]
        ).pack(anchor="w", pady=(8, 0))
        tk.Label(
            title_frame,
            text="循环冗余校验解析与验证工具",
            font=Config.FONTS["zh_bold"],
            bg=Config.COLORS["main_bg"],
            fg=Config.COLORS["text_dark"],
        ).pack(anchor="w", pady=(4, 0))
        tk.Label(
            title_frame,
            text=f"版本: {Config.VERSION}",
            font=Config.FONTS["en_main"],
            bg=Config.COLORS["main_bg"],
            fg=Config.COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

    def _create_about_tech_info(self, parent):
        """创建关于对话框的技术信息与链接区域"""
        info_frame = tk.Frame(parent, bg=Config.COLORS["main_bg"])
        info_frame.pack(fill=tk.BOTH, expand=True)

        import tkinter.font as tkfont
        import webbrowser

        zh_normal_font = Config.FONTS["zh_normal"]
        link_font = tkfont.Font(family=zh_normal_font[0], size=zh_normal_font[1], underline=True)

        meta_frame = tk.Frame(info_frame, bg=Config.COLORS["main_bg"])
        meta_frame.pack(fill=tk.X, pady=(0, 10))

        author_row = tk.Frame(meta_frame, bg=Config.COLORS["main_bg"])
        author_row.pack(fill=tk.X, pady=2)
        tk.Label(
            author_row, text="开发作者: ", font=Config.FONTS["zh_normal"], bg=Config.COLORS["main_bg"], fg=Config.COLORS["text_dark"]
        ).pack(side=tk.LEFT)
        tk.Label(
            author_row, text=Config.AUTHOR, font=Config.FONTS["zh_normal"], bg=Config.COLORS["main_bg"], fg=Config.COLORS["text_dark"]
        ).pack(side=tk.LEFT)

        repo_row = tk.Frame(meta_frame, bg=Config.COLORS["main_bg"])
        repo_row.pack(fill=tk.X, pady=2)
        tk.Label(
            repo_row, text="开源仓库: ", font=Config.FONTS["zh_normal"], bg=Config.COLORS["main_bg"], fg=Config.COLORS["text_dark"]
        ).pack(side=tk.LEFT)

        repo_lbl = tk.Label(
            repo_row, text=Config.REPOSITORY, font=link_font, fg=Config.COLORS["primary"], bg=Config.COLORS["main_bg"], cursor="hand2"
        )
        repo_lbl.pack(side=tk.LEFT)
        repo_lbl.bind("<Button-1>", lambda e: webbrowser.open_new(Config.REPOSITORY))

        feedback_row = tk.Frame(meta_frame, bg=Config.COLORS["main_bg"])
        feedback_row.pack(fill=tk.X, pady=2)
        tk.Label(
            feedback_row, text="问题反馈: ", font=Config.FONTS["zh_normal"], bg=Config.COLORS["main_bg"], fg=Config.COLORS["text_dark"]
        ).pack(side=tk.LEFT)

        feedback_url = f"{Config.REPOSITORY}/issues"
        feedback_lbl = tk.Label(
            feedback_row, text=feedback_url, font=link_font, fg=Config.COLORS["primary"], bg=Config.COLORS["main_bg"], cursor="hand2"
        )
        feedback_lbl.pack(side=tk.LEFT)
        feedback_lbl.bind("<Button-1>", lambda e: webbrowser.open_new(feedback_url))

        tech_text = (
            "核心技术特性:\n"
            "• 支持无损矢量 EMF / SVG 导出，拒绝缩放模糊\n"
            "• 搭载 GDI 高清渲染核心，实现 Office 排版像素级兼容\n"
            "• 实时二进制长除运算结果看板与过程特征自动解析"
        )
        tk.Label(
            info_frame,
            text=tech_text,
            font=Config.FONTS["zh_normal"],
            bg=Config.COLORS["main_bg"],
            fg=Config.COLORS["text_dark"],
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X, expand=True, pady=(5, 0))

    def _create_about_libs(self, parent):
        """创建关于对话框的第三方库展示区域"""
        import tkinter.font as tkfont
        import webbrowser

        zh_normal_font = Config.FONTS["zh_normal"]
        link_font = tkfont.Font(family=zh_normal_font[0], size=zh_normal_font[1], underline=True)

        libs_section = tk.Frame(parent, bg=Config.COLORS["main_bg"])
        libs_section.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            libs_section,
            text="使用的第三方库:",
            font=Config.FONTS["zh_bold"],
            bg=Config.COLORS["main_bg"],
            fg=Config.COLORS["text_dark"],
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 5))

        libs_row = tk.Frame(libs_section, bg=Config.COLORS["main_bg"])
        libs_row.pack(fill=tk.X, pady=2)

        libs_row.grid_columnconfigure(0, weight=1)
        libs_row.grid_columnconfigure(1, weight=1)
        libs_row.grid_columnconfigure(2, weight=1)

        libs = [
            ("Pillow", "https://github.com/python-pillow/Pillow", 0, 0, tk.W),
            ("svglib", "https://github.com/deeplook/svglib", 0, 1, None),
            ("reportlab", "https://pypi.org/project/reportlab/", 0, 2, tk.E),
            ("Nuitka", "https://nuitka.net/", 1, 0, tk.W),
            ("zstandard", "https://github.com/indygreg/python-zstandard", 1, 1, None),
        ]

        for name, url, row, col, sticky in libs:
            lbl = tk.Label(libs_row, text=name, font=link_font, fg=Config.COLORS["primary"], bg=Config.COLORS["main_bg"], cursor="hand2")
            if sticky:
                lbl.grid(row=row, column=col, sticky=sticky, pady=(0, 5) if row == 0 else 0)
            else:
                lbl.grid(row=row, column=col, pady=(0, 5) if row == 0 else 0)
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open_new(u))

    def _create_about_footer(self, parent, dlg):
        """创建关于对话框的底部版权与确定按钮区域"""
        bottom_frame = tk.Frame(parent, bg=Config.COLORS["main_bg"])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            bottom_frame, text=Config.COPYRIGHT, font=Config.FONTS["en_main"], bg=Config.COLORS["main_bg"], fg=Config.COLORS["text_muted"]
        ).pack(side=tk.LEFT, pady=(15, 0))

        btn = ttk.Button(bottom_frame, text="确定", width=8, command=dlg.destroy, style="Action.TButton")
        try:
            btn.pack(side=tk.RIGHT, pady=(15, 0))
        except Exception:
            ttk.Button(bottom_frame, text="确定", width=8, command=dlg.destroy).pack(side=tk.RIGHT, pady=(15, 0))
