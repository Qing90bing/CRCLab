import tkinter as tk

from config.constants import Config


class CanvasToolbar:
    """
    画布工具栏组件。
    负责渲染缩放、拖动模式等控制按钮，并将交互事件通知给主窗口。
    """

    def __init__(self, parent, on_zoom_in, on_zoom_out, on_reset_view, on_fit_view, on_toggle_drag_mode):
        self.on_toggle_drag_mode = on_toggle_drag_mode
        self._drag_mode = True

        self.tb = tk.Frame(
            parent,
            bg=Config.COLORS["toolbar_bg"],
            bd=0,
            highlightthickness=1,
            highlightbackground="#000000",
            padx=Config.LAYOUT["toolbar_padding_x"],
            pady=Config.LAYOUT["toolbar_padding_y"],
        )
        self.tb.place(relx=0.5, y=Config.LAYOUT["toolbar_y_offset"], anchor="n")

        btn_cfg = {
            "bg": Config.COLORS["toolbar_bg"],
            "activebackground": "#e2e8f0",
            "bd": 0,
            "relief": tk.FLAT,
            "cursor": "hand2",
            "font": Config.FONTS["zh_normal"],
            "padx": 10,
            "pady": 4,
        }

        tk.Button(self.tb, text=Config.UI_TEXT["btn_zoom_in"], command=on_zoom_in, **btn_cfg).pack(side=tk.LEFT, padx=2)

        self.zoom_lbl = tk.Label(self.tb, text="100%", font=Config.FONTS["zoom_lbl"], bg=Config.COLORS["toolbar_bg"], width=6)
        self.zoom_lbl.pack(side=tk.LEFT, padx=4)

        tk.Button(self.tb, text=Config.UI_TEXT["btn_zoom_out"], command=on_zoom_out, **btn_cfg).pack(side=tk.LEFT, padx=2)

        tk.Frame(self.tb, width=1, bg=Config.COLORS["toolbar_divider"], height=Config.LAYOUT["toolbar_divider_height"]).pack(
            side=tk.LEFT, padx=Config.LAYOUT["toolbar_divider_padx"]
        )

        self.drag_btn = tk.Button(
            self.tb,
            text=Config.UI_TEXT["btn_drag"],
            command=self._handle_toggle_drag,
            **{
                **btn_cfg,
                "relief": tk.SUNKEN,
                "bg": "#0078d4",
                "fg": "#ffffff",
                "activebackground": "#005a9e",
                "activeforeground": "#ffffff",
            },
        )
        self.drag_btn.pack(side=tk.LEFT, padx=2)

        tk.Button(self.tb, text=Config.UI_TEXT["btn_reset_view"], command=on_reset_view, **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(self.tb, text=Config.UI_TEXT["btn_fit"], command=on_fit_view, **btn_cfg).pack(side=tk.LEFT, padx=2)

        def on_enter(e):
            btn = e.widget
            if btn == getattr(self, "drag_btn", None) and getattr(self, "_drag_mode", False):
                return
            btn.config(bg="#e2e8f0")

        def on_leave(e):
            btn = e.widget
            if btn == getattr(self, "drag_btn", None) and getattr(self, "_drag_mode", False):
                return
            btn.config(bg=Config.COLORS["toolbar_bg"])

        for child in self.tb.winfo_children():
            if isinstance(child, tk.Button):
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)

    def _handle_toggle_drag(self):
        self.on_toggle_drag_mode()

    def set_zoom_text(self, text):
        self.zoom_lbl.config(text=text)

    def set_drag_mode_ui(self, is_drag_mode):
        self._drag_mode = is_drag_mode
        if is_drag_mode:
            self.drag_btn.config(relief=tk.SUNKEN, bg="#0078d4", fg="#ffffff")
        else:
            self.drag_btn.config(relief=tk.FLAT, bg=Config.COLORS["toolbar_bg"], fg="black")
