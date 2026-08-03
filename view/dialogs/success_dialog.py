import os
import tkinter as tk
from contextlib import suppress
from tkinter import ttk

from config.constants import Config


class SuccessDialog:
    """
    导出成功提示框。

    封装导出成功后的视觉反馈界面，以精美的竖版卡片及斑马纹明细表展示导出信息。
    """

    def __init__(self, parent, out_path, export_dir, details):
        """
        初始化对话框并配置模态交互。
        """
        self.dlg = tk.Toplevel(parent)
        self.dlg.withdraw()
        self.dlg.title("导出成功")
        self.dlg.transient(parent)

        # 禁用父窗口以实现模态，并避免 grab_set() 导致任务栏最小化失效问题
        with suppress(Exception):
            parent.attributes("-disabled", True)

        def restore_parent(event):
            if event.widget == self.dlg:
                with suppress(Exception):
                    parent.attributes("-disabled", False)

        self.dlg.bind("<Destroy>", restore_parent)

        self.dlg.configure(bg="#ffffff")
        self.out_path = out_path
        self.export_dir = export_dir
        self.details = details

        # 1. 界面主体与内容渲染
        self._build_layout()

        # 2. 窗口几何位置初始化（自适应组件尺寸与屏幕缩放）
        self._setup_geometry(parent)

    def _setup_geometry(self, parent):
        """配置窗口自适应居中与大小"""
        self.dlg.update_idletasks()

        # 自动获取当前所有组件完全展开所需的宽高
        w = self.dlg.winfo_reqwidth()
        h = self.dlg.winfo_reqheight()

        # 设置更舒展的宽度最小值，并为高度提供舒适的下边界留白
        w = max(Config.LAYOUT["success_dialog_min_w"], w)
        h = h + Config.LAYOUT["success_dialog_h_offset"]

        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()

        self.dlg.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.dlg.resizable(False, False)
        self.dlg.deiconify()

    def _build_layout(self):
        """构建各区域容器与小部件"""
        pad = Config.LAYOUT["success_dialog_pad"]
        main_frame = tk.Frame(self.dlg, bg="#ffffff", padx=pad, pady=pad)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 顶部 Header
        self._draw_header(main_frame)

        # 2. 保存路径面板
        self._draw_path_field(main_frame)

        # 3. 导出明细表格
        self._draw_details_table(main_frame)

        # 4. 底部按钮
        btn_frame = tk.Frame(main_frame, bg="#ffffff")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        self._setup_buttons(btn_frame)

    def _draw_header(self, parent):
        """绘制顶部大徽章和右侧标题与描述"""
        header_frame = tk.Frame(parent, bg="#ffffff")
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # 1. 左侧 Canvas 绘制 64x64 的打勾圆形徽章
        size = Config.LAYOUT["success_icon_size"]
        icon_cv = tk.Canvas(header_frame, width=size, height=size, bg="#ffffff", highlightthickness=0)
        icon_cv.pack(side=tk.LEFT, anchor="center", padx=(0, 16))

        # 绘制绿底
        padding = 4
        icon_cv.create_oval(padding, padding, size - padding, size - padding, fill="#10b981", outline="")

        # 绘制白色打勾
        w_line = max(2, int(size * 3 / 64))
        icon_cv.create_line(
            int(size * 20 / 64),
            int(size * 32 / 64),
            int(size * 29 / 64),
            int(size * 41 / 64),
            fill="white",
            width=w_line,
            capstyle=tk.ROUND,
        )
        icon_cv.create_line(
            int(size * 29 / 64),
            int(size * 41 / 64),
            int(size * 45 / 64),
            int(size * 25 / 64),
            fill="white",
            width=w_line,
            capstyle=tk.ROUND,
        )

        # 2. 右侧容器 Frame
        txt_frame = tk.Frame(header_frame, bg="#ffffff")
        txt_frame.pack(side=tk.LEFT, anchor="center", fill=tk.X, expand=True)

        # 标题 Label
        title_lbl = tk.Label(txt_frame, text="导出成功", font=("SimSun", 16, "bold"), bg="#ffffff", fg="#1e293b", anchor="w")
        title_lbl.pack(fill=tk.X, anchor="w", pady=(0, 3))

        # 说明文字 Label
        desc_lbl = tk.Label(
            txt_frame,
            text="图表已成功导出，文件已保存到下方路径。",
            font=("SimSun", 10),
            bg="#ffffff",
            fg="#64748b",
            anchor="w",
            justify="left",
        )
        desc_lbl.pack(fill=tk.X, anchor="w")

    def _draw_path_field(self, parent):
        """绘制保存路径区域"""
        # 标签
        lbl = tk.Label(parent, text="保存路径", font=("SimSun", 10, "bold"), bg="#ffffff", fg="#1e293b", anchor="w")
        lbl.pack(fill=tk.X, pady=(0, 6))

        # 带边框和背景的只读容器
        path_block = tk.Frame(parent, bg="#f8fafc", highlightthickness=1, highlightbackground="#e2e8f0", padx=10, pady=8)
        path_block.pack(fill=tk.X, pady=(0, 18))

        # 只读的 Entry
        path_entry = tk.Entry(
            path_block,
            font=("SimSun", 10),
            bg="#f8fafc",
            fg="#475569",
            bd=0,
            highlightthickness=0,
            readonlybackground="#f8fafc",
            selectbackground="#cbd5e1",
        )
        path_entry.pack(fill=tk.X, expand=True)
        path_entry.insert(0, self.out_path)
        path_entry.config(state="readonly")

    def _draw_details_table(self, parent):
        """绘制导出明细表格"""
        # 标签
        lbl = tk.Label(parent, text="导出明细", font=("SimSun", 10, "bold"), bg="#ffffff", fg="#1e293b", anchor="w")
        lbl.pack(fill=tk.X, pady=(0, 6))

        # 表格外部框容器（形成 1 像素灰色边框）
        table_border = tk.Frame(parent, bg="#cbd5e1", padx=1, pady=1)
        table_border.pack(fill=tk.X, pady=(0, 18))

        # 内层填充容器
        table_inner = tk.Frame(table_border, bg="#cbd5e1")
        table_inner.pack(fill=tk.X)

        # 循环绘制每一行
        # 每一行的 Frame 底部带 1 像素间距，背景使用斑马纹交替，最后一行不加底部间距
        keys = list(self.details.keys())
        total_keys = len(keys)
        for idx, key in enumerate(keys):
            bg_row = "#f8fafc" if idx % 2 == 1 else "#ffffff"
            val = self.details[key]

            row_frame = tk.Frame(table_inner, bg=bg_row, pady=4)

            # 最后一行不加底部外边距，消除表格底部边线变粗的视觉缺陷
            is_last = idx == total_keys - 1
            row_frame.pack(fill=tk.X, pady=(0, 0 if is_last else 1))

            # 左侧参数名 Label
            lbl_key = tk.Label(row_frame, text=key, font=("SimSun", 10), bg=bg_row, fg="#64748b", width=10, anchor="w")
            lbl_key.pack(side=tk.LEFT, padx=(12, 0))

            # 右侧参数值 Label
            lbl_val = tk.Label(row_frame, text=val, font=("SimSun", 10), bg=bg_row, fg="#1e293b", anchor="w")
            lbl_val.pack(side=tk.LEFT, padx=(12, 12))

    def _setup_buttons(self, parent):
        """配置确认与打开目录按钮"""
        # 使用 Grid 布局，使两个按钮平分宽度
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # 打开目录按钮
        def open_dir():
            self.dlg.destroy()
            with suppress(Exception):
                os.startfile(self.export_dir)

        btn_open = ttk.Button(parent, text="打开导出目录", command=open_dir)
        btn_open.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # 好的按钮
        btn_ok = ttk.Button(parent, text="好的", command=self.dlg.destroy)
        btn_ok.grid(row=0, column=1, sticky="ew", padx=(6, 0))
