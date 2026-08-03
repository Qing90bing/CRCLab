import tkinter as tk
from tkinter import ttk

from config.constants import Config
from view.components.widgets import Justify, ReadonlyEntry


def to_algebraic(divisor):
    """
    将二进制多项式字符串（如 '1011'）转换为代数多项式格式（如 'X³ + X + 1'）。
    """
    if not divisor:
        return "--"
    n = len(divisor)
    terms = []
    superscripts = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    for idx, bit in enumerate(divisor):
        power = n - 1 - idx
        if bit == "1":
            if power == 0:
                terms.append("1")
            elif power == 1:
                terms.append("X")
            else:
                power_str = "".join(superscripts.get(c, c) for c in str(power))
                terms.append(f"X{power_str}")
    return " + ".join(terms) if terms else "0"


class DashboardPanel(tk.Frame):
    """
    Windows 风格的实时运算结果解析看板。

    采用原生 Windows 风格（ttk.LabelFrame），移除了所有非标准的复制按钮和图标。
    所有指标行均采用统一右对齐（tk.RIGHT），保证极佳的视觉对称性与排版美观度。
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=Config.COLORS["main_bg"], height=Config.LAYOUT["dashboard_height"])
        self.app = app
        self.pack_propagate(False)

        # 1. 网格自适应列分配
        for i in range(4):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(0, weight=1)

        self._init_cards()

    def _init_cards(self):
        """使用 native Windows 风格的 ttk.LabelFrame 构建 4 块缩小标签长度的面板"""
        gap = Config.LAYOUT["card_gap"]

        # 获取 native 主题背景色，确保文字背景与系统主题浑然一体
        try:
            native_bg = self.tk.call("ttk::style", "lookup", "TFrame", "-background")
        except Exception:
            native_bg = "#ffffff"

        # Card 1: 输入特征分析 (全部右对齐)
        self.card1 = ttk.LabelFrame(self, text=Config.UI_TEXT["card_input_title"])
        self.card1.grid(row=0, column=0, sticky="nsew", padx=(0, gap), pady=5)
        self.input_lbl1 = self._add_metric_row(self.card1, "数据长度", "--", "位", native_bg=native_bg, justify="right")
        self.input_lbl2 = self._add_metric_row(self.card1, "多项式", "--", "", native_bg=native_bg, justify="right")
        self.input_lbl3 = self._add_metric_row(self.card1, "除数十六进制", "--", "", native_bg=native_bg, justify="right")

        # Card 2: 运算步骤统计 (全部右对齐)
        self.card2 = ttk.LabelFrame(self, text=Config.UI_TEXT["card_stats_title"])
        self.card2.grid(row=0, column=1, sticky="nsew", padx=gap, pady=5)
        self.stats_lbl1 = self._add_metric_row(self.card2, "二进制商", "--", "", native_bg=native_bg, justify="right")
        self.stats_lbl2 = self._add_metric_row(self.card2, "运算步数", "--", "步", native_bg=native_bg, justify="right")

        # Card 3: 校验输出结果 (全部右对齐)
        self.card3 = ttk.LabelFrame(self, text=Config.UI_TEXT["card_checksum_title"])
        self.card3.grid(row=0, column=2, sticky="nsew", padx=gap, pady=5)
        self.checksum_lbl1 = self._add_metric_row(self.card3, "校验码", "--", "", native_bg=native_bg, is_highlight=True, justify="right")
        self.checksum_lbl2 = self._add_metric_row(self.card3, "十六进制", "--", "", native_bg=native_bg, is_highlight=True, justify="right")

        # Card 4: 发送数据帧
        self.card4 = ttk.LabelFrame(self, text=Config.UI_TEXT["card_frame_title"])
        self.card4.grid(row=0, column=3, sticky="nsew", padx=(gap, 0), pady=5)

        # 居中对齐容器：使用 native ttk.Frame，自动继承 native Windows 窗口背景色，消除色差方块
        self.center_frame = ttk.Frame(self.card4)
        self.center_frame.pack(expand=True, fill=tk.BOTH, padx=12, pady=10)

        # native_bg 已在顶部获取，此处无需重复获取

        # 垂直与水平居中容器
        self.inner_center = ttk.Frame(self.center_frame)
        self.inner_center.pack(expand=True)

        # 提示标签
        self.title_lbl = ttk.Label(self.inner_center, text="拼接发送帧 (可双击选定复制)", font=Config.FONTS["zh_normal"])
        self.title_lbl.pack(anchor=tk.CENTER, pady=(0, 6))

        # 拼接发送帧数据框：完全居中正中央显示，背景与系统主题一致
        self.frame_entry = ReadonlyEntry(
            self.inner_center,
            "--",
            font=("Times New Roman", 13, "bold"),
            fg=Config.COLORS["text_dark"],
            bg=native_bg,
            width=24,
            justify="center",
        )
        self.frame_entry.pack(anchor=tk.CENTER, fill=tk.X)

    def _add_metric_row(
        self, parent_frame, label_text, val_text, unit_text, native_bg="#ffffff", is_highlight=False, justify: Justify = "right"
    ):
        """统一添加支持右对齐对齐的 Windows 属性行"""
        bg_color = native_bg

        row_frame = tk.Frame(parent_frame, bg=bg_color)
        row_frame.pack(fill=tk.X, anchor=tk.W, padx=12, pady=6)

        # 左侧标签
        tk.Label(row_frame, text=label_text, font=Config.FONTS["zh_normal"], bg=bg_color, fg=Config.COLORS["text_muted"]).pack(side=tk.LEFT)

        # 右侧数值与单位对齐容器，使用 pack(fill=tk.X, expand=True) 允许 Entry 最大化伸拉
        val_frame = tk.Frame(row_frame, bg=bg_color)
        val_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # 根据高亮类型选择前景色
        fg_color = Config.COLORS["primary"] if is_highlight else Config.COLORS["text_dark"]
        font_family = "Times New Roman"

        if unit_text:
            # 如果带单位，右侧先 pack 单位
            tk.Label(val_frame, text=f" {unit_text}", font=Config.FONTS["zh_normal"], bg=bg_color, fg=Config.COLORS["text_muted"]).pack(
                side=tk.RIGHT
            )

        # 统一使用右对齐的 ReadonlyEntry，使所有数据行在右侧完美对齐，消除尴尬的左侧大空白
        val_entry = ReadonlyEntry(val_frame, val_text, font=(font_family, 11, "bold"), fg=fg_color, bg=bg_color, width=24, justify=justify)
        val_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        return val_entry

    def update_data(self, data, divisor, q, rows):
        """供渲染管线实时调用的刷新函数"""
        # 从运算步骤中查找余数行类型获取初始余数
        raw_remainder = "--"
        for r in reversed(rows):
            if r["type"] == "remainder":
                raw_remainder = r["val"]
                break

        # 核心数学修复：CRC 校验码长度必须是多项式阶数，即 len(divisor) - 1 位，需用 zfill 补全高位 0！
        if raw_remainder != "--" and len(divisor) > 1:
            n_bits = len(divisor) - 1
            remainder = raw_remainder[-n_bits:].zfill(n_bits)
        else:
            remainder = raw_remainder

        # 计算 XOR 运算步数
        xor_steps = sum(1 for r in rows if r["type"] == "divisor")

        # 1. 刷新卡片 1: 输入分析
        self.input_lbl1.set_value(str(len(data)))
        self.input_lbl2.set_value(to_algebraic(divisor))

        # 转换除数为 Hex 十六进制
        if divisor and all(c in "01" for c in divisor):
            div_hex = f"0x{int(divisor, 2):X}"
            self.input_lbl3.set_value(div_hex)
        else:
            self.input_lbl3.set_value("--")

        # 2. 刷新卡片 2: 运算统计
        self.stats_lbl1.set_value(q if q else "--")
        self.stats_lbl2.set_value(str(xor_steps))

        # 3. 刷新卡片 3: 校验结果 (校验余数)
        is_verify = False
        if hasattr(self.app, "calc_mode_var") and self.app.calc_mode_var.get() == "verify":
            is_verify = True

        if is_verify:
            if remainder != "--" and all(c in "01" for c in remainder):
                if all(c == "0" for c in remainder):
                    self.checksum_lbl1.set_value(f"{remainder} (整除/无错)", fg=Config.COLORS["valid_green"])
                else:
                    self.checksum_lbl1.set_value(f"{remainder} (检测到错误)", fg=Config.COLORS["invalid_red"])
            else:
                self.checksum_lbl1.set_value(remainder, fg=Config.COLORS["primary"])
        else:
            self.checksum_lbl1.set_value(remainder, fg=Config.COLORS["primary"])

        # 转换校验码为 Hex 十六进制
        if remainder != "--" and all(c in "01" for c in remainder):
            hex_str = f"0x{int(remainder, 2):0{max(1, (len(remainder) + 3) // 4)}X}"
            self.checksum_lbl2.set_value(hex_str)
        else:
            self.checksum_lbl2.set_value("--")

        # 4. 刷新卡片 4: 发送数据帧 / 校验数据帧
        if is_verify:
            self.title_lbl.config(text="接收校验数据帧")
            self.frame_entry.set_value(data)
        else:
            self.title_lbl.config(text="拼接发送帧 (可双击选定复制)")
            if remainder != "--":
                self.frame_entry.set_value(data + remainder)
            else:
                self.frame_entry.set_value("--")
